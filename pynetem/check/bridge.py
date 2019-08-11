# pynetem: network emulator
# Copyright (C) 2015-2019 Mickael Royer <mickael.royer@recherche.enac.fr>
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

from pyroute2 import IPDB
from pynetem.check._base import _BaseCheck


class BridgeCheck(_BaseCheck):

    def get_name(self):
        return "bridge"

    def get_desc(self):
        return "Bridgecheck"

    def check(self, network):
        if "bridges" not in network:
            return False

        for br_name in network["bridges"]:
            bridge = network["bridges"][br_name]
            self.check_args(br_name, bridge, {
                "host_if": {
                    "type": "string",
                    "mandatory": True
                },
            })
            if self.has_errors():
                continue
            host_if = bridge["host_if"]
            with IPDB() as ipdb:
                if host_if not in ipdb.interfaces:
                    self.add_error("%s: host if %s does not exist" %
                                   (br_name, host_if))

        return self.has_errors()
