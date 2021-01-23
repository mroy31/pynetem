# pynetem: network emulator
# Copyright (C) 2019 Mickael Royer <mickael.royer@recherche.enac.fr>
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

import pytest
import time
import os
import subprocess
import shlex
import asyncio
from pynetem.server.client import NetemClientProtocol
from pynetem.server.rpc import RPCRequest
from pynetem.daemon.server import NetemDaemonThread
from pynetem.daemon.client import NetemDaemonClient

SERVER_PORT = 10100
NETID = "ntmtt"


@pytest.fixture(scope="module")
def pynetem_daemon():
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


@pytest.fixture(scope="module")
def server_rpc_cmd():
    def send_rpc_cmd(cmd_name, args=[], on_signal=lambda sig: None):
        async def __send_rpc_cmd(cmd_name, args=[]):
            request = RPCRequest(cmd_name, args)
            loop = asyncio.get_running_loop()
            on_answer = loop.create_future()

            transport, _ = await loop.create_connection(
                lambda: NetemClientProtocol(request, on_signal, on_answer),
                "127.0.0.1",
                SERVER_PORT,
            )

            result = await on_answer
            transport.close()

            return result

        return asyncio.run(__send_rpc_cmd(cmd_name, args=args))

    yield send_rpc_cmd


@pytest.fixture(scope="function")
def pynetem_server(server_rpc_cmd):

    def server_factory(prj_path):
        f_path = os.path.dirname(__file__)
        cmd = "{} --conf {} --id {} --port {} {}".format(
            os.path.join(f_path, "..", "pynetem-server"),
            os.path.join(f_path, "conf/tests.conf"),
            NETID, SERVER_PORT, prj_path
        )
        result = subprocess.run(shlex.split(cmd), stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise OSError("Unable to start server: {}".format(result.stderr))

    yield server_factory

    # stop the server with quit command
    server_rpc_cmd("quit")
