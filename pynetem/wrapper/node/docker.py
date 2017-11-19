# pyNetmem, a network emulator
# Copyright (C) 2016 Mickael Royer <mickael.royer@enac.fr>
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
import subprocess
import shlex
import logging
from pynetem import NETEM_ID
from pynetem import NetemError
from pynetem.ui.config import NetemConfig
from pynetem.wrapper import _BaseWrapper
from pynetem.wrapper.link import NetemLinkFactory


class DockerNode(_BaseWrapper):
    SHELL = "/bin/bash"

    def __init__(self, conf_dir, name, image_name):
        super(DockerNode, self).__init__()

        self.name = name
        self.conf_dir = conf_dir
        self.__running = False
        self.__pid = None
        self.__shell = None
        self.__image = image_name
        self.__interfaces = []
        self.__link_factory = NetemLinkFactory.instance()
        self.container_name = "%s.%s" % (NETEM_ID, self.name)
        # create container
        self.__create()

    def get_name(self):
        return self.name

    def get_pid(self):
        return self.__pid

    def __create(self):
        logging.debug("Create docker container %s" % self.container_name)
        self._command("docker create --privileged --cap-add=ALL --net=none "
                      "-h %s --name %s %s" % (self.name, self.container_name, 
                                              self.__image))

    def add_sw_if(self, sw_instance):
        if_parms = {
            "peer": "switch",
            "sw_instance": sw_instance,
            "left_if": "%s.%s" % (sw_instance.get_name(), self.name),
            "right_if": "%s.%s" % (self.name, sw_instance.get_name()),
            "target_if": "eth%d" % len(self.__interfaces)
        }
        self.__interfaces.append(if_parms)

    def start(self):
        if not self.__running:
            logging.debug("Start docker container %s" % self.container_name)
            self._command("docker start %s" % self.container_name)
            self.__pid = self._command("docker inspect --format '{{.State.Pid}}' "
                                       "%s" % self.container_name)
            for if_conf in self.__interfaces:
                if if_conf["peer"] == "switch":
                    sw_instance = if_conf["sw_instance"]
                    if sw_instance is not None:
                        sw_type = sw_instance.get_sw_type()
                        if sw_type == "vde":
                            raise NetemError("Docker node can not be "
                                             "attached to vde switch")
                        # create link attach to node and switch
                        self.__link_factory.create_link(if_conf["left_if"],
                                                        if_conf["right_if"],
                                                        None,
                                                        self.__pid)
                        sw_instance.attach_interface(if_conf["left_if"])
                        self.__attach_interface(if_conf["right_if"],
                                                if_conf["target_if"])
            self.__running = True

    def __attach_interface(self, if_name, target_name):
        self._command("docker exec %s ip link set %s "
                      "name %s" % (self.container_name, if_name, target_name))
        self._command("docker exec %s ip link set %s "
                      "up" % (self.container_name, target_name))

    def open_shell(self):
        if self.__shell is not None and self.__shell.poll() is None:
            raise NetemError("The console is already opened")
        if self.__running:
            term_cmd = NetemConfig.instance().get("general", "terminal") % {
                "title": self.name,
                "cmd": "docker exec -it %s %s" % (self.container_name, self.SHELL)
            }
            args = shlex.split(term_cmd)
            self.__shell = subprocess.Popen(args, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            shell=False)

    def save(self):
        raise NotImplementedError

    def stop(self):
        if self.__running:
            logging.debug("Stop docker container %s" % self.container_name)
            if self.__shell is not None and self.__shell.poll() is None:
                self.__shell.terminate()
                self.__shell = None
            for if_c in self.__interfaces:
                if if_c["sw_instance"] is None:
                    continue
                if_c["sw_instance"].detach_interface(if_c["left_if"])
                self.__link_factory.delete_link(if_c["left_if"],
                                                if_c["right_if"])
            self._command("docker stop %s" % self.container_name)
            self.__pid = None
            self.__running = False

    def clean(self):
        self.stop()
        self._command("docker rm %s" % self.container_name)
        self.__interfaces = []

    def _docker_exec(self, cmd, interactive=False, check_output=True):
        cmd_line = "docker exec"
        if interactive:
            cmd_line += " -i"
        cmd_line += " %s %s" % (self.container_name, cmd)
        self._command(cmd_line, check_output=check_output)


class HostNode(DockerNode):
    IMG = "rca/host"
    CONFIG_FILE = "/tmp/custom.net.conf"

    def __init__(self, conf_dir, name, node_config):
        super(HostNode, self).__init__(conf_dir, name, self.IMG)

    def __conf_path(self):
        return os.path.join(self.conf_dir, "%s.net.conf" % self.name)

    def start(self):
        super(HostNode, self).start()
        # set network config if available
        conf_path = self.__conf_path()
        if os.path.isfile(conf_path):
            self._command("docker cp %s %s:%s" % (self.__conf_path(),
                                                  self.container_name,
                                                  self.CONFIG_FILE))
            self._docker_exec("network-config.py -l %s" % self.CONFIG_FILE)

    def save(self):
        self._docker_exec("network-config.py -s %s" % self.CONFIG_FILE)
        self._command("docker cp %s:%s "
                      "%s" % (self.container_name, self.CONFIG_FILE,
                              self.__conf_path()))


class XorpRouter(DockerNode):
    IMG = "rca/xorp"
    CONFIG_FILE = "/etc/xorp/config.boot"
    SHELL = "/usr/sbin/xorpsh"

    def __init__(self, conf_dir, name, node_config):
        super(XorpRouter, self).__init__(conf_dir, name, self.IMG)

    def __conf_path(self):
        return os.path.join(self.conf_dir, "%s.xorp.conf" % self.name)

    def start(self):
        super(XorpRouter, self).start()
        # load xorp config if available and start xorp
        conf_path = self.__conf_path()
        if os.path.isfile(conf_path):
            self._command("docker cp %s %s:%s" % (self.__conf_path(),
                                                  self.container_name,
                                                  self.CONFIG_FILE))
        # then restart xorp processes
        self._docker_exec("/etc/init.d/xorp restart")

    def save(self):
        self._docker_exec("xorpsh -c 'configure' -c 'save /tmp/xorp.conf'")
        self._command("docker cp %s:/tmp/xorp.conf "
                      "%s" % (self.container_name, self.__conf_path()))


class QuaggaRouter(DockerNode):
    IMG = "rca/quagga"
    SHELL = "/usr/bin/vtysh"
    TMP_CONF = "/tmp/quagga.conf"

    def __init__(self, conf_dir, name, node_config):
        super(QuaggaRouter, self).__init__(conf_dir, name, self.IMG)

    def __conf_path(self):
        return os.path.join(self.conf_dir, "%s.quagga.conf" % self.name)

    def start(self):
        super(QuaggaRouter, self).start()
        # load quagga config if available and start quagga
        conf_path = self.__conf_path()
        if os.path.isfile(conf_path):
            self._docker_exec("supervisorctl start all:")
            self._command("docker cp %s %s:%s" % (conf_path,
                                                  self.container_name,
                                                  self.TMP_CONF))
            self._docker_exec("load-quagga.sh %s" % self.TMP_CONF)

    def save(self):
        self._docker_exec("save-quagga.sh %s" % self.TMP_CONF)
        self._command("docker cp %s:%s "
                      "%s" % (self.container_name, self.TMP_CONF, 
                              self.__conf_path()))


DOCKER_NODES = {
    "host": HostNode,
    "xorp": XorpRouter,
    "quagga": QuaggaRouter,
}
