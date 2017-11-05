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
import logging
from configobj import ConfigObj
from pynetem import NetemError
from pynetem.wrapper.switch import build_sw_instance
from pynetem.wrapper.node.qemu import QEMUInstance


class TopologieManager(object):

    def __init__(self, config, netfile):
        self.config = config
        self.netfile = netfile

        self.nodes, self.switches = [], []
        try:
            self.__load()
        except NetemError as err:
            self.close()
            logging.error("Unable to load net file %s: %s" % (netfile, err))

    def __load_switches(self, sw_section):
        for s_name in sw_section:
            s_inst = build_sw_instance(self.config, s_name, sw_section[s_name])
            s_inst.start()
            self.switches.append(s_inst)

    def __load(self):
        logging.debug("Start to load topology")
        network = ConfigObj(self.netfile)

        # load switches
        if "switches" in network:
            self.__load_switches(network["switches"])
        else:
            logging.warning("WARNING: No switches section")

        # first, be sure we can record images
        image_dir = os.path.join(os.path.dirname(self.netfile),
                                 network["config"]["image_dir"])
        if not os.path.isdir(image_dir):
            os.mkdir(image_dir)
        # load nodes
        if "nodes" in network:
            nodes_section = network["nodes"]
            for n_name in nodes_section:
                logging.debug("Create node instance %s" % n_name)
                n_inst = QEMUInstance(self.config, image_dir, n_name,
                                      nodes_section[n_name])

                # create interfaces
                nb_if = nodes_section[n_name].as_int("if_numbers")
                for i in range(nb_if):
                    if_name = "if%d" % i
                    s_name = nodes_section[n_name][if_name]
                    logging.debug("Attach switch %s to %s" % (s_name, n_name))
                    n_inst.add_sw_if(self.get_switch(s_name))

                n_inst.start()
                self.nodes.append(n_inst)

    def get_switch(self, sw_name):
        for instance in self.switches:
            if instance.get_name() == sw_name:
                return instance
        return None

    def get_all_switches(self):
        return self.switches

    def get_node(self, instance_name):
        for instance in self.nodes:
            if instance.get_name() == instance_name:
                return instance
        return None

    def get_all_nodes(self):
        return self.nodes

    def stop(self, instance_name):
        for instance in self.nodes:
            if instance.get_name() == instance_name:
                if instance.is_started():
                    instance.stop()

    def start(self, instance_name):
        for instance in self.nodes:
            if instance.get_name() == instance_name:
                if not instance.is_started():
                    instance.start()

    def stopall(self):
        for instance in self.nodes + self.switches:
            instance.stop()

    def startall(self):
        for instance in self.nodes + self.switches:
            instance.start()

    def reload(self):
        self.stopall()
        self.nodes, self.switches = [], []
        self.__load()

    def status(self):
        return """
Switches:
\t%s

Nodes:
\t%s
""" % (
        "\n\t".join(["Switch %s is %s" % (s.get_name(), s.get_status())
                    for s in self.switches]),
        "\n\t".join(["Node %s is %s" % (n.get_name(), n.get_status())
                    for n in self.nodes])
    )

    def close(self):
        self.stopall()
