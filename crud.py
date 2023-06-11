import sqlite3
from typing import Any
from settings import settings


def init_db() -> None:
    with sqlite3.connect(settings.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS players (
            name TEXT PRIMARY KEY, age INTEGER, email TEXT, avatar TEXT,
             wins INTEGER, losses INTEGER, time_played FLOAT, gender TEXT)"""
        )

    conn.close()


def add_player(name: str, **kwargs: Any) -> None:
    with sqlite3.connect(settings.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT EXISTS(SELECT 1 FROM players WHERE name='{name}');")

        if cur.fetchone()[0] == 0:
            cur.execute(
                f"""INSERT INTO players ({', '.join(['name'] + list(kwargs.keys()))})
                 VALUES ({', '.join('?' * (len(kwargs) + 1))})""", [name] + list(kwargs.values())
            )

    conn.close()


def update_player(name: str, **kwargs: Any) -> None:
    with sqlite3.connect(settings.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f"""UPDATE players SET
                       {', '.join([f'{column} = ?' for column in kwargs.keys()])}\
                       WHERE name = '{name}'""",
                    list(kwargs.values()))

    conn.close()


def delete_player(name: str) -> None:
    with sqlite3.connect(settings.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM players WHERE name = ?", [name])

    conn.close()


def get_player(name: str) -> dict | None:
    with sqlite3.connect(settings.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE name = ?", [name])
        res = cur.fetchone()

    conn.close()
    return {column: value for column, value in
            zip(["name", "age", "email", "avatar", "wins", "losses", "time_played", "gender"], res)}


def get_players() -> list | None:
    with sqlite3.connect(settings.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players")
        res = cur.fetchall()

    conn.close()
    return res


def add_to_player(name: str, **kwargs) -> None:
    player = get_player(name)
    for key, value in kwargs.items():
        player[key] += value
    update_player(**player)
