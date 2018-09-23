#!/bin/bash
set -e
source /build/buildconfig
set -x

## Install Quagga and supervisor
$minimal_apt_get_install gdebi-core supervisor

# install ffr packages
gdebi --non-interactive /build/debs/frr_5.0.1-1.debian9.1_amd64.deb
gdebi --non-interactive /build/debs/frr-pythontools_5.0.1-1.debian9.1_all.deb

if [ -d "/etc/frr/" ]; then
    cd /etc/frr/
    cp /build/conf/zebra.conf .
    touch ospfd.conf bgpd.conf pimd.conf pbrd.conf ldpd.conf
    chown frr:frr zebra.conf ospfd.conf bgpd.conf pimd.conf pbrd.conf ldpd.conf
fi
chown frr:frr /var/run/frr
# add root to quagga group
gpasswd -a root frr

# copy script to load/save config
cp /build/conf/load-frr.sh /usr/local/bin/load-frr.sh
chmod 755 /usr/local/bin/load-frr.sh
cp /build/conf/save-frr.sh /usr/local/bin/save-frr.sh
chmod 755 /usr/local/bin/save-frr.sh
