#!/bin/bash
HOST="$(cut -d':' -f1<<<"$RABBITMQ_ADDR")"
PORT="$(cut -d':' -f2<<<"$RABBITMQ_ADDR")"

# wait for rabbitmq container
./docker/dev/wfi.sh -h "$HOST" -p "$PORT" -t 30

python3 -m monitor