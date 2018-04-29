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

from pynetem.daemon.client import NetemDaemonClient
P2P_NAME = "p2p"


class NetemP2PSwitch(object):

    def __init__(self, prj_id):
        self.daemon = NetemDaemonClient.instance()
        self.__sw_name = "{0}.{1}".format(prj_id, P2P_NAME)
        self.__connections = []

        # create switch used for p2p connections
        self.daemon.ovs_create(self.__sw_name)

    def add_connection(self, l_ifname, r_ifname):
        tag = self.get_tag(l_ifname, r_ifname)
        # just connect the left node
        self.daemon.ovs_add_port(self.__sw_name, l_ifname)
        self.daemon.ovs_port_vlan(l_ifname, str(tag))
        # store connection informations
        self.__connections.append({
            "l_ifname": l_ifname,
            "r_ifname": r_ifname,
            "tag": tag
        })

    def delete_connection(self, l_ifname, r_ifname):
        conn = self.get_connection(l_ifname, r_ifname)
        if conn is not None:
            self.daemon.ovs_del_port(self.__sw_name, l_ifname)
            self.__connections.remove(conn)

    def get_tag(self, l_ifname, r_ifname):
        for c in self.__connections:
            if c["l_ifname"] == r_ifname and c["r_ifname"] == l_ifname:
                return c["tag"]
        return 10 + len(self.__connections)

    def get_connection(self, l_ifname, r_ifname):
        for c in self.__connections:
            if c["l_ifname"] == l_ifname and c["r_ifname"] == r_ifname:
                return c
        return None

    def close(self):
        self.daemon.ovs_delete(self.__sw_name)
