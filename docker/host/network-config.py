#!/usr/bin/python3
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

import sys
import json
import os.path
from optparse import OptionParser
from pyroute2 import IPDB


def load_net_config(f_path):
    with open(f_path) as f_hd:
        net_config = json.load(f_hd)
        with IPDB() as ipdb:
            # configure ip addresses
            for ifname in net_config["interfaces"]:
                if ifname not in ipdb.interfaces:
                    continue
                with ipdb.interfaces[ifname] as i:
                    i.up()
                    for address in net_config["interfaces"][ifname]:
                        i.add_ip(address)
            # configure routes
            for route in net_config["routes"]:
                if route["gateway"] is not None:
                    ipdb.routes.add(route).commit()


def save_net_config(f_path, all_if):
    def format_addr(addr_conf):
        return "%s/%s" % addr_conf

    net_config = {
        "interfaces": {},
        "routes": []
    }
    with IPDB() as ipdb:
        # record ip addresses
        for if_name in ipdb.interfaces:
            if isinstance(if_name, int):
                continue
            if not all_if and not if_name.startswith("eth"):
                continue
            addresses = ipdb.interfaces[if_name]["ipaddr"]
            net_config["interfaces"][if_name] = [format_addr(a) for a in addresses]
        # record route
        net_config["routes"] = [{
            "dst": route["dst"],
            "gateway": route["gateway"],
            "family": route["family"]
        } for route in ipdb.routes]
    
    with open(f_path, "w") as f_hd:
        f_hd.write(json.dumps(net_config))


if __name__ == "__main__":
    usage = "usage: %prog [options] <network file>"
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--save", action="store_true", dest="save",
                      help="save network config")
    parser.add_option("-l", "--load", action="store_true", dest="load",
                      help="load network config")
    parser.add_option("-a", "--all", action="store_true", dest="all",
                      help="save config for all interfaces")
    (options, args) = parser.parse_args()

    if len(args) != 1:
        sys.exit("You have to specify a network file")
    f_path = args[0]
    if options.load:
        if not os.path.isfile(f_path):
            sys.exit("%s file does not exist" % f_path)
        load_net_config(f_path)
    elif options.save:
        save_net_config(f_path, options.all)
