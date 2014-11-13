# Deejayd, a media player daemon
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

from junemule import JunemuleError

class JunemuleConsole(object):

    def __init__(self, config, manager):
        self.config = config
        self.manager = manager

    def start(self):
        while True:
            command = raw_input("[junemule] --> ").strip()
            if command == "help":
                print """
available commands:
    help: return this help
    status: print router and host state
    stopall: stop all router and host instance
    startall: start all router and host instance
    quit: stop all machines and quit
"""
            elif command == "status":
                print self.manager.status()
            elif command == "stopall":
                self.manager.stopall()
            elif command == "startall":
                self.manager.startall()
            elif command == "quit":
                self.manager.close()
                break
            else:
                print "Unknown command, enter help for more details"


# vim: ts=4 sw=4 expandtab
