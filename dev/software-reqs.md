# RPi prod

The production machine is a `RPi4 (1GB RAM) with UbuntuCore 20.04`.
The production SD card has a capacity of 16GB.
The base image here is Ubuntu CORE 20.04 with the `iris-incuvers` snaps installed.

# RPi dev Hardware

The recommended development machine is a `RPi4 (4GB RAM) with Ubuntu Server 20.04`. The development SD card should have capacity of 32GB minimum.
You **WILL** need 4GB of RAM to build the Snap.

# RPi DEV Software

## python packages from apt
Some packages are best installed using `apt` and NOT `pip`.
Usually this is because `pip` will miss a lof of additional libraries (`CBlas`, `Lapack`, for `numpy` ). Use `apt`:
``` bash
sudo apt install python3-numpy
sudo apt install python3-pygame

```

## pygame2

Pygame was updated to pygame2 and will need additional requirements
``` bash
sudo apt install libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev libsdl2-mixer-dev
```

## Install TIS camera
https://github.com/TheImagingSource/tiscamera

install cmake
```bash
sudo snap install cmake --classic
```

go to the home directory and...
``` bash
git clone https://github.com/TheImagingSource/tiscamera.git
cd tiscamera
git checkout v-tiscamera-0.13.1
sudo ./scripts/install-dependencies.sh --compilation --runtime
mkdir build
cd build
```
``` bash
cmake -DBUILD_ARAVIS=OFF -DBUILD_TOOLS=ON ..
make
sudo make install
```

Install gst library
```bash
sudo apt install python3-gst-1.0
```

## Serial communication with the motherboard

The port should now be `/dev/ttys0` (It was formly `/dev/ttyAMA0`).
May need to verify this in the `Interface` class and `test_serial.py`/`serial_simple.py`.
The file `/boot/firmnware/usercfg.txt` should have:
```
enable_uart=1
dtoverlay=pi3-disable-bt
```


