# Arduino Flash Service
Updated: 2020-11

- [Arduino Flash Service](#arduino-flash-service)
  - [Package Contents](#package-contents)
  - [Setup](#setup)
  - [ICB Submodule for Cross Repository Firmware Version Control](#icb-submodule-for-cross-repository-firmware-version-control)
  - [Submodules](#submodules)
    - [Cloning](#cloning)
    - [Pulling in Submodule Upstream Changes](#pulling-in-submodule-upstream-changes)
  - [Manual Flash Services](#manual-flash-services)

## Package Contents
1. `build/` directory
2. `icb/` submodule
3. `flash_service.py` flash script

The `HardwareInitTool.ino.hex` configures the hardware memory space and preps the system to be written by the firmware update. Therefore the hardware init tool must be flashed to the arduino before the firmware is. `Incuvers_Incubator.ino.hex` is the hex file containing our current version firmware. Finally, the `flash_service.py` module simply automates the flashing process. It can be executed as a python script and flashes the `HardwareInitTool.ino.hex` (for board initialization) followed by `Incuvers_Incubator.ino.hex`.

## Setup
The `build/` directory tracks the build artefacts from latest/master in the `Incuvers/icb` repository. Therefore the flash_service should reference this build directory for all the latest firmware changes.

## ICB Submodule for Cross Repository Firmware Version Control
## Submodules
The build artefacts for the ICB motherboard are contained and referenced within `Incuvers/monitor` as a git submodule combined with a symlink. This is a sub repository within the `Incuvers/monitor` repository but still maintains its reference pointers to its parent repository `Incuvers/monitor`. The submodule and its parent can diverge so in order to ensure that your runtime has the latest changes from the `iris` repository you will have to perform a git fetch

### Cloning
Once you have cloned `Incuvers/monitor` the `icb` submodule will be empty. You must first initialize and make an explicit request to update the submodule in order to clone its contents:
```bash
git submodule init
git submodule update
```
Alternatively when you clone `monitor` you can pass in a flag to tell git to recursively init and update all embedded submodules:
```bash
git clone https://github.com/Incuvers/monitor --recurse-submodules
```
### Pulling in Submodule Upstream Changes
To see the diffs in the local and upstream submodule run:
```bash
git diff submodule
```

To update, navigate to the submodule directory and perform normal git fetch and merge operations:
```bash
git fetch
git merge origin/master
```

Alternatively you can let git automate the fetch and merge process with:
```bash
git submodule update --remote
```

## Manual Flash Services
The command to flash and `.hex` to the IRIS motherboard is given below:
```bash
avrdude -v -p atmega2560 -cwiring -P /dev/ttyX -b 115200 -D -U flash:w:{.hex file}:i
```
Notably, we do not use the `avrdude.conf` instead we rely on the global config discovered within the file system. 


## Robot Integration tests
When we want to verify the state or do a quick sanity check in context of the proper functioning of the Arduino motherboard we may look to this directory
monitor/monitor/tests/integration_tests/arduino_communication
 contained inside this directory there is another readme which explains how to use this service in context of debugging and verifying the working order of the Arduino and raspberry pi communication exchange.