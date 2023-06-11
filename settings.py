from pydantic import BaseSettings

from enums import RoleEnum


class Settings(BaseSettings):
    GRPC_SERVER_HOST: str = "proto_server"
    GRPC_SERVER_PORT: int = 50051

    GRPC_CLIENT_HOST: str = "0.0.0.0"
    GRPC_CLIENT_PORT: int = 50052

    CLIENT_NAME: str = "DEFAULT"

    DB_PATH: str = "./player.db"

    REST_HOST: str = "app"
    REST_PORT: int = 8000


settings = Settings()

roles_config: dict[int, dict[RoleEnum, int]] = {4: {RoleEnum.CIVILIAN: 2, RoleEnum.MAFIA: 1, RoleEnum.COP: 1}}
