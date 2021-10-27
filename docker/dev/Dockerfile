FROM ubuntu:latest

LABEL version="2.0"
LABEL Christian Sargusingh "https://github.com/cSDes1gn"

# Grab dependencies and generate locale
RUN apt update && apt upgrade -y && apt install -y git sudo locales && locale-gen en_US.UTF-8

WORKDIR /app

# add package dependancy indices
COPY apt-packages.txt /app/apt-packages.txt
COPY pre-requirements.txt /app/pre-requirements.txt
COPY requirements.txt /app/requirements.txt

# install dependancies
RUN DEBIAN_FRONTEND=noninteractive TZ=America/New_York \
    xargs -a apt-packages.txt apt install \
    -y --no-install-recommends --fix-missing
RUN python3 -m pip install --upgrade -r pre-requirements.txt --ignore-installed
RUN python3 -m pip install -r requirements.txt

# install tis from source
RUN git clone https://github.com/TheImagingSource/tiscamera.git
WORKDIR /app/tiscamera
RUN git checkout 97b40072c4379bec65242cfba0270be0d7634188
RUN ./scripts/install-dependencies.sh --compilation --runtime --yes
RUN mkdir build
WORKDIR /app/tiscamera/build
RUN cmake -DBUILD_ARAVIS=OFF -DBUILD_TOOLS=ON ..
RUN make && make install
WORKDIR /app
RUN rm -rfv tiscamera/


CMD [ "./bin/monitor", "-d"]