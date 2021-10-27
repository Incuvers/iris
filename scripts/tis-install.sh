#!/bin/bash

set -e

# Install tis from source
cd /home/ubuntu/ || exit 1
git clone https://github.com/TheImagingSource/tiscamera.git
cd tiscamera
git checkout 97b40072c4379bec65242cfba0270be0d7634188
sudo ./scripts/install-dependencies.sh --compilation --runtime --yes
mkdir build
cd build
cmake -DBUILD_ARAVIS=OFF -DBUILD_TOOLS=ON ..
make
sudo make install
cd /home/ubuntu/ || exit 1
rm -rfv tiscamera/
