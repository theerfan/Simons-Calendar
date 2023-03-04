# syntax=docker/dockerfile:1

FROM python:3.10-buster

WORKDIR /app

COPY requirements.in requirements.in
RUN pip3 install -r requirements.in

COPY . .

CMD [ "python3", "src/main.py" ]