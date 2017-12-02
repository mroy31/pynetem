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

import os.path
from pynetem.ui.config import NetemConfig
from pynetem.check._base import _BaseCheck


class QemuNodeCheck(_BaseCheck):

    def get_name(self):
        return "qemu"

    def get_desc(self):
        return "Qemu node check"

    def check(self, network):
        console_numbers = []

        for name in network["nodes"]:
            node = network["nodes"][name]
            if node["type"].startswith("qemu."):
                self.__check_image(node["type"])
                self.__check_node_args(name, node)
                if self.has_errors():
                    continue
                # check unicity of console number
                if node["console"] in console_numbers:
                    self.add_error("%s: Console number %s is "
                                   "already used." % (name, node["console"]))
                else:
                    console_numbers.append(node["console"])
                self.check_connections(network, name, node)
        return self.has_errors()

    def __check_image(self, node_type):
        null, image = node_type.split(".")
        img_folder = NetemConfig.instance().get("general", "image_dir")
        img_path = os.path.join(img_folder, "%s.img" % image)
        if not os.path.isfile(img_path):
            self.add_error("image %s does not exist in images dir" % image)

    def __check_node_args(self, name, node):
        self.check_args(name, node, {
            "console": {"type": "int", "mandatory": True},
            "if_numbers": {"type": "int", "mandatory": True},
            "memory": {"type": "int", "mandatory": False},
        })
        return self.has_errors()
    