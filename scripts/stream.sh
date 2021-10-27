#!/bin/bash
gst-launch-1.0 tcambin ! video/x-raw, format=GRAY8, width=3872, height=2764, framerate=3/1 ! videoconvert ! videoscale ! video/x-raw, width=640, height=480 ! videoconvert ! fbdevsink
