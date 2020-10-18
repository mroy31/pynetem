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
import shutil
from pynetem import NetemError, get_docker_images
from pynetem.ui.config import NetemConfig
from pynetem.wrapper import _BaseWrapper
from pynetem.wrapper.link import NetemLinkFactory

DOCKER_IMAGES = get_docker_images(NetemConfig.instance())


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

    def __init__(self, p2p_sw, prj_id, conf_dir, name, n_config):
        super(DockerNode, self).__init__(prj_id)

        self.name = name
        self.conf_dir = conf_dir
        self.p2p_sw = p2p_sw
        self.running = False
        self.interfaces = []
        self.__pid = None
        self.__lk_factory = NetemLinkFactory.instance()
        self.docker_image = "image" in n_config and n_config["image"] or self.IMG
        self.container_name = "%s.%s" % (prj_id, self.name)
        self.ipv6_support = False
        if "ipv6" in n_config:
            self.ipv6_support = n_config.as_bool("ipv6")
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
        self.daemon.docker_create(
            self.name,
            self.container_name,
            self.docker_image,
            self.ipv6_support and "yes" or "no")

    def __add_if(self, peer_type, peer_instance, peer_if=None):
        if_id = len(self.interfaces)
        ifname = None
        if peer_instance is not None:
            ifname = self.gen_ifname(if_id, peer_instance, peer_if)
        self.interfaces.append({
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

    def add_br_if(self, br_instance):
        self.__add_if("bridge", br_instance)

    def start(self):
        if not self.running:
            self.daemon.docker_start(self.container_name)
            self.__pid = self.daemon.docker_pid(self.container_name)
            self.running = True
            # attach interfaces
            for if_conf in self.interfaces:
                if if_conf["peer"] == "null":
                    continue  # skip this interface
                p_if = self.__lk_factory.create(if_conf["ifname"], self.__pid)
                if if_conf["peer"] == "switch":
                    sw_instance = if_conf["peer_instance"]
                    sw_instance.attach_interface(if_conf["ifname"])
                elif if_conf["peer"] == "bridge":
                    br_instance = if_conf["peer_instance"]
                    br_instance.attach_interface(if_conf["ifname"])
                elif if_conf["peer"] == "node":
                    self.p2p_sw.add_connection(if_conf["ifname"])
                self.__attach_interface(p_if, if_conf["target_if"])

    def __attach_interface(self, if_name, target_name):
        self.daemon.docker_attach_interface(self.container_name, if_name,
                                            target_name)

    @require_running
    def open_shell(self, debug=False):
        display = self._get_x11_env()
        term_cmd = NetemConfig.instance().get("general", "terminal")
        shell_cmd = debug and self.BASH or self.SHELL
        self.daemon.docker_shell(
            self.container_name, self.name,
            shell_cmd, display, term_cmd
        )

    @require_running
    def capture(self, if_number):
        if not shutil.which("wireshark"):
            raise NetemError(
                "Unable to start capture -> Wireshark is not installed on"
                " your computer")

        if len(self.interfaces) <= if_number:
            raise NetemError("%s: interface %d does not "
                             "exist" % (self.name, if_number))

        if_name = "eth%s" % if_number
        display = self._get_x11_env()
        self.daemon.docker_capture(display, self.container_name, if_name)

    @require_running
    def set_if_state(self, if_number, state):
        if len(self.interfaces) > if_number:
            if_entry = self.interfaces[if_number]
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
        for if_c in self.interfaces:
            if if_c["peer_instance"] is None:
                continue
            if if_c["peer"] == "switch":
                if_c["peer_instance"].detach_interface(if_c["ifname"])
            elif if_c["peer"] == "bridge":
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
        self.interfaces = []

    def get_status(self):
        return {
            "name": self.name,
            "isRunning": self.running,
            "interfaces": [
                {
                    "name": i["target_if"],
                    "isUp": i["state"] == "up"
                } for i in self.interfaces
            ]

        }

    def _docker_exec(self, cmd):
        self.daemon.docker_exec(self.container_name, cmd)

    def _docker_cp(self, source, dest):
        self.daemon.docker_cp(source, dest)

    def _get_x11_env(self):
        display = ":0.0"
        if "DISPLAY" in os.environ:
            display = os.environ["DISPLAY"]
        return display


class HostNode(DockerNode):
    IMG = DOCKER_IMAGES["host"]
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


class ServerNode(HostNode):
    IMG = DOCKER_IMAGES["server"]
    SERVERS = {
        "dhcp": {
            "configs": [{
                "target": "/etc/dhcp/dhcpd.conf",
                "name": "dhcpd.conf"
            }, {
                "target": "/etc/default/isc-dhcp-server",
                "name": "isc-dhcp-server.default"
            }],
            "service": "isc-dhcp-server"
        },
        "tftp": {
            "configs": [{
                "target": "/etc/default/tftpd-hpa",
                "name": "tftpd-hpa.default",
            }],
            "service": "tftpd-hpa"
        },
    }

    def __fmt_conf_path(self, config_name, conf_path=None):
        return os.path.join(
            conf_path or self.conf_dir,
            "%s.%s" % (self.name, config_name)
        )

    def start(self):
        super(ServerNode, self).start()
        # set server configs if available
        for server in self.SERVERS:
            s_attrs = self.SERVERS[server]
            for config in s_attrs["configs"]:
                conf_path = self.__fmt_conf_path(config["name"])
                if os.path.isfile(conf_path):
                    dest = "%s:%s" % (self.container_name, config["target"])
                    self._docker_cp(conf_path, dest)

    @require_running
    def save(self, conf_path=None):
        super(ServerNode, self).save(conf_path)
        # save server configs
        for server in self.SERVERS:
            s_attrs = self.SERVERS[server]
            for config in s_attrs["configs"]:
                fconf_path = self.__fmt_conf_path(config["name"], conf_path)
                source = "%s:%s" % (self.container_name, config["target"])
                self._docker_cp(source, fconf_path)


class FrrRouter(DockerNode):
    IMG = DOCKER_IMAGES["frr"]
    SHELL = "/usr/bin/vtysh"
    CONF = "/etc/frr/frr.conf"

    def __init__(self, p2p_sw, prj_id, conf_dir, name, n_config):
        super(FrrRouter, self).__init__(p2p_sw, prj_id, conf_dir, name, n_config)
        self.mpls_support = False
        if "mpls" in n_config:
            self.mpls_support = n_config.as_bool("mpls")
        self.vrfs = "vrfs" in n_config and n_config["vrfs"].split(";") or []

    def __fmt_conf_path(self, conf_path):
        return os.path.join(
            conf_path or self.conf_dir,
            "%s.frr.conf" % self.name
        )

    def start(self):
        super(FrrRouter, self).start()
        # enable mpls if necessary
        if self.mpls_support:
            self._docker_exec("sysctl -w net.mpls.platform_labels=100000")
            self._docker_exec("sysctl -w net.mpls.conf.lo.input=1")
            for if_conf in self.interfaces:
                self._docker_exec("sysctl -w net.mpls.conf.{}.input=1".format(if_conf["target_if"]))
        # create vrfs
        for idx, vrf in enumerate(self.vrfs):
            self._docker_exec("ip link add {} type vrf table {}".format(vrf, 10+idx))
            self._docker_exec("ip link set {} up".format(vrf))
        # load frr config if available and start frr
        conf_path = self.__fmt_conf_path(None)
        if os.path.isfile(conf_path):
            dest = "{}:{}".format(self.container_name, self.CONF)
            self._docker_cp(conf_path, dest)
            self._docker_exec("chown frr:frr {}".format(self.CONF))
        self._docker_exec("/usr/lib/frr/frrinit.sh start")

    @require_running
    def save(self, conf_path=None):
        self._docker_exec("vtysh -w")
        self._docker_exec("chmod +r {}".format(self.CONF))
        source = "{}:{}".format(self.container_name, self.CONF)
        self._docker_cp(source, self.__fmt_conf_path(conf_path))


DOCKER_NODES = {
    "host": HostNode,
    "server": ServerNode,
    "frr": FrrRouter,
    "router": FrrRouter
}
