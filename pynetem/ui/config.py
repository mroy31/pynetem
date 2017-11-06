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

import configparser
import os


class NetemConfig(object):
    custom_conf = None
    __global_conf = '/etc/pynetem.conf'
    __config = None
    __instance = None

    @classmethod
    def instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        if NetemConfig.__config is None:
            NetemConfig.__config = configparser.SafeConfigParser(interpolation=None)

            default_config_path = os.path.abspath(os.path.dirname(__file__))
            NetemConfig.__config.readfp(open(default_config_path
                                             + '/defaults.conf'))

            conf_files = [NetemConfig.__global_conf]
            if NetemConfig.custom_conf:
                conf_files.append(NetemConfig.custom_conf)
            NetemConfig.__config.read(conf_files)

    def __getattr__(self, name):
        return getattr(NetemConfig.__config, name)

    def set(self, section, variable, value):
        self.__config.set(section, variable, value)

    def getlist(self, section, variable):
        list_items = self.__config.get(section, variable).split(',')
        return [it.strip() for it in list_items]

    def get_bind_addresses(self, service='net'):
        bind_addresses = self.getlist(service, 'bind_addresses')
        if 'all' in bind_addresses:
            return ['']
        else:
            return bind_addresses
