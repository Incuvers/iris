#!/bin/bash

# wait for rabbitmq container
./docker/wfi.sh -h rmq -p 5672

python3 -m monitor