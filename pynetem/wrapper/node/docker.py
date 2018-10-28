# pyNetmem, a network emulator
# Copyright (C) 2016-2018 Mickael Royer <mickael.royer@enac.fr>
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
from pynetem import NetemError
from pynetem.ui.config import NetemConfig
from pynetem.wrapper import _BaseWrapper
from pynetem.wrapper.link import NetemLinkFactory


def require_running(func):
    def running_func(self, *args, **kwargs):
        if not self.running:
            print("Warning: try to execute action "
                  "%s on stopped node" % func.__name__)
            return
        return func(self, *args, **kwargs)

    running_func.__name__ = func.__name__
    return running_func


class DockerNode(_BaseWrapper):
    SHELL = "/bin/bash"
    BASH = "/bin/bash"
    IMG = None

    def __init__(self, p2p_sw, prj_id, conf_dir, name, image_name):
        super(DockerNode, self).__init__(prj_id)

        self.name = name
        self.conf_dir = conf_dir
        self.p2p_sw = p2p_sw
        self.running = False
        self.__pid = None
        self.__interfaces = []
        self.__lk_factory = NetemLinkFactory.instance()
        self.container_name = "%s.%s" % (prj_id, self.name)
        # create container
        self.__create()

    def get_name(self):
        return self.name

    def get_type(self):
        return "node.docker"

    def get_pid(self):
        return self.__pid

    def is_running(self):
        return self.running

    def __create(self):
        logging.debug("Create docker container %s" % self.container_name)
        self.daemon.docker_create(self.name, self.container_name, self.IMG)

    def __add_if(self, peer_type, peer_instance, peer_if=None):
        if_id = len(self.__interfaces)
        ifname = None
        if peer_instance is not None:
            ifname = self.gen_ifname(if_id, peer_instance, peer_if)
        self.__interfaces.append({
            "peer": peer_type,
            "peer_instance": peer_instance,
            "ifname": ifname,
            "target_if": "eth%d" % if_id,
            "state": "up"
        })

    def add_null_if(self):
        self.__add_if("null", None)

    def add_node_if(self, node_instance, if_number):
        self.__add_if("node", node_instance, peer_if=if_number)

    def add_sw_if(self, sw_instance):
        self.__add_if("switch", sw_instance)

    def start(self):
        if not self.running:
            self.daemon.docker_start(self.container_name)
            self.__pid = self.daemon.docker_pid(self.container_name)
            self.running = True
            # attach interfaces
            for if_conf in self.__interfaces:
                if if_conf["peer"] == "null":
                    continue  # skip this interface
                p_if = self.__lk_factory.create(if_conf["ifname"], self.__pid)
                if if_conf["peer"] == "switch":
                    sw_instance = if_conf["peer_instance"]
                    sw_instance.attach_interface(if_conf["ifname"])
                elif if_conf["peer"] == "node":
                    self.p2p_sw.add_connection(if_conf["ifname"])
                self.__attach_interface(p_if, if_conf["target_if"])

    def __attach_interface(self, if_name, target_name):
        self.daemon.docker_attach_interface(self.container_name, if_name,
                                            target_name)

    @require_running
    def open_shell(self, debug=False):
        display, xauth = self._get_x11_env()
        term_cmd = NetemConfig.instance().get("general", "terminal")
        shell_cmd = debug and self.BASH or self.SHELL
        self.daemon.docker_shell(
            self.container_name, self.name,
            shell_cmd, display, xauth, term_cmd
        )

    @require_running
    def capture(self, if_number):
        if len(self.__interfaces) > if_number:
            if_name = "eth%s" % if_number
            display, xauth = self._get_x11_env()
            self.daemon.docker_capture(display, xauth,
                                       self.container_name, if_name)
        else:
            raise NetemError("%s: interface %d does not "
                             "exist" % (self.name, if_number))

    @require_running
    def set_if_state(self, if_number, state):
        if len(self.__interfaces) > if_number:
            if_entry = self.__interfaces[if_number]
            if_name = if_entry["target_if"]
            self._docker_exec("ip link set {} {}".format(if_name, state))
            if_entry["state"] = state
        else:
            raise NetemError("%s: interface %d does not "
                             "exist" % (self.name, if_number))

    def save(self, conf_path=None):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    @require_running
    def stop(self):
        for if_c in self.__interfaces:
            if if_c["peer_instance"] is None:
                continue
            if if_c["peer"] == "switch":
                if_c["peer_instance"].detach_interface(if_c["ifname"])
            elif if_c["peer"] == "node":
                self.p2p_sw.delete_connection(if_c["ifname"])
            self.__lk_factory.delete(if_c["ifname"])
        self.daemon.docker_stop(self.container_name)
        self.__pid = None
        self.running = False

    def clean(self):
        if self.running:
            self.stop()
        self.daemon.docker_rm(self.container_name)
        self.__interfaces = []

    def get_status(self):
        n_status = self.running and "Started" or "Stopped"
        if_status = "\n".join(["\t\t%s: %s" % (i["target_if"], i["state"]) 
                               for i in self.__interfaces])
        return "{0}\n{1}".format(n_status, if_status)

    def _docker_exec(self, cmd):
        self.daemon.docker_exec(self.container_name, cmd)

    def _docker_cp(self, source, dest):
        self.daemon.docker_cp(source, dest)

    def _get_x11_env(self):
        display, xauth = ":0.0", "null"
        if "DISPLAY" in os.environ:
            display = os.environ["DISPLAY"]    
        if "XAUTHORITY" in os.environ:
            xauth = os.environ["XAUTHORITY"]    
        return display, xauth


