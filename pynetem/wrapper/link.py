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


class NetemLinkFactory(_BaseWrapper):
    __instance = None

    @classmethod
    def instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        super(NetemLinkFactory, self).__init__()
        self.__links = []
        self.__ns_list = []

    def is_link_exists(self, l_ifname, r_ifname):
        for link in self.__links:
            if link["l_if"] in (l_ifname, r_ifname)\
                    or link["r_if"] in (l_ifname, r_ifname):
                return True
        return False

    def create_link(self, l_ifname, r_ifname, l_ns=None, r_ns=None):
        if self.is_link_exists(l_ifname, r_ifname):
            logging.warning("Links %s-%s already exist" % (l_ifname, r_ifname))
            return
        # create the link
        self._daemon_command("link_create %s %s" % (l_ifname, r_ifname))
        self.__links.append({
            "l_if": l_ifname,
            "l_ns": l_ns,
            "r_if": r_ifname,
            "r_ns": r_ns
        })
        # attach to net namespace
        self.set_ns(l_ifname, l_ns)
        self.set_ns(r_ifname, r_ns)

    def set_ns(self, if_name, netns):
        if netns is not None:
            if netns not in self.__ns_list:
                logging.debug("Create netns %s for node %s" % (netns, if_name))
                self._daemon_command("netns_create %s" % netns)
                self.__ns_list.append(netns)
            self._daemon_command("link_netns %s %s" % (if_name, netns))

    def delete_link(self, l_ifname, r_ifname):
        link = None
        for lk_infos in self.__links:
            if lk_infos["l_if"] in (l_ifname, r_ifname):
                self._daemon_command("link_delete %s" % lk_infos["l_if"])
                self.__links.remove(lk_infos)
                link = lk_infos
                break
        if link is not None:
            for netns in (link["l_ns"], link["r_ns"]):
                if not self.__is_netns_used(netns):
                    self.remove_netns(netns)

    def remove_netns(self, netns):
        if netns in self.__ns_list:
            self._daemon_command("netns_delete %s" % netns)
            self.__ns_list.remove(netns)

    def clear(self):
        for lk_infos in self.__links:
            self._daemon_command("link_delete %s" % lk_infos["l_if"])
        for netns in self.__ns_list:
            self._daemon_command("netns_delete %s" % netns)
        self.__links, self.__ns_list = [], []

    def __is_netns_used(self, netns):
        for lk_infos in self.__links:
            if netns in (lk_infos["l_ns"], lk_infos["r_ns"]):
                return True
        return False
