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