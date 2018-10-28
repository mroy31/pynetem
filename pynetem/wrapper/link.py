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
        super(NetemLinkFactory, self).__init__(None)
        self.__links = []
        self.__ns_list = []

    def create(self, ifname, ns):
        if self.__is_exists(ifname):
            logging.warning("Links %s already exist" % ifname)
            return
        # create the link
        p_ifname = self.__peer_ifname(ifname)
        self.daemon.link_create(ifname, self.__peer_ifname(ifname))
        self.__links.append({"ifname": ifname, "ns": ns})
        # attach to net namespace
        self.set_ns(p_ifname, ns)

        return self.__peer_ifname(ifname)

    def set_ns(self, ifname, netns):
        if netns not in self.__ns_list:
            logging.debug("Create netns %s for node %s" % (netns, ifname))
            self.daemon.netns_create(netns)
            self.__ns_list.append(netns)
        self.daemon.link_netns(ifname, netns)

    def delete(self, ifname):
        link = None
        for lk_infos in self.__links:
            if lk_infos["ifname"] == ifname:
                self.daemon.link_delete(lk_infos["ifname"])
                self.__links.remove(lk_infos)
                link = lk_infos
                break
        if link is not None:
            if not self.__is_netns_used(link["ns"]):
                self.remove_netns(link["ns"])

    def remove_netns(self, netns):
        if netns in self.__ns_list:
            self.daemon.netns_delete(netns)
            self.__ns_list.remove(netns)

    def clear(self):
        for lk_infos in self.__links:
            self.daemon.link_delete(lk_infos["l_if"])
        for netns in self.__ns_list:
            self.daemon.netns_delete(netns)
        self.__links, self.__ns_list = [], []

    def __is_exists(self, ifname):
        for link in self.__links:
            if link["ifname"] == ifname:
                return True
        return False

    def __peer_ifname(self, ifname):
        return "{0}.int0".format(ifname.split(".", 1)[0])

    def __is_netns_used(self, netns):
        for lk_infos in self.__links:
            if netns == lk_infos["ns"]:
                return True
        return False
