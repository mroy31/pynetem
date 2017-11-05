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
from pynetem.wrapper import _BaseWrapper
from pynetem import NETEM_ID


class OVSwitchInstance(_BaseWrapper):

    def __init__(self, config, sw_name, sw_config):
        super(OVSwitchInstance, self).__init__(config)

        self.name = sw_name
        self.__is_started = False
        self.__sw_interfaces = []
        self.__sw_name = "%s.%s" % (NETEM_ID, sw_name)

    def is_switch(self):
        return True

    def get_sw_type(self):
        return "ovs"

    def get_name(self):
        return self.name

    def attach_interface(self, if_name):
        if self.__is_started and if_name not in self.__sw_interfaces:
            self._daemon_command("ovs_add_port %s "
                                 "%s" % (self.__sw_name, if_name))
            self.__sw_interfaces.append(if_name)

    def detach_interface(self, if_name):
        if self.__is_started and if_name in self.__sw_interfaces:
            self._daemon_command("ovs_del_port %s "
                                 "%s" % (self.__sw_name, if_name))
            self.__sw_interfaces.remove(if_name)

    def add_port_mirroring(self, p_name):
        pass

    def start(self):
        if not self.__is_started:
            logging.debug("Start ovswitch %s" % self.__sw_name)
            self._daemon_command("ovs_create %s" % self.__sw_name)
            self.__is_started = True

    def stop(self):
        if self.__is_started:
            logging.debug("Stop ovswitch %s" % self.__sw_name)
            for if_name in self.__sw_interfaces:
                self._daemon_command("ovs_del_port %s "
                                     "%s" % (self.__sw_name, if_name))
            self._daemon_command("ovs_delete %s" % self.__sw_name)
            self.__is_started = False
            self.__sw_interfaces = []
