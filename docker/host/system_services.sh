#!/bin/bash
set -e
source /build/buildconfig
set -x

## Install init process.
cp /build/iinit.sh /usr/bin/
chmod +x /usr/bin/iinit.sh

## Install network conf script
$minimal_apt_get_install python3 python3-pyroute2
cp /build/network-config.py /usr/bin/
chmod +x /usr/bin/network-config.py

## install multicast programs
$minimal_apt_get_install build-essential
gcc -o /tmp/mult_receive /build/programs/mult_receive.c
gcc -o /tmp/mult_send /build/programs/mult_send.c
mv /tmp/mult_receive /usr/bin/
mv /tmp/mult_send /usr/bin/