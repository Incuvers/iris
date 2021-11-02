#!/bin/bash

source .env

printf "%b" "${OKB}Building project${NC}\n"
docker compose -f docker/dev/docker-compose.yaml up