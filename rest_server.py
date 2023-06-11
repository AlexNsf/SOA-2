from flask import Flask, abort, request, Response, send_from_directory
from queue import Queue
import logging
import status
from uuid import uuid4
import threading
from settings import settings
from worker import target

import crud

logger = logging.getLogger(__name__)

queue = Queue()

app = Flask(__name__)


@app.get("/players/<string:name>")
def get_player(name: str):
    try:
        res = crud.get_player(name=name)
    except Exception as e:
        abort(Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR))

    return Response(str(res), status=status.HTTP_200_OK)


@app.get("/players")
def get_players():
    try:
        res = crud.get_players()
    except Exception as e:
        abort(Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR))

    return Response(str(res), status=status.HTTP_200_OK)


@app.post("/players/<string:name>")
def add_player(name: str):
    logging.info(f"Add player {name}")
    data = request.get_json()

    try:
        crud.add_player(
            name,
            age=data.get("age"),
            email=data.get("email"),
            avatar="img.png",
            wins=0,
            losses=0,
            time_played=0,
            gender=data.get("gender")
        )
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        abort(Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR))

    return Response(status=status.HTTP_200_OK)


@app.patch("/players/<string:name>")
def update_player(name: str):
    data = request.get_json()

    try:
        crud.update_player(
            name,
            age=data.get("age"),
            email=data.get("email"),
            gender=data.get("gender")
        )
    except Exception as e:
        abort(Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR))

    return Response(status=status.HTTP_200_OK)


@app.patch("/players/avatar/<string:name>")
def update_avatar(name: str):
    img = request.files.get("avatar")
    avatar = "img.png"
    if img is not None:
        img.save(f"contents/avatars/{name}.png")
        avatar = f"{name}.png"

    try:
        crud.update_player(name, avatar=avatar)
    except Exception as e:
        abort(Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR))

    return Response(status=status.HTTP_200_OK)


@app.patch("/players/add_to_player/<string:name>")
def add_to_player(name: str):
    data = request.get_json()

    try:
        crud.add_to_player(
            name,
            wins=data.get("wins"),
            losses=data.get("losses"),
            time_played=data.get("time_played")
        )
    except Exception as e:
        abort(Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR))

    return Response(status=status.HTTP_200_OK)


@app.post("/pdfs/<string:name>")
def post_task(name: str):
    id = uuid4()
    queue.put((id, name))
    return Response(f"Link to get pdf: http://127.0.0.1:{settings.REST_PORT}/pdfs/{id}.pdf", status=status.HTTP_200_OK)


@app.get("/pdfs/<path:path>")
def get_pdf(path: str):
    return send_from_directory("contents/pdfs", path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting rest server")

    crud.init_db()
    worker_thread = threading.Thread(target=target, args=[queue])
    worker_thread.start()
    app.run(host="0.0.0.0", port=settings.REST_PORT)
    worker_thread.join()
