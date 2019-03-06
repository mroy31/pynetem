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
import logging
import time
from pynetem import NetemError
from pynetem.daemon.client import NetemDaemonClient


class _BaseWrapper(object):

    def __init__(self, prj_id):
        self.prj_id = prj_id
        self.daemon = NetemDaemonClient.instance()

    def _command(self, cmd_line, check_output=True, shell=False):
        args = shlex.split(cmd_line)
        try:
            return subprocess.run(
                args, shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as err:
            msg = "%s --> %s" % (err.cmd, err.stderr)
            raise NetemError(msg)
        except FileNotFoundError as err:
            raise NetemError(str(err))

    def get_name(self):
        raise NotImplementedError

    def get_type(self):
        raise NotImplementedError

    def is_running(self):
        raise NotImplementedError

    def gen_ifname(self, if_id, peer, p_if=None):
        name = "{}{}{}.{}".format(
            self.prj_id,
            self.short(self.get_name()),
            if_id, self.short(peer.get_name())
        )
        if p_if is not None:
            name += "{}".format(p_if)
        return name

    def short(self, name):
        if len(name) > 2:
            return name[:2] + name[-1]
        return name

    def clean(self):
        pass


class _BaseInstance(_BaseWrapper):

    def __init__(self, prj_id, name):
        super(_BaseInstance, self).__init__(prj_id)
        self.daemon = NetemDaemonClient.instance()
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
                                        start_new_session=True,
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

    def is_running(self):
        return self.is_started
