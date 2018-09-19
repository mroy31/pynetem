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

import logging
from pynetem import NetemError
from pynetem.wrapper.node.qemu import QEMUInstance
from pynetem.wrapper.node.docker import DOCKER_NODES


def build_node_instance(prj_id, p2p_sw, img_dir, conf_dir, n_name, n_config):
    logging.debug("Create node instance %s" % n_name)
    if "type" in n_config:
        nc_type = n_config["type"].split('.', 1)
        n_type, n_image = "qemu", None
        if len(nc_type) == 1:
            n_image = nc_type[0]
        elif len(nc_type) == 2:
            n_type, n_image = nc_type
        else:
            raise NetemError("type args for node %s has wrong format" % n_name)

        # create instance based on type field
        if n_type == "qemu":
            return QEMUInstance(p2p_sw, img_dir, n_image, n_name, n_config)
        if n_type == "docker":
            try:
                return DOCKER_NODES[n_image](
                    p2p_sw, prj_id,
                    conf_dir, n_name, n_config)
            except KeyError:
                raise NetemError("docker image %s does not exist" % n_image)

    raise NetemError("Type is not specified for %s" % n_name)
