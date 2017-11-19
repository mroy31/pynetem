#!/bin/bash
set -e
source /build/buildconfig
set -x

## Install Quagga and supervisor
$minimal_apt_get_install quagga supervisor
if [ -d "/etc/quagga/" ]; then
    cd /etc/quagga/
    cp /build/conf/zebra.conf .
    touch ospfd.conf bgpd.conf pimd.conf
    chown quagga:quagga zebra.conf ospfd.conf bgpd.conf pimd.conf
fi
# create /var/run/quagga
mkdir /var/run/quagga
chown quagga:quagga /var/run/quagga
# add root to quagga group
gpasswd -a root quagga

# update quagga to 1.2
dpkg -i /build/debs/*deb

# copy script to load/save config
cp /build/conf/load-quagga.sh /usr/local/bin/load-quagga.sh
chmod 755 /usr/local/bin/load-quagga.sh
cp /build/conf/save-quagga.sh /usr/local/bin/save-quagga.sh
chmod 755 /usr/local/bin/save-quagga.sh
