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

import logging
from pynetem.wrapper import _BaseWrapper
from pynetem.wrapper.spinner import Spinner


class OVSwitchInstance(_BaseWrapper):

    def __init__(self, prj_id, sw_name, sw_config):
        super(OVSwitchInstance, self).__init__()

        self.name = sw_name
        self.__is_started = False
        self.__sw_interfaces = []
        self.__sw_name = "%s.%s" % (prj_id, sw_name)

    def is_switch(self):
        return True

    def get_sw_type(self):
        return "ovs"

    def get_name(self):
        return self.name

    def attach_interface(self, if_name):
        if self.__is_started and if_name not in self.__sw_interfaces:
            self.daemon.ovs_add_port(self.__sw_name, if_name)
            self.__sw_interfaces.append(if_name)

    def detach_interface(self, if_name):
        if self.__is_started and if_name in self.__sw_interfaces:
            self.daemon.ovs_del_port(self.__sw_name, if_name)
            self.__sw_interfaces.remove(if_name)

    def start(self):
        if self.__is_started:
            return
        spinner = Spinner("Start ovs switch %s ... " % self.name)
        spinner.start()

        ret = self.daemon.ovs_create(self.__sw_name)
        if ret == "EXIST":
            logging.warning("The switch %s already exists." % self.__sw_name)
        self.__is_started = True
        spinner.stop()

    def stop(self):
        if self.__is_started:
            spinner = Spinner("Stop ovs switch %s ... " % self.name)
            spinner.start()

            for if_name in self.__sw_interfaces:
                self.daemon.ovs_del_port(self.__sw_name, if_name)
            self.daemon.ovs_delete(self.__sw_name)
            self.__is_started = False
            self.__sw_interfaces = []
            spinner.stop()
