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

import os
import logging
from pynetem.wrapper import _BaseInstance


class VdeSwitchInstance(_BaseInstance):

    def __init__(self, name, sw_config):
        super(VdeSwitchInstance, self).__init__(name)
        need_tap = sw_config.as_bool("tap")
        self.tap_name = None
        if need_tap:
            self.tap_name = "VDE%s" % name

    def is_switch(self):
        return True

    def get_sw_type(self):
        return "vde"

    def get_tap_name(self):
        return self.tap_name

    def build_cmd_line(self):
        cmd_line = "vde_switch -M /tmp/%s.mgnt -x "\
                   "-s /tmp/%s.ctl" % (self.name, self.name)
        if self.tap_name is not None:
            logging.debug("Create tap interface %s" % self.tap_name)
            self._daemon_command("tap_create "
                                 "%s %s" % (self.tap_name,
                                            os.environ["LOGNAME"]))
            cmd_line += " -t %s" % self.tap_name
        return cmd_line

    def stop(self):
        super(VdeSwitchInstance, self).stop()
        if self.tap_name is not None:
            logging.debug("Delete tap interface %s" % self.tap_name)
            self._daemon_command("tap_delete %s" % self.tap_name)
