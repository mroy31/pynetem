# pynetem: network emulator
# Copyright (C) 2015-2018 Mickael Royer <mickael.royer@recherche.enac.fr>
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

__version__ = "0.14.3"
NETEM_ID = "ntm"


def get_docker_images(cfg):
    return {
        "host": "{}:{}".format(cfg.get("docker", "host_img"), __version__),
        "server": "{}:{}".format(cfg.get("docker", "server_img"), __version__),
        "frr": "{}:{}".format(cfg.get("docker", "frr_img"), __version__),
        "router": "{}:{}".format(cfg.get("docker", "frr_img"), __version__),
    }


class NetemError(Exception):
    pass
