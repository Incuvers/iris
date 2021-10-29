FROM ubuntu:latest

LABEL version="2.0"
LABEL Christian Sargusingh "https://github.com/cSDes1gn"

# Grab dependencies and generate locale
RUN apt update && apt upgrade -y && apt install -y git sudo locales && locale-gen en_US.UTF-8

WORKDIR /app

# add package dependancy indices
COPY apt-packages.txt /app/apt-packages.txt

# install dependancies
RUN DEBIAN_FRONTEND=noninteractive TZ=America/New_York \
    xargs -a apt-packages.txt apt install \
    -y --no-install-recommends --fix-missing

# mount the repository root and install the application
COPY . .
RUN python3 -m pip install .

ENTRYPOINT [ "./docker/prod/entry"]