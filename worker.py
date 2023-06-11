import crud
from reportlab.pdfgen.canvas import Canvas

from logging import getLogger
logger = getLogger(__name__)


def target(queue_in):
    not_in_db = "Not in db"

    while True:
        task_id, name = queue_in.get()
        if (data := crud.get_player(name)) is None:
            canvas = Canvas(f"contents/pdfs/{task_id}.pdf", pagesize=(300, 110))
            canvas.drawString(12, 25, f"No such player: {name}")
            canvas.save()

        else:
            canvas = Canvas(f"contents/pdfs/{task_id}.pdf", pagesize=(300, 110))
            canvas.drawString(10, 90, f"Name: {data['name']}")
            canvas.drawString(10, 80, f"Age: {not_in_db if data.get('age') is None else data['age']}")
            canvas.drawString(10, 70, f"Email: {not_in_db if data.get('email') is None else data['email']}")
            canvas.drawString(10, 60, f"Wins: {not_in_db if data.get('wins') is None else data['wins']}")
            canvas.drawString(10, 40, f"Losses: {not_in_db if data.get('losses') is None else data['losses']}")
            canvas.drawString(10, 30, f"Gender: {not_in_db if data.get('gender') is None else data['gender']}")
            canvas.drawString(10, 20, f"Time played: {not_in_db if data.get('time_played') is None else (str(round(data['time_played'])) + 'seconds')}")

            canvas.drawImage(f"contents/avatars/{data['avatar']}", x=200, y=10, width=50, height=50)
            canvas.save()

        logger.info("Generated pdf successfully")
