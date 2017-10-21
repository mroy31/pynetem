# pynetem: network emulator
# Copyright (C) 2015-2017 Mickael Royer <mickael.royer@recherche.enac.fr>
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
import threading
from socketserver import UnixStreamServer, BaseRequestHandler
import subprocess
import logging
import shlex
from pynetem import NetemError
from pynetem.ui.config import NetemConfig


class NetemDaemonHandler(BaseRequestHandler):

    def setup(self):
        BaseRequestHandler.setup(self)
        self.config = NetemConfig()

    def handle(self):
        cmd = self.request.recv(1024).decode("utf-8").strip()
        logging.debug("Receive data: %s" % cmd)

        try:
            if cmd.startswith("tap_create"):
                cmd_split = cmd.split()
                if len(cmd_split) != 3:
                    raise NetemError("Wrong tap_create invocation")
                self.create_tap(cmd_split[1], cmd_split[2])
            elif cmd.startswith("tap_delete"):
                cmd_split = cmd.split()
                if len(cmd_split) != 2:
                    raise NetemError("Wrong tap_create invocation")
                self.delete_tap(cmd_split[1])
            else:
                raise NetemError("Unknown command %s" % cmd)
        except NetemError as err:
            msg = "ERROR: %s" % err
            self.request.sendall(msg.encode("utf-8"))
        else:
            self.request.sendall("OK".encode("utf-8"))

    def create_tap(self, name, user):
        logging.debug("Create tap %s" % name)
        self.__command("tunctl -u %s -t %s" % (user, name))
        self.__command("ifconfig %s up" % (name,))

    def delete_tap(self, name):
        logging.debug("Delete tap %s" % name)
        self.__command("tunctl -d %s" % (name,))

    def __command(self, cmd_line):
        args = shlex.split(cmd_line)
        ret = subprocess.call(args)
        if ret != 0:
            msg = "Unable to excecute command %s" % (cmd_line,)
            logging.error(msg)
            raise NetemError(msg)


class NetemDaemonThread(threading.Thread):

    def __init__(self, socket):
        super(NetemDaemonThread, self).__init__()

        self.__server = None
        self.__socket = socket
        self.running = False

    def run(self):
        self.running = True
        self.__server = UnixStreamServer(self.__socket, NetemDaemonHandler)
        os.chmod(self.__socket, 0o666)

        logging.info("Start pynetem daemon")
        self.__server.serve_forever()

    def stop(self):
        if self.__server is not None:
            logging.info("Stop pynetem daemon")
            self.__server.shutdown()
            self.__server = None
        self.running = False
