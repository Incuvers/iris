#!/bin/bash

source .env

trap 'handler $? $LINENO' ERR

handler () {
    printf "%b" "${FAIL} ✗ ${NC} ${0##*/} failed on line $2 with exit status $1\n"
    exit "$1"
}
printf "%b" "${OKB}Checking for .env diff in $DOCKER_ROOT/${NC}\n"
if [ ! -f ./"$DOCKER_ROOT"/.env ] || [ "$(diff ".env" "./$DOCKER_ROOT/.env")" ] ; then
    cp .env ./"$DOCKER_ROOT"/.
    printf "%b" "${OKG} ✓ ${NC} copied .env file to $DOCKER_ROOT/\n"
else
    printf "%b" "${OKG} ✓ ${NC} ok\n"
fi
printf "%b" "${OKB}Validating docker compose configuration${NC}\n"
cd "$DOCKER_ROOT" || exit 1
docker compose config
cd - > /dev/null || exit 1
printf "%b" "${OKG} ✓ ${NC}validation complete\n"