class HostNode(DockerNode):
    IMG = "rca/host"
    CONFIG_FILE = "/tmp/custom.net.conf"

    def __fmt_conf_path(self, conf_path):
        return os.path.join(
            conf_path or self.conf_dir,
            "%s.net.conf" % self.name
        )

    def start(self):
        super(HostNode, self).start()
        # set network config if available
        conf_path = self.__fmt_conf_path(None)
        if os.path.isfile(conf_path):
            dest = "%s:%s" % (self.container_name, self.CONFIG_FILE)
            self._docker_cp(conf_path, dest)
            self._docker_exec("network-config.py -l %s" % self.CONFIG_FILE)

    @require_running
    def save(self, conf_path=None):
        self._docker_exec("network-config.py -s %s" % self.CONFIG_FILE)
        source = "%s:%s" % (self.container_name, self.CONFIG_FILE)
        self._docker_cp(source, self.__fmt_conf_path(conf_path))


class QuaggaRouter(DockerNode):
    IMG = "rca/quagga"
    SHELL = "/usr/bin/vtysh"
    TMP_CONF = "/tmp/quagga.conf"

    def __fmt_conf_path(self, conf_path):
        return os.path.join(
            conf_path or self.conf_dir,
            "%s.quagga.conf" % self.name
        )

    def start(self):
        super(QuaggaRouter, self).start()
        # load quagga config if available and start quagga
        conf_path = self.__fmt_conf_path(None)
        if os.path.isfile(conf_path):
            self._docker_exec("supervisorctl start all:")
            dest = "%s:%s" % (self.container_name, self.TMP_CONF)
            self._docker_cp(conf_path, dest)
            self._docker_exec("load-quagga.sh %s" % self.TMP_CONF)

    @require_running
    def save(self, conf_path=None):
        self._docker_exec("save-quagga.sh %s" % self.TMP_CONF)
        source = "%s:%s" % (self.container_name, self.TMP_CONF)
        self._docker_cp(source, self.__fmt_conf_path(conf_path))


class FrrRouter(DockerNode):
    IMG = "rca/frr"
    SHELL = "/usr/bin/vtysh"
    TMP_CONF = "/tmp/frr.conf"

    def __fmt_conf_path(self, conf_path):
        return os.path.join(
            conf_path or self.conf_dir,
            "%s.frr.conf" % self.name
        )

    def start(self):
        super(FrrRouter, self).start()
        # load frr config if available and start frr
        conf_path = self.__fmt_conf_path(None)
        if os.path.isfile(conf_path):
            self._docker_exec("supervisorctl start all:")
            dest = "%s:%s" % (self.container_name, self.TMP_CONF)
            self._docker_cp(conf_path, dest)
            self._docker_exec("load-frr.sh %s" % self.TMP_CONF)

    @require_running
    def save(self, conf_path=None):
        self._docker_exec("save-frr.sh %s" % self.TMP_CONF)
        source = "%s:%s" % (self.container_name, self.TMP_CONF)
        self._docker_cp(source, self.__fmt_conf_path(conf_path))


DOCKER_NODES = {
    "host": HostNode,
    "quagga": QuaggaRouter,
    "frr": FrrRouter
}
