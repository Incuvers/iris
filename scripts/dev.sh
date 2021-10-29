#!/bin/bash

# handle all non-zero exit status codes with a slack notification
trap 'handler $? $LINENO' ERR

handler () {
    printf "%b" "${FAIL} ✗ ${NC} ${0##*/} failed on line $2 with exit status $1\n"
}

printf "%b" "${OKB}Building project${NC}\n"
docker compose -f docker/dev/docker-compose.yaml up
printf "%b" "${OKG} ✓ ${NC}containers active\n"