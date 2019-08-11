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

from pynetem.check.common import CommonCheck
from pynetem.check.qemu import QemuNodeCheck
from pynetem.check.docker import DockerNodeCheck
from pynetem.check.junos import JunosNodeCheck
from pynetem.check.bridge import BridgeCheck


def check_network(network):
    errors = {}

    for check_module in (
            CommonCheck,
            BridgeCheck,
            QemuNodeCheck,
            DockerNodeCheck,
            JunosNodeCheck):
        mod = check_module()
        mod.check(network)
        if mod.has_errors():
            errors[mod.get_name()] = {
                "desc": mod.get_desc(),
                "errors": mod.get_errors()
            }

    return errors
