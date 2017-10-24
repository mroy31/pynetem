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
from pynetem.wrapper.qemu import RouterInstance, HostInstance
from pynetem.wrapper.vde import SwitchInstance


class TopologieManager(object):

    def __init__(self, config, netfile):
        self.config = config
        self.netfile = netfile

        self.routers, self.hosts, self.switches = [], [], []
        try:
            self.__load()
        except NetemError as err:
            self.close()
            logging.error("Unable to load net file %s: %s" % (netfile, err))

    def __load(self):
        logging.debug("Start to load topologie")

        network = ConfigObj(self.netfile)
        autostart = network['config'].as_bool("autostart")

        # load switches
        switches_section = network["switches"]
        for s_name in switches_section:
            logging.debug("Create switch instance %s" % s_name)
            need_tap = switches_section[s_name].as_bool("tap")
            s_inst = SwitchInstance(self.config, s_name, need_tap)
            if autostart:
                logging.debug("Start switch instance %s" % s_name)
                s_inst.start()
            self.switches.append(s_inst)

        image_dir = os.path.join(os.path.dirname(self.netfile),
                                 network["config"]["image_dir"])
        # load routers
        routers_section = network["routers"]
        for r_name in routers_section:
            logging.debug("Create router instance %s" % r_name)
            b_img = routers_section[r_name]["type"]
            img = os.path.join(image_dir, "%s.img" % r_name)
            console = routers_section[r_name].as_int("console")
            r_inst = RouterInstance(self.config, r_name, img, b_img, console)

            # create interfaces
            nb_if = routers_section[r_name].as_int("if_numbers")
            for i in range(nb_if):
                if_name = "if%d" % i
                s_connected = routers_section[r_name][if_name]
                r_inst.add_if(s_connected)

            # start if necessary
            if autostart:
                logging.debug("Start router instance %s" % r_name)
                r_inst.start()
                logging.debug("Router %s is available on telnet port %d"
                              % (r_name, console))
            self.routers.append(r_inst)

        # load hosts
        hosts_section = network["hosts"]
        for h_name in hosts_section:
            logging.debug("Create hosts instance %s" % h_name)
            b_img = hosts_section[h_name]["type"]
            img = os.path.join(image_dir, "%s.img" % h_name)
            console = hosts_section[h_name].as_int("console")
            h_inst = HostInstance(self.config, h_name, img, b_img, console)

            # create interfaces
            nb_if = hosts_section[h_name].as_int("if_numbers")
            for i in range(nb_if):
                if_name = "if%d" % i
                s_connected = hosts_section[h_name][if_name]
                h_inst.add_if(s_connected)

            # start if necessary
            if autostart:
                logging.debug("Start host instance %s" % h_name)
                h_inst.start()
                logging.debug("Host %s is available on telnet port %d"
                              % (h_name, console))
            self.hosts.append(h_inst)

    def get_node(self, instance_name):
        for instance in self.routers + self.hosts:
            if instance.get_name() == instance_name:
                return instance
        return None

    def stop(self, instance_name):
        for instance in self.routers + self.hosts + self.switches:
            if instance.get_name() == instance_name:
                if instance.is_started():
                    instance.stop()

    def start(self, instance_name):
        for instance in self.routers + self.hosts + self.switches:
            if instance.get_name() == instance_name:
                if not instance.is_started():
                    instance.start()

    def stopall(self):
        for instance in self.routers + self.hosts + self.switches:
            instance.stop()

    def startall(self):
        for instance in self.routers + self.hosts + self.switches:
            instance.start()

    def status(self):
        return """
Switches:
\t%s

Routers:
\t%s

Hosts:
\t%s
""" % (
        "\n\t".join(["Switch %s is %s" % (s.get_name(), s.get_status())
                    for s in self.switches]),
        "\n\t".join(["Router %s is %s" % (r.get_name(), r.get_status())
                    for r in self.routers]),
        "\n\t".join(["Host %s is %s" % (h.get_name(), h.get_status())
                    for h in self.hosts])
    )

    def close(self):
        self.stopall()
