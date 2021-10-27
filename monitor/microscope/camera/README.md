Imaging with TIS
================

Requirements
------------

install this
`sudo apt-get install python-gtk2`
`sudo apt-get install python-gst0.10`

Camera Support
--------------
The Imaging Source (TIS) cameras are being tested.

USB2 cameras need a firmware update (see wiki form TIS)

https://github.com/TheImagingSource/tiscamera.git


Modes
-----

`streaming`

We need a low-latency streaming mode for sampled placement. The data is sent directly to the HDMI port. A minimum framerate of 7/1 (images per second) is needed until. In this mode, it is ok to sacrifice image quality for low-latency. Any latency over 1 second is unacceptable. Ideally, the full field of view can be shown.


`capture` The full field of view, highest quality image. Latency or framerate is not an issue since we will be capturing stills.

The capture can be triggered by software or hardware. We will choose the latter since it will be easier to syncronize.

Illumination syncronization for captures
----------------------------------------
The cameras we opted to use have a hardware trigger option.
There is a handy
[TIS whitepaper on trigger](https://s1-dl.theimagingsource.com/api/2.5/packages/publications/whitepapers-cameras/wp224272trigo/330c61fe-3e7f-5975-93de-563372ed59ed/wp224272trigo_1.6.en_US.pdf) that describes its use.

There are two ways to sync illumination with capture: i) send a signal to the illuminator when the camera shutter is open or ii) send a signal to open the shutter when the illumination is triggered. Since we will choose to take four back-to-back images with different illuminations, we will choose the second syncronization option.
