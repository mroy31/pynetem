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
import pytest
import docker
from pyroute2 import IPRoute
from pyroute2 import netns
from tests.data import gen_rnd_string
from pynetem import __version__


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
    client = docker.from_env()
    cname = gen_rnd_string(min_size=8, max_size=8)
    image = "mroy31/pynetem-host:{}".format(__version__)

    # check the image exists
    assert client.images.get(image) is not None

    # create container and check its existence
    pynetem_daemon.docker_create(cname, cname, image, "no")
    containers = [c.name for c in client.containers.list(all=True)]
    assert cname in containers

    # start container
    pynetem_daemon.docker_start(cname)
    container = client.containers.get(cname)
    assert container.status == "running"

    # check pid
    pid = pynetem_daemon.docker_pid(cname)
    assert int(pid) == container.attrs["State"]["Pid"]

    # stop container
    pynetem_daemon.docker_stop(cname)
    container.reload()
    assert container.status == "exited"

    # delete container
    pynetem_daemon.docker_rm(cname)
    containers = [c.name for c in client.containers.list(all=True)]
    assert cname not in containers
