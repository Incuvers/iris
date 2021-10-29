#!/bin/bash

source .env

# handle all non-zero error status codes
trap 'handler $? $LINENO' ERR

handler () {
    # print error message and propagate error status
    if [ "$1" != "0" ]; then
        printf "%b" "${FAIL} ✗ ${NC} Failed with status: $1 on line: $2\n"
        exit "$1"
    fi
}

printf "%b" "${OKB}Linting yaml syntax${NC}\n"
yamllint .
printf "%b" "${OKG} ✓ ${NC} Pass\n"

printf "%b" "${OKB}Linting shell scripts${NC}\n"
shellcheck -x scripts/*
printf "%b" "${OKG} ✓ ${NC} Pass\n"

printf "%b" "${OKB}Linting python w/ flake8${NC}\n"
flake8 .
printf "%b" "${OKG} ✓ ${NC} Pass\n"