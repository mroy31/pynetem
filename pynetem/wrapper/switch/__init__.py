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
from pynetem.wrapper.switch.vde import VdeSwitchInstance
from pynetem.wrapper.switch.ovs import OVSwitchInstance


SWITCH_CLASSES = {
    "vde": VdeSwitchInstance,
    "ovs": OVSwitchInstance
}


def build_sw_instance(config, sw_name, sw_config):
    logging.debug("Create switch instance %s" % sw_name)
    try:
        sw_type = sw_config["type"]
        s_inst = SWITCH_CLASSES[sw_type](config, sw_name, sw_config)
    except KeyError:
        raise NetemError("Wrong switch type for %s" % sw_name)
    return s_inst
