#!/bin/bash
name=60-io.yaml

if [ -f /home/ubuntu/"$name" ]; then
    sudo mv /home/ubuntu/"$name" /etc/netplan/"$name"
else :
    sudo mv /etc/netplan/"$name" /home/ubuntu/"$name"
fi;
sudo netplan apply