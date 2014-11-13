# junemule, a network emulator
# Copyright (C) 2012-2013 Mickael Royer <mickael.royer@gmail.com>
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

import SocketServer, subprocess
import logging, shlex

from junemule import JunemuleError
from junemule.ui.config import JunemuleConfig

class JunemuleDaemonHandler(SocketServer.BaseRequestHandler):

    def setup(self):
        SocketServer.BaseRequestHandler.setup(self)

        self.config = JunemuleConfig()

    def handle(self):
        cmd = self.request.recv(1024).strip()
        logging.debug("Receive data: %s" % cmd)

        try:
            if cmd.startswith("tap_create"):
                cmd_split = cmd.split()
                if len(cmd_split) != 3:
                    raise JunemuleError("Wrong tap_create invocation")
                self.create_tap(cmd_split[1], cmd_split[2])
            elif cmd.startswith("tap_delete"):
                cmd_split = cmd.split()
                if len(cmd_split) != 2:
                    raise JunemuleError("Wrong tap_create invocation")
                self.delete_tap(cmd_split[1])
            else:
                raise JunemuleError("Unknown command %s" % cmd)
        except JunemuleError, err:
            self.request.sendall("%s" % err)
        else:
            self.request.sendall("OK")

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
            raise JunemuleError(msg)

# vim: ts=4 sw=4 expandtab
