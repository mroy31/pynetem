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

import subprocess
import shlex
import logging
import traceback
from pynetem import NetemError


def run(cmd_line):
    args = shlex.split(cmd_line)
    try:
        result = subprocess.check_output(args)
    except subprocess.CalledProcessError:
        msg = "Unable to excecute command %s" % (cmd_line,)
        logging.error(msg)
        raise NetemError(msg)

    logging.debug("Execute command -> '%s', result -> '%s'"
                  % (cmd_line, result))
    return result


def run_background(cmd_line):
    args = shlex.split(cmd_line)
    return subprocess.Popen(args, close_fds=True)


def get_exc_desc():
    return """
-------------Traceback lines-----------------
%s
---------------------------------------------
""" % traceback.format_exc()