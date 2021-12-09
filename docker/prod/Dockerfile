FROM ubuntu:latest

LABEL version="2.0"
LABEL Christian Sargusingh "https://github.com/cSDes1gn"

# Grab dependencies and generate locale
WORKDIR /app

# add package dependancy indices
COPY apt-packages.txt /app/apt-packages.txt
RUN apt update && \
    apt upgrade -y && \
    apt install -y git sudo locales && \
    locale-gen en_US.UTF-8 && \
    DEBIAN_FRONTEND=noninteractive TZ=America/New_York xargs -a apt-packages.txt apt install -y --no-install-recommends --fix-missing

COPY . .

# mount the repository root and install the application
RUN python3 -m pip install --upgrade -r pre-requirements.txt --ignore-installed
RUN python3 -m pip install .

ENTRYPOINT [ "iris"]