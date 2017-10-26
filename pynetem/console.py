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

import cmd
from pynetem import NetemError
from pynetem.project import NetemProject


def require_project(func):

    def cmd_func(self, *args, **kwargs):
        if self.current_project is None:
            print("ERROR: no project has been loaded")
            return
        try:
            return func(self, *args, **kwargs)
        except NetemError as err:
            print("ERROR: %s" % err)
    cmd_func.__name__ = func.__name__

    return cmd_func


class NetemConsole(cmd.Cmd):
    intro = 'Welcome to network emulator. Type help or ? to list commands.\n'
    prompt = '[net-emulator] '

    def __init__(self, config, project=None):
        super(NetemConsole, self).__init__()
        self.config = config
        self.current_project = project

    def do_quit(self, arg):
        "Quit the network emulator"
        if self.current_project is not None:
            self.current_project.close()
        return True

    def do_load(self, prj_path):
        """Load a qnet project"""
        if self.current_project is not None:
            self.current_project.close()
        try:
            self.current_project = NetemProject.load(self.config, prj_path)
        except NetemError as err:
            print("ERROR: %s" % err)

    def do_create(self, prj_path):
        """Create a qnet project"""
        if self.current_project is not None:
            self.current_project.close()
        try:
            self.current_project = NetemProject.create(self.config, prj_path)
        except NetemError as err:
            print("ERROR: %s" % err)

    @require_project
    def do_save(self, arg):
        """Save the project"""
        self.current_project.save()

    @require_project
    def do_reload(self, arg):
        """Reload the project"""
        self.current_project.topology.reload()

    @require_project
    def do_edit(self, arg):
        "Edit the topology"""
        self.current_project.edit_topology()

    @require_project
    def do_start(self, arg):
        "Start the nodes and switches"
        self.current_project.topology.startall()

    @require_project
    def do_stop(self, arg):
        "Stop the nodes and switches"
        self.current_project.topology.stopall()

    @require_project
    def do_status(self, arg):
        "Display routeur/host status"
        print(self.current_project.topology.status())

    @require_project
    def do_console(self, arg):
        "open a console for the given router/host"
        node = self.current_project.topology.get_node(arg)
        if node is None:
            print("Error: node %s not found in the network" % arg)
            return
        node.open_shell()
