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

import re
from pynetem.check._base import _BaseCheck

NAME_RE = re.compile("^\w+$")


class CommonCheck(_BaseCheck):

    def get_name(self):
        return "common"

    def get_desc(self):
        return "Global check"

    def check(self, network):
        # check config
        for key in ("image_dir", "config_dir"):
            if key not in network["config"]:
                self.add_error("key %s is mandatory in the config part" % key)

        # check nodes
        for n_name in network["nodes"]:
            if NAME_RE.match(n_name) is None:
                self.add_error("The node name %s is not compliant: it has to "
                               "respect the regexp '^\w+$'" % n_name)
            elif "type" not in network["nodes"][n_name]:
                self.add_error("You do not specify type for node %s" % n_name)
            else:
                n_type = network["nodes"][n_name]["type"]
                if not re.match("^(qemu|docker)\.\S+$", n_type):
                    self.add_error("Node %s has wrong type" % n_name)

        # check switches
        for s_name in network["switches"]:
            if NAME_RE.match(s_name) is None:
                self.add_error("The sw name %s is not compliant: it has to "
                               "respect the regexp '^\w+$'" % s_name)
            elif "type" not in network["switches"][s_name]:
                self.add_error("You do not specify type for "
                               "switch %s" % s_name)
            else:
                s_type = network["switches"][s_name]["type"]
                if s_type not in ("vde", "ovs"):
                    self.add_error("Switch %s has wrong type" % s_name)
