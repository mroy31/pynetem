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

from pynetem import get_docker_images
from pynetem.ui.config import NetemConfig
from pynetem.check._base import _BaseCheck

DOCKER_IMAGES = get_docker_images(NetemConfig.instance())


class DockerNodeCheck(_BaseCheck):

    def get_name(self):
        return "docker"

    def get_desc(self):
        return "Docker node check"

    def check(self, network):
        for name in network["nodes"]:
            node = network["nodes"][name]
            if node["type"].startswith("docker."):
                self.__check_type(name, node["type"])
                self.__check_node_args(name, node)
                if self.has_errors():
                    continue
                self.__check_docker_img(name, node)
                self.check_connections(network, name, node)
        return self.has_errors()

    def __check_type(self, name, node_type):
        _, n_type = node_type.split(".", 1)
        if n_type not in ("host", "frr", 'server', 'router'):
            self.add_error("%s: docker type %s is not valid" % (name, n_type))

    def __check_node_args(self, name, node):
        self.check_args(name, node, {
            "if_numbers": {"type": "int", "mandatory": True},
            "ipv6": {"type": "bool", "mandatory": False},
        })
        _, n_type = node["type"].split(".", 1)
        if n_type in ("frr", "router"):
            self.check_args(name, node, {
                "mpls": {"type": "bool", "mandatory": False},
                "vrrps": {
                    "type": "re",
                    "pattern": "^(eth[0-9]\|\d+\|\d+\.\d+\.\d+\.\d+\/\d+)(;eth[0-9]\|\d+\|\d+\.\d+\.\d+\.\d+\/\d+)*$",
                    "mandatory": False
                },
                "vrfs": {
                    "type": "re",
                    "pattern": "^(\w+)(;\w+)*$",
                    "mandatory": False
                },
            })
        return self.has_errors()

    def __check_docker_img(self, name, node):
        null, n_type = node["type"].split(".", 1)
        img = "image" in node and node["image"] or DOCKER_IMAGES[n_type]
        if self.daemon.docker_image_present(img) == "no":
            self.add_error(
                "{}: docker image {} has not been found. Are you run "
                "'pynetem-emulator --pull' ?".format(name, img))
        return self.has_errors()
