#!/bin/bash
set -e
source /build/buildconfig
set -x

# install suervisor and ffr packages
$minimal_apt_get_install supervisor frr frr-pythontools frr-snmp

if [ -d "/etc/frr/" ]; then
    cd /etc/frr/
    cp /build/conf/zebra.conf .
    touch ospfd.conf bgpd.conf pimd.conf pbrd.conf ldpd.conf
    chown frr:frr zebra.conf ospfd.conf bgpd.conf pimd.conf pbrd.conf ldpd.conf
fi
mkdir /var/run/frr
chown frr:frr /var/run/frr
# add root to frr group
gpasswd -a root frr

# copy script to load/save config
cp /build/conf/load-frr.sh /usr/local/bin/load-frr.sh
chmod 755 /usr/local/bin/load-frr.sh
cp /build/conf/save-frr.sh /usr/local/bin/save-frr.sh
chmod 755 /usr/local/bin/save-frr.sh