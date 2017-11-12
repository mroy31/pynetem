#!/bin/bash
set -e
source /build/buildconfig
set -x

## install tools
$minimal_apt_get_install curl less nano vim psmisc tcpdump iputils-ping \
iputils-arping iputils-tracepath net-tools file telnet man traceroute hping3 \
iptables links lighttpd htop
