# pynetem: network emulator
# Copyright (C) 2021 Mickael Royer <mickael.royer@recherche.enac.fr>
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


def get_project(name):
    dir_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(dir_path, "projects", name)


def test_project_open(pynetem_server, server_rpc_cmd):
    pynetem_server(get_project("simple.pnet"))

    answer = server_rpc_cmd("projectPath")
    assert answer["state"] == "OK"
    assert os.path.basename(answer["content"]) == "simple.pnet"
