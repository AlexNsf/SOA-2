import time
from collections.abc import Generator
from dataclasses import dataclass
from uuid import UUID, uuid4

from enums import ActionsEnum, DayOfTimeEnum, RoleEnum
from settings import roles_config
from random import shuffle

from threading import Lock

from logging import getLogger


@dataclass
class Player:
    name: str
    role: RoleEnum | None = None
    alive: bool = True
    asleep: bool = False


class Game:
    def __init__(self, id: UUID, amount_of_players_to_start: int = 4):
        self.id = id

        self.time_start: float = time.time()
        self.time_end: float | None = None

        self.name_2_player: dict[str, Player] = {}
        self.name_2_mafia_player: dict[str, Player] = {}
        self.cop_player: Player | None = None

        self.time_of_day: DayOfTimeEnum | None = None
        self._is_first_day: bool = True
        self.started: bool = False
        self.finished: bool = False

        self.amount_of_players_to_start: int = amount_of_players_to_start
        self.amount_of_alive_civilian_players: int | None = None
        self.amount_of_alive_mafia_players: int | None = None
        self.amount_of_done_players: int = 0

        self.civilian_votes: dict[str, int] = {}
        self.mafia_votes: dict[str, int] = {}

        self.name_2_actions: dict[str, set[ActionsEnum]] = {}
        self.found_mafia: Player | None = None

        self.notifications: list[str] = []

        self.add_player_action_generator_instance = self._add_player_action_generator()
        self.add_player_action_generator_instance.send(None)

        self.lock = Lock()

        self.logger = getLogger(__name__)

        self.logger.info(f"New game with id {self.id} was created")

    @property
    def ready_to_start(self) -> bool:
        return len(self.name_2_player) >= self.amount_of_players_to_start and not self.started and not self.finished

    def add_player(self, name: str) -> bool:
        with self.lock:
            if self.started or len(self.name_2_player) >= self.amount_of_players_to_start:
                return False

            self.name_2_player[name] = Player(name=name)

            self.logger.info(f"Player with name {name} was added")

            return True

    def start_game(self) -> bool:
        if self.started or not self.ready_to_start:
            return False

        self.started = True

        roles = []
        for role, amount in roles_config[len(self.name_2_player)].items():
            roles.extend([role] * amount)
        shuffle(roles)

        for player, role in zip(self.name_2_player.values(), roles):
            player.role = role

            if role == RoleEnum.MAFIA:
                self.name_2_mafia_player[player.name] = player

            elif role == RoleEnum.COP:
                self.cop_player = player

        self.amount_of_alive_mafia_players = roles_config[len(self.name_2_player)][RoleEnum.MAFIA]
        self.amount_of_alive_civilian_players = len(self.name_2_player) - self.amount_of_alive_mafia_players

        self.logger.info(f"Game with id {self.id} started, players are: {self.name_2_player.values()}")

        self._day_actions()

        return True

    def check_game_end(self) -> RoleEnum | None:
        if self.amount_of_alive_mafia_players == 0:
            res = RoleEnum.CIVILIAN
        elif self.amount_of_alive_mafia_players == self.amount_of_alive_civilian_players:
            res = RoleEnum.MAFIA
        else:
            return None

        if self.time_end is None:
            self.time_end = time.time()

        self.finished = True

        return res

    def get_available_actions_for_player(self, name: str) -> list[ActionsEnum]:
        with self.lock:
            actions = set()

            if not self.name_2_player[name].alive or self.finished:
                return list(actions)

            if self.time_of_day == DayOfTimeEnum.DAY:
                actions.update([ActionsEnum.SLEEP, ActionsEnum.VOTE])

                if self.found_mafia is not None and self.cop_player.name == name:
                    actions.add(ActionsEnum.SHOW_MAFIA)
            else:
                if name in self.name_2_mafia_player:
                    actions.add(ActionsEnum.KILL)
                elif self.cop_player is not None and name == self.cop_player.name:
                    actions.add(ActionsEnum.CHECK)
            self.logger.info(actions)
            self.logger.info(self.name_2_actions.get(name))
            self.logger.info(self.name_2_player)
            self.logger.info(self.finished)
            self.logger.info(list(actions - (self.name_2_actions.get(name) or set())))
            self.logger.info('\n\n')
            return list(actions - (self.name_2_actions.get(name) or set()))

    def get_and_delete_notifications(self) -> list[str]:
        notifications = self.notifications.copy()
        self.notifications = []
        return notifications

    def kill_player(self, name: str) -> None:
        if name in self.name_2_mafia_player:
            self.amount_of_alive_mafia_players -= 1
        else:
            self.amount_of_alive_civilian_players -= 1

        self.name_2_player[name].alive = False

        self.notifications.append(f"{name} was killed by mafia")

        winner_team = self.check_game_end()
        if winner_team is not None:
            self.notifications.append(f"{winner_team} won the game with id {self.id}")

    def _get_player_name_with_most_votes(self) -> str | None:
        if not self.civilian_votes:
            return None

        sorted_votes = sorted(self.civilian_votes.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_votes) == 1:
            return sorted_votes[0][0]

        if sorted_votes[0][1] == sorted_votes[1][1]:
            return None

        return sorted_votes[0][0]

    def _add_player_action_generator(self) -> Generator[str, [str, ActionsEnum, str | None]]:  # Действия поприменяются в виде генератора,
        while True:                                                                            # так как от них требуется мгновенный ответ,
            name, action, target_name = yield                                                  # от которого теоретически будет зависеть ход
                                                                                               # другого игрока
            player = self.name_2_player[name]

            self.name_2_actions[name] = self.name_2_actions.get(name, set()) | {action}

            if action == ActionsEnum.SLEEP:
                player.asleep = True
                self.amount_of_done_players += 1

                yield f"Player {name} goes to sleep"
            elif action == ActionsEnum.VOTE:
                self.civilian_votes[target_name] = self.civilian_votes.get(target_name, 0) + 1

                yield f"Player {name} voted for {target_name}. {target_name} now has {self.civilian_votes[target_name]} votes"
            elif action == ActionsEnum.SHOW_MAFIA:
                yield f"Cop {name} found mafia: {self.found_mafia.name}"
            elif action == ActionsEnum.KILL:
                self.mafia_votes[target_name] = self.mafia_votes.get(target_name, 0) + 1
                self.amount_of_done_players += 1

                yield f"Mafia {name} want to kill {target_name} this night"
            else:
                self.amount_of_done_players += 1

                if target_name in self.name_2_mafia_player:
                    self.found_mafia = self.name_2_mafia_player[target_name]

                    yield f"{target_name} is mafia"
                else:
                    yield f"{target_name} is not mafia"

            if self.time_of_day == DayOfTimeEnum.DAY:
                if self.amount_of_done_players == self.amount_of_alive_mafia_players + self.amount_of_alive_civilian_players:
                    self._night_actions()
            else:
                if self.amount_of_done_players == self.amount_of_alive_mafia_players + self.cop_player.alive:
                    self._day_actions()

    def _refresh(self) -> None:
        self.amount_of_done_players = 0

        self.civilian_votes = {}
        self.mafia_votes = {}

        self.name_2_actions = {}
        self.found_mafia = None

    def _day_actions(self) -> None:
        self.logger.info(repr(self))

        for player in self.name_2_player.values():
            player.asleep = False

        self.time_of_day = DayOfTimeEnum.DAY

        if self._is_first_day:
            self._is_first_day = False
            self.time_of_day = DayOfTimeEnum.NIGHT
        else:
            killed_player_name = max(self.mafia_votes.items(), key=lambda x: x[1])[0]

            self.kill_player(killed_player_name)

            self._refresh()

            self.notifications.append(f"New day started!")

    def _night_actions(self) -> None:
        self.logger.info(repr(self))
        self.time_of_day = DayOfTimeEnum.NIGHT
        most_voted_player = self._get_player_name_with_most_votes()

        if most_voted_player is not None:
            self.kill_player(most_voted_player)

        else:
            self.notifications.append("No one was killed today")

        self._refresh()

        self.notifications.append(f"New night started!")


if __name__ == '__main__':  # for debug purposes
    game = Game(uuid4())
    while True:
        try:
            action, *params = input().split()

            if params and params[0] == "()":
                print(getattr(game, action)())
            elif params:
                print(getattr(game, action)(*params))
            else:
                print(getattr(game, action))
        except Exception as e:
            print(e)
