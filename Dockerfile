FROM python:slim-bullseye
ADD . /app
RUN cd /app && pip3 install -r requirements.txt
WORKDIR /app
ENTRYPOINT python main.py
