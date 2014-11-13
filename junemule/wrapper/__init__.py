# Junemule, a network emulator
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

import os, subprocess, shlex, socket
import logging
from junemule import JunemuleError

class _BaseInstance(object):

    def __init__(self, config, name):
        self.name = name
        self.config = config
        self.process = None

    def get_name(self):
        return self.name

    def stop(self):
        if self.process is not None:
            import signal
            try:
                logging.debug("Killing pid %d" % self.process.pid)
                #os.kill(self.process.pid, signal.SIGTERM)
                self.process.terminate()
                self.process.wait()
            except OSError, e:
                raise JunemuleError("Unable to stop %s" % self.name)
            finally:
                self.process = None

    def is_started(self):
        return self.process is not None

    def get_status(self):
        return self.process is not None and "Started" or "Stopped"

    def _command(self, cmd_line):
        args = shlex.split(cmd_line)
        ret = subprocess.call(args)
        if ret != 0:
            msg = "Unable to excecute command %s" % (cmd_line,)
            logging.error(msg)
            raise JunemuleError(msg)

    def _daemon_command(self, cmd):
        s_name = self.config.get("general", "daemon_socket")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try: sock.connect(s_name)
        except socket.error, err:
            raise JunemuleError("Unable to connect to daemon: %s" % err)

        sock.sendall(cmd)
        ans = sock.recv(1024).strip()
        if ans != "OK":
            raise JunemuleError("Daemon returns an error: %s" % ans)



# vim: ts=4 sw=4 expandtab
