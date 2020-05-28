# pynetem: network emulator
# Copyright (C) 2015-2020 Mickael Royer <mickael.royer@recherche.enac.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import os
import time
import pytest
from pyroute2 import IPRoute
from pyroute2 import netns
from tests.data import gen_rnd_string


class IPRouteUtilities(object):

    def __init__(self):
        self.ip = IPRoute()

    def close(self):
        self.ip.close()

    def get_if(self, if_name):
        for link in self.ip.get_links():
            for (attr, value) in link['attrs']:
                if attr == 'IFLA_IFNAME' and value == if_name:
                    return link

        return None

    def is_if_exists(self, if_name):
        for link in self.ip.get_links():
            for (attr, value) in link['attrs']:
                if attr == 'IFLA_IFNAME' and value == if_name:
                    return True

        return False

    def is_ns_exists(self, ns_name):
        return ns_name in netns.listnetns()


@pytest.fixture(scope="module")
def iproute():
    ipr = IPRouteUtilities()
    yield ipr
    ipr.close()


@pytest.fixture(scope="module")
def pynetem_daemon():
    from pynetem.daemon.server import NetemDaemonThread
    from pynetem.daemon.client import NetemDaemonClient

    socket = os.path.join("/tmp", "ntmtest-daemon.ctl")
    # start server thread
    server_thread = NetemDaemonThread(socket)
    server_thread.start()
    # init client to send commands to daemon
    client = NetemDaemonClient.instance()
    client.set_socket_path(socket)
    yield client

    # stop daemon
    time.sleep(0.1)
    server_thread.stop()
    server_thread.join()

    # Make sure the socket does not already exist
    if os.path.exists(socket):
        os.unlink(socket)


def test_version(pynetem_daemon):
    from pynetem import __version__
    version = pynetem_daemon.version()
    assert version == __version__


def test_tuntap(pynetem_daemon, iproute):
    current_user = os.environ["LOGNAME"]
    tap_name = gen_rnd_string(min_size=4, max_size=4)

    pynetem_daemon.tap_create(tap_name, current_user)
    assert iproute.is_if_exists(tap_name)

    pynetem_daemon.tap_delete(tap_name)
    assert not iproute.is_if_exists(tap_name)


def test_netns(pynetem_daemon, iproute):
    ns_name = gen_rnd_string(min_size=4, max_size=4)
    pynetem_daemon.netns_create(ns_name)
    assert iproute.is_ns_exists(ns_name)

    pynetem_daemon.netns_delete(ns_name)
    assert not iproute.is_ns_exists(ns_name)


def test_bridge(pynetem_daemon, iproute):
    br_name = gen_rnd_string(min_size=4, max_size=4)
    pynetem_daemon.br_create(br_name)
    assert iproute.is_if_exists(br_name)
    br = iproute.get_if(br_name)
    assert br["state"] == "up"

    pynetem_daemon.br_delete(br_name)
    assert not iproute.is_if_exists(br_name)


def test_docker(pynetem_daemon):
    pass
