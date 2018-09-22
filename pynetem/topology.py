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
import re
import logging
from configobj import ConfigObj, ConfigObjError
from pynetem import NetemError
from pynetem.check import check_network
from pynetem.wrapper.switch import build_sw_instance
from pynetem.wrapper.node import build_node_instance
from pynetem.wrapper.p2p import NetemP2PSwitch
from pynetem.wrapper.spinner import Spinner


class TopologieManager(object):

    def __init__(self, prj_id, netfile):
        self.prj_id = prj_id
        self.netfile = netfile
        self.p2p_switch = NetemP2PSwitch(prj_id)

        self.saved_state = []
        self.nodes, self.switches = [], []

    def load(self):
        self.__load()

    def check(self):
        try:
            network = ConfigObj(self.netfile)
        except ConfigObjError as err:
            raise NetemError("Syntax error in the network file: %s" % err)
        # check network files before start it
        errors = check_network(network)
        if len(errors) > 0:
            msg = ""
            for e_mod in errors:
                err_msg = "\n\t".join(errors[e_mod]["errors"])
                msg += "%s:\n\t%s\n" % (errors[e_mod]["desc"], err_msg)
            raise NetemError("The network file has errors\n  %s" % msg)

        return network

    def __load_switches(self, sw_section):
        for s_name in sw_section:
            s_inst = build_sw_instance(self.prj_id, s_name, sw_section[s_name])
            s_inst.start()
            self.switches.append(s_inst)

    def __load(self):
        logging.debug("Start to load topology")
        network = self.check()
        # load switches
        if "switches" in network:
            self.__load_switches(network["switches"])

        # first, be sure we can record images and configs
        image_dir = os.path.join(os.path.dirname(self.netfile),
                                 network["config"]["image_dir"])
        config_dir = os.path.join(os.path.dirname(self.netfile),
                                  network["config"]["config_dir"])
        for path in (image_dir, config_dir):
            if not os.path.isdir(path):
                os.mkdir(path)

        if "nodes" in network:
            # load nodes
            nodes_section = network["nodes"]
            for n_name in nodes_section:
                n_inst = build_node_instance(self.prj_id, self.p2p_switch,
                                             image_dir, config_dir, n_name,
                                             nodes_section[n_name])

                self.nodes.append(n_inst)

                # record save_state option
                need_save = True
                if "save_state" in nodes_section[n_name]:
                    need_save = nodes_section[n_name].as_bool("save_state")
                if need_save:
                    self.saved_state.append(n_inst)

            # load nodes connections and start node
            for n_name in nodes_section:
                n_inst = self.get_node(n_name)
                nb_if = nodes_section[n_name].as_int("if_numbers")
                for i in range(nb_if):
                    if_name = "if%d" % i
                    peer_name = nodes_section[n_name][if_name]
                    if peer_name == "__null__":
                        n_inst.add_null_if()
                    elif peer_name.startswith("sw."):
                        (s_name,) = re.match("^sw\.(\w+)$", peer_name).groups()
                        n_inst.add_sw_if(self.get_switch(s_name))
                    else:  # this is a connection to a node
                        p_id, p_if = re.match("^(\w+)\.(\d+)$",
                                              peer_name).groups()
                        n_inst.add_node_if(self.get_node(p_id), p_if)

                self.__start_node(n_inst)
            # load configuration
            for n in (n for n in self.nodes if n.get_type() == "node.junos"):
                self.__load_configuration(n)

    def get_switch(self, sw_name):
        for instance in self.switches:
            if instance.get_name() == sw_name:
                return instance
        return None

    def get_all_switches(self):
        return self.switches

    def get_node(self, name):
        return next((i for i in self.nodes if i.get_name() == name), None)

    def get_all_nodes(self):
        return self.nodes

    def capture(self, if_id):
        node, if_number = self.__get_node_if(if_id)
        node.capture(if_number)

    def set_if_state(self, if_id, state):
        node, if_number = self.__get_node_if(if_id)
        node.set_if_state(if_number, state)

    def stop(self, name):
        node = self.get_node(name)
        if node is not None:
            self.__stop_node(node)

    def start(self, name):
        node = self.get_node(name)
        if node is not None:
            self.__start_node(node)
            if node.get_type() == "node.junos":
                self.__load_configuration(node)

    def stopall(self):
        for n in self.nodes:
            self.__stop_node(n)
        for s in self.switches:
            s.stop()

    def reload(self):
        self.stopall()
        for n in self.nodes:
            n.clean()
        self.nodes, self.switches = [], []
        self.saved_state = []
        self.__load()

    def save(self):
        for n in self.saved_state:
            spinner = Spinner("Save node %s ... " % n.get_name())
            n.save()
            spinner.stop()

    def status(self):
        return """
Status of nodes:
\t%s
""" % ("\n\t".join(["Node %s is %s" % (n.get_name(), n.get_status())
                    for n in self.nodes]))

    def close(self):
        self.stopall()
        for node in self.nodes:
            node.clean()
        self.p2p_switch.close()

    def __start_node(self, node):
        spinner = Spinner("Start node %s ... " % node.get_name())
        node.start()
        spinner.stop()

    def __stop_node(self, node):
        spinner = Spinner("Stop node %s ... " % node.get_name())
        node.stop()
        spinner.stop()

    def __load_configuration(self, node):
        spinner = Spinner("Load configuration for "
                          "node %s ... " % node.get_name())
        node.load_configuration()
        spinner.stop()

    def __get_node_if(self, if_id):
        if_ids = if_id.split(".")
        if len(if_ids) == 2:
            node_id, if_number = if_ids
            node = self.get_node(node_id)
            if node is None:
                raise NetemError("Node %s does not exist" % node_id)
            try:
                if_number = int(if_number)
            except (TypeError, ValueError):
                raise NetemError("%s is not a correct identifier" % if_number)
        else:
            logging.warning("if_name must follow the form <host>.<if_number>")
        return node, if_number
