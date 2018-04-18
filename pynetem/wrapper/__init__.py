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

import threading
import subprocess
import shlex
import socket
import logging
import time
from pynetem import NetemError
from pynetem.ui.config import NetemConfig


class _BaseWrapper(object):

    def _command(self, cmd_line, check_output=True, shell=False):
        args = shlex.split(cmd_line)
        if check_output:
            try:
                result = subprocess.check_output(args, shell=shell)
            except subprocess.CalledProcessError:
                msg = "Unable to execute command %s" % (cmd_line,)
                logging.error(msg)
                raise NetemError(msg)
            return result.decode("utf-8").strip("\n")
        else:
            ret_code = subprocess.call(args, shell=shell)
            if ret_code != 0:
                msg = "Unable to execute command %s" % (cmd_line,)
                logging.error(msg)
                raise NetemError(msg)

    def _daemon_command(self, cmd):
        s_name = NetemConfig.instance().get("general", "daemon_socket")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(s_name)
        except socket.error as err:
            raise NetemError("Unable to connect to daemon: %s" % err)

        sock.sendall(cmd.encode("utf-8"))
        ans = sock.recv(1024).decode("utf-8").strip()
        if not ans.startswith("OK"):
            raise NetemError("Daemon returns an error: %s" % ans)
        return ans.replace("OK ", "")
    
    def is_switch(self):
        return False

    def is_router(self):
        return False

    def is_host(self):
        return False

    def clean(self):
        pass


class _BaseInstance(_BaseWrapper):

    def __init__(self, name):
        self.name = name
        self.process = None

        self.is_started = False
        self.watch_thread = None

    def get_name(self):
        return self.name

    def watch_process(self):
        logging.debug("Start watching process for %s" % self.name)
        while self.is_started:
            time.sleep(0.2)
            r_code = self.process.poll()
            if r_code is not None:
                out, err = self.process.communicate()
                logging.error("ERROR: process %s dies "
                              "unexpectedly" % self.name)
                logging.error(err.decode("utf-8"))
                self.is_started = False
        logging.debug("Stop watching process for %s" % self.name)

    def build_cmd_line(self):
        raise NotImplementedError

    def start(self):
        if self.is_started:
            return

        cmd_line = self.build_cmd_line()
        logging.debug(cmd_line)
        args = shlex.split(cmd_line)
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=False)
        self.is_started = True
        # start thread to monitor process
        self.watch_thread = threading.Thread(target=self.watch_process)
        self.watch_thread.start()

    def stop(self):
        if self.is_started:
            self.is_started = False
            self.watch_thread.join()
            try:
                self.process.terminate()
                self.process.wait()
            except OSError as e:
                raise NetemError("Unable to stop %s -> %s" % (self.name, e))
            finally:
                self.process = None
                self.watch_thread = None

    def get_status(self):
        return self.is_started is not None and "Started" or "Stopped"
