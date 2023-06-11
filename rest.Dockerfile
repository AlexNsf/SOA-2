FROM python:3.10

COPY . .
RUN pip3 install pip-tools

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "rest_server.py"]