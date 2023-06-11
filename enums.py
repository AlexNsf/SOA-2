from enum import Enum


class RoleEnum(str, Enum):
    CIVILIAN = "CIVILIAN"
    MAFIA = "MAFIA"
    COP = "COP"


class DayOfTimeEnum(str, Enum):
    DAY = "DAY"
    NIGHT = "NIGHT"


class ActionsEnum(str, Enum):
    SLEEP = "SLEEP"
    VOTE = "VOTE"
    SHOW_MAFIA = "SHOW_MAFIA"
    KILL = "KILL"
    CHECK = "CHECK"
