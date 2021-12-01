#!/bin/bash

source .env

printf "%b" "${OKB}Pulling images for $STAGE${NC}\n"
docker-compose -f docker/"$STAGE"/docker-compose.yaml pull
printf "%b" "${OKG} ✓ ${NC}complete\n"