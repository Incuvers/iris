#!/bin/bash

source .env

trap 'handler $? $LINENO' ERR

handler () {
    printf "%b" "${FAIL} ✗ ${NC} ${0##*/} failed on line $2 with exit status $1\n"
    exit "$1"
}
printf "%b" "${OKB}Checking for .env diff in docker/$STAGE/${NC}\n"
if [ ! -f ./docker/"$STAGE"/.env ] || [ "$(diff ".env" "./docker/$STAGE/.env")" ] ; then
    cp .env ./docker/"$STAGE"/.
    printf "%b" "${OKG} ✓ ${NC} copied .env file to docker/$STAGE/\n"
else
    printf "%b" "${OKG} ✓ ${NC} ok\n"
fi
printf "%b" "${OKB}Validating docker compose configuration${NC}\n"
cd docker/"$STAGE" || exit 1
docker-compose config
cd - > /dev/null || exit 1
printf "%b" "${OKG} ✓ ${NC}validation complete\n"