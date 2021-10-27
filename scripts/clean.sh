#!/bin/bash

# shellcheck disable=SC1091
source .env

# handle all non-zero exit status codes with a slack notification
trap 'handler $? $LINENO' ERR

handler () {
    printf "%b" "${FAIL} ✗ ${NC} ${0##*/} failed on line $2 with exit status $1\n"
    exit $1
}

printf "%b" "${OKB}Cleaning docker environment${NC}\n"
docker compose -f docker/dev/docker-compose.yaml down --rmi all --volumes;
docker compose -f docker/dev/docker-compose.yaml rm -f;
docker image prune --force;
printf "%b" "${OKG} ✓ ${NC} complete\n"