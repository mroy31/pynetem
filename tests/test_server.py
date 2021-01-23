# pynetem: network emulator
# Copyright (C) 2021 Mickael Royer <mickael.royer@recherche.enac.fr>
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
import docker
from tests.conftest import NETID


def get_project(name):
    dir_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(dir_path, "projects", name)


def test_open(pynetem_server, server_rpc_cmd):
    pynetem_server(get_project("simple.pnet"))

    answer = server_rpc_cmd("projectPath")
    assert answer["state"] == "OK"
    assert os.path.basename(answer["content"]) == "simple.pnet"


def test_status(pynetem_server, server_rpc_cmd):
    def check_status(running=False):
        answer = server_rpc_cmd("status")
        assert answer["state"] == "OK"

        prj = answer["content"]["project"]
        assert os.path.basename(prj["path"]) == "simple.pnet"
        assert prj["running"] == running

    pynetem_server(get_project("simple.pnet"))
    check_status(running=False)

    # start the topology
    answer = server_rpc_cmd("load")
    assert answer["state"] == "OK"
    check_status(running=True)


def test_valid_check(pynetem_server, server_rpc_cmd):
    pynetem_server(get_project("simple.pnet"))

    answer = server_rpc_cmd("check")
    assert answer["state"] == "OK"
    assert answer["content"]


def test_invalid_check(pynetem_server, server_rpc_cmd):
    pynetem_server(get_project("invalid.pnet"))

    answer = server_rpc_cmd("check")
    assert answer["state"] == "error"


def test_stop_start(pynetem_server, server_rpc_cmd):
    pynetem_server(get_project("simple.pnet"))

    server_rpc_cmd("load")
    answer = server_rpc_cmd("status")
    assert answer["state"] == "OK"

    prj = answer["content"]["project"]
    assert os.path.basename(prj["path"]) == "simple.pnet"
    assert prj["running"]

    c_name = "{}.R1".format(NETID)
    client = docker.from_env()
    # check the existence of docker container
    containers = [c.name for c in client.containers.list(all=True)]
    assert c_name in containers
    container = client.containers.get(c_name)
    assert container.status == "running"

    # stop R1 node
    answer = server_rpc_cmd("stop", args=["R1"])
    assert answer["state"] == "OK"
    container.reload()
    assert container.status == "exited"

    # start R1 node
    answer = server_rpc_cmd("start", args=["R1"])
    assert answer["state"] == "OK"
    container.reload()
    assert container.status == "running"


def test_topo_file(pynetem_server, server_rpc_cmd):
    pynetem_server(get_project("simple.pnet"))
    answer = server_rpc_cmd("topologyFile")
    assert answer["state"] == "OK"
    assert os.path.isfile(answer["content"])
