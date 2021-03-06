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

import sys
import time
import threading
import itertools
from pynetem.console.color import GREEN, RED, DEFAULT, ORANGE


class Spinner(object):

    def __init__(self, text, delay=0.1, color=DEFAULT):
        self.spinner_generator = itertools.cycle(['-', '/', '|', '\\'])
        self.delay = delay
        self.text = text
        self.color = color
        # start the thread
        self.busy = True
        self.thread = threading.Thread(target=self.spinner_task)
        self.thread.start()

    def is_running(self):
        return self.busy

    def spinner_task(self):
        sys.stdout.write(self.color+self.text+DEFAULT)
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def __stop(self, msg):
        if self.busy:
            self.busy = False
            self.thread.join()
            sys.stdout.write(msg)

    def stop(self):
        self.__stop(GREEN+'OK\n'+DEFAULT)

    def interrupt(self):
        self.__stop(ORANGE+"INTERRUPT\n"+DEFAULT)

    def error(self, err=None):
        msg = "NOK"
        if err is not None:
            msg = msg + "\n\t{}".format(err)
        self.__stop(RED+'{}\n'.format(msg)+DEFAULT)
