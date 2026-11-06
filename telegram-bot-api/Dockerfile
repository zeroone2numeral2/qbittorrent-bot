# Local Telegram Bot API server (tdlib/telegram-bot-api) patched to reach Telegram through an MTProto proxy.
# The patch adds the --mtproto-proxy option / TELEGRAM_MTPROTO_PROXY environment variable.
FROM debian:bookworm-slim AS build

ARG TBA_COMMIT=e3e9dd8e5b3d7ab8537cd5a10dc31d5ffa8f82d1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates git make cmake g++ gperf zlib1g-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone https://github.com/tdlib/telegram-bot-api.git . \
    && git checkout "$TBA_COMMIT" \
    && git submodule update --init --recursive

COPY mtproto-proxy.patch /tmp/mtproto-proxy.patch
RUN git apply /tmp/mtproto-proxy.patch

# Client.cpp needs a lot of RAM to compile; lower -j if the build gets OOM-killed
ARG JOBS=2
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --target install -j "$JOBS" \
    && strip /usr/local/bin/telegram-bot-api

FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates zlib1g libssl3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /usr/local/bin/telegram-bot-api /usr/local/bin/telegram-bot-api

VOLUME /var/lib/telegram-bot-api
EXPOSE 8081
ENTRYPOINT ["telegram-bot-api", "--dir=/var/lib/telegram-bot-api", "--http-port=8081"]
