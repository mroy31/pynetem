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


class NetemConsole(cmd.Cmd):
    intro = 'Welcome to network emulator. Type help or ? to list commands.\n'
    prompt = '[net-emulator] '

    def __init__(self, config, manager):
        super(NetemConsole, self).__init__()
        self.config = config
        self.manager = manager

    def do_quit(self, arg):
        "Quit the network emulator"
        self.manager.close()
        return True

    def do_start(self, arg):
        "Start the nodes and switches"
        self.manager.startall()

    def do_stop(self, arg):
        "Stop the nodes and switches"
        self.manager.stopall()

    def do_status(self, arg):
        "Display routeur/host status"
        print(self.manager.status())
