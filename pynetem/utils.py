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
import errno
import subprocess
import shlex
import traceback
import zipfile
from pynetem import NetemError


def daemonize():
    if os.fork():    # launch child and...
        os._exit(0)  # kill off parent
    os.setsid()
    if os.fork():    # launch child and...
        os._exit(0)  # kill off parent again.
    os.umask(0o77)
    null = os.open('/dev/null', os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError as e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)


def test_project(prj_path):
    _, ext = os.path.splitext(prj_path)
    if ext.lower() != ".pnet":
        raise NetemError("Project %s has wrong ext" % prj_path)
    if not os.path.isfile(prj_path):
        raise NetemError("Project %s does not exist" % prj_path)
    if not zipfile.is_zipfile(prj_path):
        raise NetemError("Project %s is not a zip file" % prj_path)


def cmd_run_app(cmd_line):
    args = shlex.split(cmd_line)
    try:
        return subprocess.Popen(args, shell=False, env={"DISPLAY": get_x11_env()})
    except FileNotFoundError as err:
        raise NetemError(str(err))


def cmd_call(cmd_line):
    args = shlex.split(cmd_line)
    return subprocess.run(args).returncode


def cmd_check_output(cmd_line):
    args = shlex.split(cmd_line)
    return subprocess.check_output(args, stderr=subprocess.STDOUT)


def cmd_run_background(cmd_line):
    args = shlex.split(cmd_line)
    return subprocess.Popen(args, close_fds=True)


def get_exc_desc():
    return """
-------------Traceback lines-----------------
%s
---------------------------------------------
""" % traceback.format_exc()


def get_x11_env():
    display = ":0.0"
    if "DISPLAY" in os.environ:
        display = os.environ["DISPLAY"]
    return display
