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

from pynetem.check._base import _BaseCheck


class DockerNodeCheck(_BaseCheck):

    def get_name(self):
        return "docker"

    def get_desc(self):
        return "Docker node check"

    def check(self, network):
        for name in network["nodes"]:
            node = network["nodes"][name]
            if node["type"].startswith("docker."):
                self.__check_image(name, node["type"])
                self.__check_node_args(name, node)
                if self.has_errors():
                    continue
                self.check_connections(network, name, node)
        return self.has_errors()

    def __check_image(self, name, node_type):
        null, image = node_type.split(".")
        if image not in ("host", "xorp", "quagga"):
            self.add_error("%s: image %s is not valid" % (name, image))

    def __check_node_args(self, name, node):
        self.check_args(name, node, {
            "if_numbers": {"type": "int", "mandatory": True},
        })
        return self.has_errors()
