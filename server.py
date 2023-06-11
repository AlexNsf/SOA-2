import logging
import time
from concurrent import futures
from uuid import UUID, uuid4
import grpc

from threading import Lock

from python_proto import server_pb2, server_pb2_grpc, client_pb2, client_pb2_grpc
from enums import RoleEnum, ActionsEnum
from mafia import Game
from settings import settings
import google.protobuf.empty_pb2
import requests


class ClientStub:
    def __init__(self, host: str, port: int, name: str):
        self.stub = client_pb2_grpc.ClientStub(grpc.insecure_channel(f"{host}:{port}"))
        self.name = name
        self.id = uuid4()
        self.game_id: UUID | None = None

        self.logger = logging.getLogger(__name__)

    def notify_join(self, name: str) -> None:
        message = client_pb2.JoinNotification()
        message.player = name
        self.stub.NotifyJoin(message, timeout=1)

    def notify_leave(self, name: str) -> None:
        message = client_pb2.LeaveNotification()
        message.player = name
        self.stub.NotifyLeave(message, timeout=1)

    def notify_action(self, notification: str) -> None:
        message = client_pb2.ActionNotification()
        message.notification = notification
        self.stub.NotifyAction(message, timeout=1)

    def send_role(self, role: RoleEnum) -> None:
        message = client_pb2.Role()
        message.role = role.value
        self.stub.SendRole(message, timeout=1)

    def send_available_actions(self, actions: list[ActionsEnum]):
        message = client_pb2.AvailableActions()
        message.actions.extend([action.value for action in actions])
        self.stub.SendAvailableActions(message, timeout=1)

    def livez(self):
        message = client_pb2.LivezRequest()
        self.stub.Livez(message, timeout=1)


