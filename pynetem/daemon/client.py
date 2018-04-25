# pynetem: network emulator
# Copyright (C) 2015-2018 Mickael Royer <mickael.royer@recherche.enac.fr>
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

import re
import socket
import logging
from pynetem import NetemError
from pynetem.daemon.server import CMD_LIST


def build_cmd_func(cmd, nb_args):
    def cmd_func(self, *args):
        logging.debug("Call daemon command: %s -> %s" % (cmd, args))
        if len(args) != nb_args:
            raise NetemError("Wrong number of arguments for cmd %s" % cmd)

        cmd_line = "%s %s" % (cmd, " ".join(args))
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self.socket_path)
        except socket.error as err:
            raise NetemError("Unable to connect to daemon: %s" % err)

        sock.sendall(cmd_line.encode("utf-8"))
        ans = sock.recv(1024).decode("utf-8").strip()
        sock.close()
        if not ans.startswith("OK"):
            raise NetemError("Daemon returns an error: %s" % ans)
        return ans.replace("OK ", "")

    return cmd_func


class NetemDaemonClient(object):
    __instance = None

    @classmethod
    def instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        # define a method for each command
        for cmd in CMD_LIST:
            reg_exp = re.compile(CMD_LIST[cmd])
            cmd_func = build_cmd_func(cmd, reg_exp.groups)
            cmd_func.__name__ = cmd

            setattr(NetemDaemonClient, cmd, cmd_func)

    def set_socket_path(self, s_path):
        self.socket_path = s_path