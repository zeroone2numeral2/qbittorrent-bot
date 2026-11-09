# Local Telegram Bot API server (tdlib/telegram-bot-api) patched to reach Telegram through an MTProto proxy.
# The patch adds the --mtproto-proxy option / TELEGRAM_MTPROTO_PROXY environment variable.
FROM debian:bookworm-slim AS build

ARG TBA_COMMIT=e3e9dd8e5b3d7ab8537cd5a10dc31d5ffa8f82d1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates git make cmake clang gperf php-cli zlib1g-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone https://github.com/tdlib/telegram-bot-api.git . \
    && git checkout "$TBA_COMMIT" \
    && git submodule update --init --recursive

COPY mtproto-proxy.patch /tmp/mtproto-proxy.patch
RUN git apply /tmp/mtproto-proxy.patch

# TDLib needs a lot of RAM to compile. To keep the build within a few GB:
# - clang uses noticeably less memory than g++ on these sources;
# - SplitSource.php (shipped with TDLib) cuts the largest TDLib .cpp files into smaller ones;
# - one compiler process at a time. Raise JOBS only if you have RAM to spare (about 4 GB per job).
ARG JOBS=1
ENV CC=clang CXX=clang++
RUN cmake -S td -B td/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build td/build --target prepare_cross_compiling -j "$JOBS" \
    && cd td && php SplitSource.php \
    && rm -rf build
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
