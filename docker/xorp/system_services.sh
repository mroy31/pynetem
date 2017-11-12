#!/bin/bash
set -e
source /build/buildconfig
set -x

## Install init process.
cp /build/iinit.sh /usr/bin/
chmod +x /usr/bin/iinit.sh

## install xorp
$minimal_apt_get_install xorp

# enable launch script
sed -i -e 's/RUN="no"/RUN="yes"/g' /etc/default/xorp
# set default_config
cp /build/default_config.boot /etc/xorp/config.boot
# add root to xorp group
gpasswd -a root xorp