class ServerServicer(server_pb2_grpc.ServerServicer):
    def __init__(self):
        self.id_2_registered_clients: dict[UUID, ClientStub] = {}
        self.name_2_registered_clients: dict[str, ClientStub] = {}
        self.id_2_active_clients: dict[UUID, ClientStub] = {}
        self.name_2_active_client: dict[str, ClientStub] = {}

        self.id_2_game: dict[UUID, Game] = {}

        self.last_checkpoint = time.time()

        self.lock = Lock()

        self.rest = f"http://{settings.REST_HOST}:{settings.REST_PORT}" if settings.REST_PORT else None

        self.logger = logging.getLogger(__name__)

        self.logger.info("Server started")

    def Register(self, request, context):
        if request.name in self.name_2_registered_clients:
            context.abort(
                code=grpc.StatusCode.ALREADY_EXISTS, details=f"client with name {request.name} already registered."
            )

        else:
            if self.rest is not None:
                requests.post(self.rest + f"/players/{request.name}", json={"name": request.name})
            client_stub = ClientStub(request.host, request.port, request.name)
            self.id_2_registered_clients[client_stub.id] = client_stub
            self.name_2_registered_clients[client_stub.name] = client_stub
            self.id_2_active_clients[client_stub.id] = client_stub
            self.name_2_active_client[client_stub.name] = client_stub

            response = server_pb2.RegisterResponse()
            response.uuid = str(client_stub.id)

            return response

    def Leave(self, request, context):
        player_uuid = UUID(request.uuid)
        player = self.id_2_registered_clients[player_uuid]

        if player_uuid not in self.id_2_active_clients:
            return

        del self.id_2_active_clients[player_uuid]
        del self.name_2_active_client[player.name]

        self.id_2_game[player.game_id].kill_player(player.name)

        for client in self.id_2_active_clients.values():
            client.notify_leave(self.id_2_registered_clients[player_uuid].name)

        return google.protobuf.empty_pb2.Empty()

    def PerformAction(self, request, context):
        player = self.id_2_active_clients[UUID(request.uuid)]
        game = self.id_2_game[player.game_id]
        available_actions = game.get_available_actions_for_player(player.name)
        if request.action not in available_actions:
            context.abort(
                code=grpc.StatusCode.INVALID_ARGUMENT,
                details=f"Action is not available. Available actions: {available_actions}"
            )

        target_name = request.target_name if request.HasField("target_name") else None
        notification = game.add_player_action_generator_instance.send([player.name, request.action, target_name])

        self.logger.info(f"Notification to send to clients: {notification}")
        if request.action == ActionsEnum.KILL:
            self.send_action_notification_to_group(notification, list(game.name_2_mafia_player.keys()))
        elif request.action == ActionsEnum.CHECK:
            self.send_action_notification_to_group(notification, [game.cop_player.name])
        else:
            self.send_action_notification_to_group(notification, list(game.name_2_player.keys()))

        game.add_player_action_generator_instance.send(None)

        return google.protobuf.empty_pb2.Empty()

    def send_action_notification_to_group(self, notification: str, names: list[str]):
        for name in names:
            if name in self.name_2_active_client:
                self.name_2_registered_clients[name].notify_action(notification)

    def connect_player_to_game(self, name: str) -> None:
        for game_id, game in self.id_2_game.items():
            if game.add_player(name):
                selected_game_id = game_id
                for player in self.id_2_game[selected_game_id].name_2_player.keys():
                    self.name_2_active_client[name].notify_join(player)

                break
        else:
            selected_game_id = uuid4()
            self.id_2_game[selected_game_id] = Game(selected_game_id)
            self.id_2_game[selected_game_id].add_player(name)

        for player in self.id_2_game[selected_game_id].name_2_player.keys():
            if self.name_2_active_client[player].game_id == selected_game_id:
                self.name_2_active_client[player].notify_join(name)

        player = self.name_2_registered_clients[name]
        player.game_id = selected_game_id
        self.id_2_active_clients[player.id] = player

    def start_games(self):
        if time.time() > self.last_checkpoint + 20:
            for game_id, game in self.id_2_game.items():
                if game.ready_to_start:
                    game.start_game()

                    for name, player in game.name_2_player.items():
                        self.name_2_active_client[name].send_role(player.role)

            self.last_checkpoint = time.time()

    def connect_players_to_games(self):
        for name, client in self.name_2_active_client.items():
            if client.game_id is None:
                self.connect_player_to_game(name)

    def check_finished_games(self) -> None:
        games_to_del = []
        for game_id, game in self.id_2_game.items():
            if game.finished:
                games_to_del.append(game_id)
                for name in game.name_2_player.keys():
                    self.name_2_active_client[name].notify_action(f"Game finished, {game.check_game_end()} won")
                    self.name_2_registered_clients[name].game_id = None
                    for player in game.name_2_player.keys():
                        self.name_2_active_client[name].notify_leave(player)

        for game_id in games_to_del:
            self.update_player_data(self.id_2_game[game_id])
            del self.id_2_game[game_id]

    def update_player_data(self, game: Game) -> None:
        winner_team = game.check_game_end()

        for name, player in game.name_2_player.items():
            requests.post(self.rest + f"/players/{name}", json={"name": name})
            requests.patch(self.rest + f"/players/add_to_player/{name}", json={
                "name": name,
                "wins": (player.role == winner_team),
                "losses": (player.role != winner_team),
                "time_played": game.time_end - game.time_start
            })

    def send_action_requests(self) -> None:
        with self.lock:
            for game in self.id_2_game.values():
                if game.started and not game.finished:
                    for player in game.name_2_player.values():
                        if player.name in self.name_2_active_client and player.alive:
                            if available_actions := game.get_available_actions_for_player(player.name):
                                self.name_2_active_client[player.name].send_available_actions(available_actions)

    def send_notifications(self):
        for game in self.id_2_game.values():
            if game.started and not game.finished:
                for player in game.name_2_player.values():
                    if player.name in self.name_2_active_client:
                        for notification in game.get_and_delete_notifications():
                            self.name_2_active_client[player.name].notify_action(notification)

    def check_liveness(self):
        to_delete = set()
        for client in self.name_2_active_client.values():
            try:
                client.livez()
            except grpc.RpcError:
                to_delete.add(client.name)
        for name in to_delete:
            del self.name_2_active_client[name]


def serve():
    server_servicer = ServerServicer()

    executor = futures.ThreadPoolExecutor(max_workers=1)

    server = grpc.server(executor)
    server_pb2_grpc.add_ServerServicer_to_server(server_servicer, server)
    server.add_insecure_port(f"{settings.GRPC_SERVER_HOST}:{settings.GRPC_SERVER_PORT}")
    server.start()

    while True:
        server_servicer.check_liveness()

        server_servicer.check_finished_games()

        server_servicer.connect_players_to_games()

        server_servicer.start_games()

        server_servicer.send_notifications()

        server_servicer.send_action_requests()

        server_servicer.logger.info(server_servicer.name_2_active_client)

        time.sleep(4)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    serve()
