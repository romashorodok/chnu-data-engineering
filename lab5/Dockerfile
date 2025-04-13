FROM python:3.13-alpine3.21 as app

WORKDIR /app

RUN pip install kafka-python==2.1.5

COPY . .

RUN python3 ./unzip.py
