# Fresh SD card
Download and burn on a 32GB SD card:
http://cdimage.ubuntu.com/releases/20.04/release/ubuntu-20.04-preinstalled-server-arm64+raspi.img.xz

On first boot, a script is ran to create the default user, give it some time.

Log in with `ubuntu` as username, use `ubuntu` as password.
If it fails, wait for the creation script to finish.

You will be prompted for a new password, please use `incuvers` (will be asked to re-type the current  password---it's `ubuntu`)
If you have the incuvers dev-board, the screen will look odd, this will be fixed in the firmware setup step below.

## Get internet
The first thing you want to do is get internet working.
If you are using ethernet, just plug it in and it should work, you can skip this step.
For wifi, keep on reading.
Make a copy of the default `netplan` file to hold the wifi setup you will use.
```bash
sudo cp /etc/netplan/50-cloud-init.yaml /etc/netplan/55-home.yaml
```
edit (as `sudo`!) the contents  so it looks like:
``` yaml
network:
  version: 2
  renderer: NetworkManager
  wifis:
    wlan0:
      dhcp4: true
      access-points:
        "YOUR_WIFI_SSID_HERE":
          password: "YOUR_WIFI_PASSWORD_HERE"
```
To apply these changes try `sudo netplan generate` followed by `sudo netplan apply`.
Check the status of `wlan0` using `ip addr` and look for it's assigned adddress.
You can also just `sudo reboot` if it doesn't work.

## Get the monitor repo
Before I use git, I like to create a public/private key pair and setup a new public key in Github so that I don't have to type in my password all the time.
For that, I log in via ssh and copy/paste the key.
Get a local clone of the repo:
``` bash
git clone git@github.com:Incuvers/monitor.git
```
And might as well setup my user:
```bash
git config --global user.name "David Sean"
git config --global user.email david.sean@gmail.com
```


## Requirements to run the monitor and webserver app
You can skip this step if you do not plan on running the monitor code on this machine.
It's probably good practice to go though these steps regardless.


### RPi firmware
The Raspberry pi firmware setup used at Incuvers is saved in the `monitor` repo under `./dev/BOOT/firmware`.
These files should be placed in `/boot/firmware/`.
If you cloned the monitor in your $HOME directory, just copy them with
``` bash
sudo cp ~/monitor/dev/BOOT/firmware/*.txt /boot/firmware/.
sudo cp ~/monitor/dev/BOOT/firmware/uboot.env /boot/firmware/.
```
Note that last line is there in order to skip the `uboot` prompt. See the `./dev/BOOT/readme.md` for more details.
Reboot to apply the new firmware config.
You should now have the screen in the proper portrait orientation.
Make sure you see the serial port is present.
You should also see a device at `/dev/ttyAMA0`:
```
crw-rw---- 1 root dialout 204, 64 Apr  1 17:23 /dev/ttyAMA0
```

## Network Manager
By default `Ubuntu 20.04 Server` does not ship with `network-manager` which a required `netplan` backend.
``` bash
sudo apt-get install network-manager
```
This allows you to use the example netplan in `monitor/daemon/netplan/.`, or to use IRIS hosted webApp to configure your network.


### WiringPi
See instructions at `./dev/software-reqs.md`

### TIS camera
See instructions at `./dev/software-reqs.md`

## Requirements to build the snap

### Snapd and snapcraft
Please use apt to install `snapd`.
install `snapd`
``` bash
sudo apt-get update
sudo apt-get install snapd
```

With it `snapd`, you can then install the snap version of snapcraft.
Note that if you want to build the snap with `lxd`, this step will be ran by the lxd-build script (below).
use `snap` to install `snapcraft`
``` bash
sudo snap install snapcraft --classic --channel=candidate
```

### lxd setup
Please follow the instructions shown in  `./monitor/dev/snap-build-instructions.md`
TLDR: just run `lxd-build.sh`
