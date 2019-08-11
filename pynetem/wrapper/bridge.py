# pynetem: network emulator
# Copyright (C) 2015-2019 Mickael Royer <mickael.royer@recherche.enac.fr>
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


class BridgeInstance(_BaseWrapper):

    def __init__(self, prj_id, name, config):
        super(BridgeInstance, self).__init__(prj_id)

        self.name = name
        self.__is_started = False
        self.__host_interface = config["host_if"]
        self.__br_interfaces = []
        self.__br_name = "%s.%s" % (prj_id, name)

    def get_type(self):
        return "bridge"

    def get_name(self):
        return self.name

    def is_running(self):
        return self.__is_started

    def attach_interface(self, if_name):
        if self.__is_started and if_name not in self.__br_interfaces:
            self.daemon.br_addif(self.__br_name, if_name)
            self.__br_interfaces.append(if_name)

    def detach_interface(self, if_name):
        if self.__is_started and if_name in self.__br_interfaces:
            self.daemon.br_delif(self.__br_name, if_name)
            self.__br_interfaces.remove(if_name)

    def start(self):
        if self.__is_started:
            return

        ret = self.daemon.br_create(self.__br_name)
        if ret == "EXIST":
            logging.warning("The bridge %s already exists." % self.__br_name)

        self.daemon.ifup(self.__host_interface)
        self.daemon.br_addif(self.__br_name, self.__host_interface)
        self.__is_started = True

    def stop(self):
        if self.__is_started:
            for if_name in self.__br_interfaces:
                self.daemon.br_delif(self.__br_name, if_name)
            self.daemon.br_delif(self.__br_name, self.__host_interface)
            self.daemon.br_delete(self.__br_name)
            self.__is_started = False
            self.__br_interfaces = []
