#!/bin/bash

source .env

printf "%b" "${OKB}Authenticating $USERNAME with github container registry${NC}\n"
echo "$CR_PAT" | docker login ghcr.io -u "$USERNAME" --password-stdin
printf "%b" "${OKB}Building project${NC}\n"
docker-compose -f docker/"$STAGE"/docker-compose.yaml up