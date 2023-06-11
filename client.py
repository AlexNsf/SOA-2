import logging
import random
import time
from concurrent import futures
from logging import getLogger

import grpc

from python_proto import server_pb2, server_pb2_grpc, client_pb2, client_pb2_grpc
from settings import settings
import google.protobuf.empty_pb2


class ClientServicer(client_pb2_grpc.ClientServicer):
    def __init__(self, host: str, port: int, server_host: str, server_port: int, name: str):
        self.id: int | None = None
        self.host = host
        self.port = port
        self.name: str = name
        self.action: str | None = None
        self.connected_player_names: set[str] = set()

        self.stub = server_pb2_grpc.ServerStub(grpc.insecure_channel(f"{server_host}:{server_port}"))

        self.logger = getLogger(__name__)

        self.logger.info("New client was created")

    def NotifyJoin(self, request, context):
        self.connected_player_names.add(request.player)

        self.logger.info(f"{request.player} joined the game")
        self.logger.info(f"Currently connected players are: {self.connected_player_names}")

        return google.protobuf.empty_pb2.Empty()

    def NotifyLeave(self, request, context):
        self.connected_player_names.discard(request.player)

        self.logger.info(f"{request.player} left the game")
        self.logger.info(f"Currently connected players are: {self.connected_player_names}")

        return google.protobuf.empty_pb2.Empty()

    def NotifyAction(self, request, context):
        self.logger.info(request.notification)

        return google.protobuf.empty_pb2.Empty()

    def SendRole(self, request, context):
        self.logger.info(f"Your role for this game is {request.role}")

        return google.protobuf.empty_pb2.Empty()

    def SendAvailableActions(self, request, context):
        self.logger.info(f"Available actions: {request.actions}")

        self.action = random.choice(request.actions)

        return google.protobuf.empty_pb2.Empty()

    def Livez(self, request, context):
        self.logger.info("Got liveness probe")

        response = client_pb2.LivezResponse()
        return response

    def connect_to_server(self):
        request = server_pb2.RegisterRequest()
        request.host = self.host
        request.port = self.port
        request.name = self.name

        try:
            response = self.stub.Register(request, timeout=1)
        except grpc.RpcError as e:
            self.logger.error("Got error while registering to server:")
            self.logger.error(e)
        else:
            self.id = response.uuid
            self.logger.info(f"Successfully registered to server. Your id is: {response.uuid}")

    def send_action(self):
        if self.action is not None:
            target_name = random.choice(list(self.connected_player_names - {self.name}))

            action_request = server_pb2.PerformActionRequest()
            action_request.uuid = str(self.id)
            action_request.action = self.action
            action_request.target_name = target_name

            self.action = None

            try:
                self.stub.PerformAction(action_request, timeout=1)
            except grpc.RpcError as e:
                logging.info(e)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    client = ClientServicer(
        settings.GRPC_CLIENT_HOST,
        settings.GRPC_CLIENT_PORT,
        settings.GRPC_SERVER_HOST,
        settings.GRPC_SERVER_PORT,
        settings.CLIENT_NAME
    )
    client_pb2_grpc.add_ClientServicer_to_server(client, server)
    server.add_insecure_port(f"{client.host}:{client.port}")
    server.start()

    client.connect_to_server()

    while True:
        client.send_action()
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    serve()
