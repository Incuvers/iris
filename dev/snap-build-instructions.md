# Instructions for Building Snap on core20

Note: do not install any packages using `apt` unless explicitly instructed since we will run into permission problems when using building using `snapcraft`. The packages must be installed as `snaps`.

## Building Snap using LXD container (Default for devs)
For the purposes of homogenizing our development platforms we should be using a container to build the snap on. This way its always from a clean copy of 20.04 and saves us from having to perform fresh flashes of 20.04 on our RPis. This is a short set of steps for starting up an lxd container on the RPi for the sole purpose of building the snap.

1. Run first time setup for lxd
Initialize container setup by navigating to `~/monitor`
```bash
 $ cd ~
 $ cd monitor/
 $ ./lxd-setup.sh
```
The container is configured to auto in the script. If there are issues, manually run `sudo lxd init` and if you have ran the init in the past the storage and network bridge will remain opened resources so be sure to say no when prompted to create new resources for these items. Note: be sure you have 15GB available for the container partition. Ubuntu 20.04 comes with the `lxd` snap installed and in it contains an image for `core18`. This requires more than 5GB of partition space when coupled with the `core20` base required by the `snapcraft.yaml`.

This script will create an `lxd` group from which `snapcraft` can use to build the snap. Once this is complete the snap will start building using the `lxd` container. The `--debug` flag will open a shell in the container if a build error occurs.

### Manual reset of LXD container
In the event that during the `snapcraft` build the container errors out with:
```
Launching a container.
Project base changed from None to 'core20', cleaning build instance.
An error occurred with the instance when trying to launch with 'LXD': The requested image couldn't be found.
Ensure that 'LXD' is setup correctly and try again.
```
The container will require a full reset. First shutdown the container
```bash
 $ lxd shutdown
```
Now we need to manually remove the storage pool and the network bridges associated to the original `lxd init`. We do this by detaching the default profile from these resources:
```bash
 $ printf 'config: {}\ndevices: {}' | lxc profile edit default
```
Now we can delete the storage pool and the bridge networks
```bash
 $ lxc storage delete <storage-name>
 $ lxc network delete <bridge-network-name>
```
Verify that no bridge networks or storage pools exist for the `init` to latch onto:
```bash
 $ lxc storage list
+---------+-------------+--------+--------------------------------------------+---------+
|  NAME   | DESCRIPTION | DRIVER |                   SOURCE                   | USED BY |
+---------+-------------+--------+--------------------------------------------+---------+
 $ lxc network list
+--------+----------+---------+-------------+---------+
|  NAME  |   TYPE   | MANAGED | DESCRIPTION | USED BY |
+--------+----------+---------+-------------+---------+
| eth0   | physical | NO      |             | 0       |
+--------+----------+---------+-------------+---------+
| wlan0  | physical | NO      |             | 0       |
+--------+----------+---------+-------------+---------+
```

Rerun the lxd container:
```bash
 $ ./lxd-build.sh
```

## Manual Snap build in LXD container
1. Install snap requirments on host
```bash
 $ sudo snap install lxd
```
Check `lxd` alias points to `/snap/bin/lxd` and not `/usr/bin/lxd`:
```bash
 $ which lxd
/snap/bin/lxd
```
Otherwise migrate the lxd to the snap context:
```bash
 $ lxd.migrate
```
2. Create and initialize container
```bash
sudo lxd init
```
Enter default for all prompts. If storage or network bridges already exist then say no for those prompts.

Create a 20.04 image in container named `u1`
```bash
 $ lxc launch ubuntu:20.04 u1
```
3. Setup build environment
Launch a shell inside newly created image and navigate to `/home/ubuntu/monitor`:`
```bash
 $ lxc exec u1 -- /bin/bash
```
Install all our snap requirments to build
```bash
 root@u1:~$ apt-get install snapd
 ...
 root@u1:~$ snap install core20
 ...
 root@u1:~$ snap install snapcraft --classic
 ...
```
Setup build environment by specifying we are building on the same architecture as the deployment. This will tell `snapcraft` to skip using multipass.
```bash
 root@u1:~$ export=SNAPCRAFT_BUILD_ENVIRONMENT="host"
```

4. Move snapcraft build files into container
Copy `monitor` into the image container by using `lxc-file-push`. Note this may take awhile to copy:
```bash
 root@u1:~$ lxc file push monitor u1/home/ubuntu -r
```
It may be faster to clone directly from our repository which will unfortunately require credentials.

5. Manually build the snap using `--destructive-mode` flag
Navigate to `monitor` and build the manually snap using:
```bash
 root@u1:~$ snapcraft `--destructive-mode`
```

## Building Snap on RPi host (no container)
1. Install and update `snapd` 
```bash
 $ sudo apt get update
 $ sudo apt-get install
```
2. Install `snapcraft`
```bash
 $ sudo snap install snapcraft --classic --channel=candidate
```
> `snapcraft` with a snapcraft build `base: core20` is unable to recognize `python` plugin on stable channel runnning version `3.11`. To alleviate this we are using the candatidate channel running version `4.0.2`:

Verify snapcraft channel and version
```bash
 $ snap info snapcraft
name:      snapcraft
summary:   easily create snaps
publisher: Canonical✓
store-url: https://snapcraft.io/snapcraft
contact:   https://forum.snapcraft.io/c/snapcraft
license:   GPL-3.0
description: |
  Package, distribute, and update any app for Linux and IoT.
  
  Snaps are containerised software packages that are simple to create and install. They auto-update
  and are safe to run. And because they bundle their dependencies, they work on all major Linux
  systems without modification.
commands:
  - snapcraft
snap-id:      vMTKRaLjnOJQetI78HjntT37VuoyssFE
tracking:     latest/candidate
refresh-date: today at 19:42 UTC
channels:
  latest/stable:    3.11  2020-04-08 (4285) 59MB classic
  latest/candidate: 4.0.2 2020-05-16 (4766) 63MB classic
  latest/beta:      ↑                            
  latest/edge:      4.0.3 2020-05-26 (4818) 62MB classic
installed:          4.0.2            (4766) 63MB classic
```
```bash
 $ sudo snap refresh --candidate snapcraft
```
Ensure that `snapcraft` points to the correct executable located under `/snap/bin/snapcraft`
```bash
 $ which snapcraft
 /snap/bin/snapcraft 
```
3. Setup build environment by specifying we are building on the same architecture as the deployment. This will tell `snapcraft` to skip using multipass.
```bash
 $ export SNAPCRAFT_BUILD_ENVIRONMENT="host"
```
4. Build the snap
```bash
 $ snapcraft --debug
```
To retry the snap build process make sure to clean the build:
```bash
 $ snapcraft clean
```

## Publishing Snap

Once the snap is snapped we are ready to publish. First we want to add `review-tools` for enhanced checks during publishing.
```bash
 $ sudo snap install review-tools
```

Login to iris@incuvers.com using credentials and then upload the snap to specified channel
```bash
snapcraft upload --release=<channel_name> <snap-name_revision_architecture.snap>
```
``` bash
snapcraft upload iris-incuvers_1.02_arm64.snap --release edge
```
