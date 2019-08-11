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

import re


class _BaseCheck(object):

    def __init__(self):
        self.__errors = []

    def get_name(self):
        raise NotImplementedError

    def get_desc(self):
        raise NotImplementedError

    def get_errors(self):
        return self.__errors

    def add_error(self, error):
        self.__errors.append(error)

    def has_errors(self):
        return len(self.__errors) > 0

    def check(self, network):
        raise NotImplementedError

    def check_connections(self, network, n_name, node):
        if_numbers = node.as_int("if_numbers")
        for if_id in range(if_numbers):
            if_name = "if%s" % if_id
            if if_name not in node:
                self.add_error("%s: %s is not present" % (n_name, if_name))
                continue

            peer_id = node[if_name]
            if peer_id != "__null__":
                if re.match("^sw\.\w+$", peer_id) is not None:
                    (sw_id,) = re.match("^sw\.(\w+)$", peer_id).groups()
                    if sw_id not in network["switches"]:
                        self.add_error("%s: switch %s does not "
                                       "exist" % (n_name, sw_id))

                    elif node["type"].startswith("docker."):
                        # only ovs switch is supported
                        sw = network["switches"][sw_id]
                        if sw["type"] != "ovs":
                            self.add_error("%s:%s -> docker node can only "
                                           "connect with ovs "
                                           "switch" % (n_name, if_name))

                elif re.match("^br\.\w+$", peer_id) is not None:
                    (br_id,) = re.match("^br\.(\w+)$", peer_id).groups()
                    if br_id not in network["bridges"]:
                        self.add_error("%s: bridge %s does not "
                                       "exist" % (n_name, br_id))

                elif re.match("^\w+\.\d+$", peer_id) is not None:
                    n_id, if_num = re.match("^(\w+)\.(\d+)$", peer_id).groups()
                    if n_id not in network["nodes"]:
                        self.add_error("%s: peer node %s does not "
                                       "exist" % (n_name, n_id))

                    else:
                        peer_if = "if%s" % if_num
                        if peer_if not in network["nodes"][n_id]:
                            self.add_error("%s: peer node %s does not have "
                                           "the target "
                                           "interface" % (n_name, n_id))
                            continue
                        peer_if_conf = network["nodes"][n_id][peer_if]
                        if peer_if_conf != "%s.%d" % (n_name, if_id):
                            self.add_error("%s: peer node %s does not have "
                                           "the right config for the target "
                                           "interface" % (n_name, n_id))
                else:
                    self.add_error("%s: the interface %d is not well "
                                   "configured," " it must be __null__, "
                                   "sw.<sw_name>, br.<br_name> or "
                                   "<node_id>.<if_number>" % (n_name, if_id))

    def check_args(self, name, node, args_dict):
        for key in args_dict:
            if key not in node and args_dict[key]["mandatory"]:
                self.add_error("%s: key %s is mandatory" % (name, key))
            elif key in node:
                val = node[key]
                a_type = args_dict[key]["type"]
                if a_type == "int":
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        self.add_error("%s: arg %s is not an "
                                       "integer" % (name, key))
