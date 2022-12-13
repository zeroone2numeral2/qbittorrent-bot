FROM python:slim
ADD . /app
RUN apt update && apt install -y gcc \
    && cd /app \
    && pip3 install -r requirements.txt \
    && apt purge --auto-remove -y gcc \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENTRYPOINT python main.py
