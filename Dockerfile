FROM python:3.11.7-slim
ADD . /app
RUN apt update && apt install -y gcc
RUN cd /app && pip3 install -r requirements.txt
WORKDIR /app
ENTRYPOINT python main.py
