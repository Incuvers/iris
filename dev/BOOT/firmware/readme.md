# What is in here?

## Ubuntu Server 20.04 DEV: the boot parameters
Here contains the boot option files `cmdline.txt` and friends.
A fresh installation of Ubuntu Server 20.04 (arm64) on a RPi4, should be finalized by copying the files here into the `/boot/firmare/.` directory.

## uboot fix
The motherboard continuously send it's sensorframe to the RPi via a serial connection. Uboot mistakes this for user input (as if a user interfaces over a uart connection) and enters the uboot shell. The Ubuntu installation has a 2-second window of opportunity "Hit any key to stop autoboot" over which the motherboard can actually interfere with the RPi's boot.

Setting `uboot`'s `bootdelay` variable and saving it (using `setenv` and `saveenv`) seems to work with Ubuntu Server.
The created `uboot.env` file reminds uboot to use the `bootdelay` variable, which may be set to -2 (which means to boot without delay and skip the "key-press abort option).
Devs can copy over the `uboot.env` file here, but risk beeing locked out of uboot. One can try to remove the file and hope that there's a hard-coded wait time in the binary. or use the included `uboot.wait.env` that was generated using with a `bootdelay` time of 3 seconds.

Need to test how this can be accomplished in Ubuntu Core, and see if writing to `/boot` is persistent.
