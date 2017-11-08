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
import threading
from socketserver import UnixStreamServer, BaseRequestHandler
import subprocess
import logging
import shlex
from pynetem import NetemError
from pynetem.ui.config import NetemConfig


class NetemDaemonHandler(BaseRequestHandler):

    def setup(self):
        BaseRequestHandler.setup(self)
        self.config = NetemConfig()
        self.__cmd_list = {
            "tap_create": {"args": 2},
            "tap_delete": {"args": 1},
            "netns_create": {"args": 1},
            "netns_delete": {"args": 1},
            "link_create": {"args": 2},
            "link_delete": {"args": 1},
            "link_netns": {"args": 2},
            "link_set_vtap": {"args": 2},
            "ovs_create": {"args": 1},
            "ovs_delete": {"args": 1},
            "ovs_add_port": {"args": 2},
            "ovs_add_mirror_port": {"args": 2},
            "ovs_del_port": {"args": 2},
        }

    def handle(self):
        cmd = self.request.recv(1024).decode("utf-8").strip()
        logging.debug("Receive data: %s" % cmd)

        try:
            cmd_args = cmd.split()
            if cmd_args[0] not in self.__cmd_list:
                raise NetemError("Unknown command %s" % cmd)
            cmd_infos = self.__cmd_list[cmd_args[0]]
            # verify argument number
            if len(cmd_args[1:]) != cmd_infos["args"]:
                raise NetemError("Wrong number of args for "
                                 "command %s" % cmd_args[0])
            # execute command
            getattr(self, cmd_args[0])(*cmd_args[1:])
        except NetemError as err:
            msg = "ERROR: %s" % err
            self.request.sendall(msg.encode("utf-8"))
        else:
            self.request.sendall("OK".encode("utf-8"))

    def tap_create(self, name, user):
        logging.debug("Create tap %s" % name)
        self.__command("tunctl -u %s -t %s" % (user, name))
        self.__command("ip link set %s up" % (name,))

    def tap_delete(self, name):
        logging.debug("Delete tap %s" % name)
        self.__command("tunctl -d %s" % (name,))

    def netns_create(self, name):
        logging.debug("Create netns %s" % name)
        is_pid = False
        try:
            int(name)
        except ValueError:
            pass
        else:
            is_pid = True

        if not is_pid:
            self.__command("ip netns add %s" % name)
        else:
            self.__command("ln -s /proc/%s/ns/net /var/run/netns/%s"
                           % (self.name, self.name))

    def netns_delete(self, name):
        logging.debug("Delete netns %s" % name)
        self.__command("ip netns del %s" % name)

    def link_create(self, if1, if2):
        logging.debug("Create link %s<-->%s" % (if1, if2))
        self.__command("ip link add %s type veth peer name %s" % (if1, if2))

    def link_delete(self, if_name):
        logging.debug("Delete link %s" % if_name)
        self.__command("ip link del %s" % if_name)

    def link_netns(self, if_name, netns):
        logging.debug("Attach link %s to namespace %s" % (if_name, netns))
        self.__command("ip link set %s netns %s" % (if_name, netns))
        self.__command("ip netns exec %s ip link set %s up" % (netns, if_name))

    def link_set_vtap(self, if_name, netns):
        logging.debug("Set link %s of namespace %s macvtap" % (if_name, netns))
        self.__command("ip netns exec %s ip link add link %s "
                       "type macvtap mode vepa" % (netns, if_name))
        self.__command("ip netns exec %s ip link set macvtap0 up" % netns)

    def ovs_create(self, sw_name):
        logging.debug("Create switch %s" % sw_name)
        self.__command("ovs-vsctl add-br %s" % sw_name)

    def ovs_delete(self, sw_name):
        logging.debug("Delete switch %s" % sw_name)
        self.__command("ovs-vsctl del-br %s" % sw_name)

    def ovs_add_port(self, sw_name, p_name):
        logging.debug("Add port %s to switch %s" % (p_name, sw_name))
        self.__command("ovs-vsctl add-port %s %s" % (sw_name, p_name))
        self.__command("ip link set %s up" % p_name)

    def ovs_del_port(self, sw_name, p_name):
        logging.debug("Delete port %s from switch %s" % (p_name, sw_name))
        self.__command("ovs-vsctl del-port %s %s" % (sw_name, p_name))

    def __command(self, cmd_line, shell=False):
        args = shlex.split(cmd_line)
        ret = subprocess.call(args, shell=shell)
        if ret != 0:
            msg = "Unable to excecute command %s" % (cmd_line,)
            logging.error(msg)
            raise NetemError(msg)


class NetemDaemonThread(threading.Thread):

    def __init__(self, socket):
        super(NetemDaemonThread, self).__init__()

        self.__server = None
        self.__socket = socket
        self.running = False

    def run(self):
        self.running = True
        self.__server = UnixStreamServer(self.__socket, NetemDaemonHandler)
        os.chmod(self.__socket, 0o666)

        logging.info("Start pynetem daemon")
        self.__server.serve_forever()

    def stop(self):
        if self.__server is not None:
            logging.info("Stop pynetem daemon")
            self.__server.shutdown()
            self.__server = None
        self.running = False
