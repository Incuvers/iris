#!/bin/bash

source .env

printf "%b" "${OKB}Tearing down project${NC}\n"
docker-compose -f docker/"$STAGE"/docker-compose.yaml down
printf "%b" "${OKG} ✓ ${NC}complete\n"