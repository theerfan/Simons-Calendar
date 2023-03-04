# syntax=docker/dockerfile:1

FROM python:3.10-buster

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

CMD [ "python3", "src/main.py" ]