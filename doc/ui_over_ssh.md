# Pygame UI over ssh

This guide goes over the steps needed to have the graphical data of the UI forwarded directly to a remote computer instead of having it displayd on the physical screen.

Pygame can be controlled using keyboard strokes: `K_LEFT` `K_RIGHT`, and `K_RETURN` to replace the rotary encoder's `clockwise` `counter-clockwise` and `push` actions.

> David says:
>
> Yeah, `up`/`down` would make more sense than `left`/`right`, sue me.

## What it is

Pygame is setup to dump graphical data to a big array that represents pixel values on the display (the `framebuffer`).
We do this in order to have a minimal requirement set for the production image.
We do not want to require the the heavy libraries (and RAM) of a full desktop environment (I.E., X11) on the RPi.

It's possible to tell pygame to use `X11` as the graphical backend, but 1) the pi doesn't have and X11 server and 2) we don't want the pi to use X11 fo production.

However we can instruct all X11 transactions that `pygame` needs to be tunneled (not sure if this is a proper tunnel) through an `ssh` connection. This means, if the connecting client (you on your laptop) has an `X11` service running, it can open a window (in the client) and render the `pygame` data there!

For now this is a development-mode only feature. It can potentially be used to make high quality screenshots of our IRIS's GUI.

## Incremental steps
There are three hurdles that have to be overcome for this to work so it's best to take increment steps.

The first hurdle is getting a simple X11 forwarding over ssh.
After that pygame needs to do it.
Finally we need the root user (because we run our app as root), to be able forward X11 traffic over ssh.

### X-forwarding over ssh

In most cases, we can simply tell ssh to automatically handle x11 using the `-X` flag:

``` bash
ssh -X ubuntu@iris-a7ac.local
```

That should open up your own X11 (I already had `XQuartz` on my macbook---you may need to install that).
To test it, run a simple X11 app on the RPi, like `xeyes`

``` bash
sudo apt install x11-apps
xeyes
```

This may require tinkering with the environmental `$DISPLAY` variable and/or the configuration file `/etc/ssh/sshd_config` (both on the RPi).
Make this this works before the next steps.
#### Troubleshooting
If `$DISPLAY` is empty, make sure you have the `xauth` packages installed.
If `$DISPLAY` is empty, make sure you are ssh'ed in with the `-X` flag and `echo $DISPLAY` from that ssh session.
Edit `/etc/ssh/sshd_config` and make sure you have uncommented `X11Forwarding yes`; `X11DisplayOffset 10`; and `X11UseLocalhost yes`.

### X forwarding as root
Now since our app runs as root (because GPIO), we need to redo the previous test as sudo.
If `xeyes` works, the easiest way is simply to try `sudo xeyes`.
It helps to init the ssh connection with the additional `-v` for more verbose logging.

``` bash
ssh -X -v ubuntu@iris-1f5c.local
```

If you try `sudo xeyes` and get somerthing that looks like `X11 connection rejected because of wrong authentication.
`, you need to look at this SO link: https://unix.stackexchange.com/questions/110558/su-with-error-x11-connection-rejected-because-of-wrong-authentication/118295#118295

``` bash
xauth list | grep unix`echo $DISPLAY | cut -c10-12` > /tmp/xauth
sudo su
xauth add `cat /tmp/xauth`
```
Make this this works before the next steps.

### X11 with Pygame

A simple way to test pygame is by trying to run it.
A simple way to run it is:

```python
import pygame
pygame.display.init()
```
or as a bash one-liner:
``` bash
python3 -c  "import pygame; pygame.display.init()"
```
With verbose ssh output, it'll be obvious if this was successful or not.
To get our app's UI to use X11, you'll need to modify the `SDL_VIDEODRIVER` string. This is done from `context_manager`'s `_set_display_env()` method.

```python
#os.environ["SDL_FBDEV"] = '/dev/fb0'
#os.environ["SDL_VIDEODRIVER"] = 'fbcon'
os.environ['SDL_VIDEO_CENTERED'] = '1'	        os.environ["SDL_VIDEODRIVER"] = 'x11'
os.environ['SDL_NOMOUSE'] = '1'
self._logger.info("Assigned SDL environment variables.")
```
Note that it might be useful to re-enable the mouse `os.environ['SDL_NOMOUSE'] = '0'`