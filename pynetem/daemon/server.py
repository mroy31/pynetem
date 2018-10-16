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

import re
import os
import threading
from socketserver import UnixStreamServer, BaseRequestHandler
import subprocess
import logging
import shlex
from pynetem import __version__, NETEM_ID
from pynetem import NetemError
from pynetem.utils import get_exc_desc
from pynetem.utils import cmd_call

CMD_LIST = {
    "version": "^version$",
    "tap_create": "^tap_create (\S+) (\S+)$",
    "tap_delete": "^tap_delete (\S+)$",
    "netns_create": "^netns_create (\S+)$",
    "netns_delete": "^netns_delete (\S+)$",
    "link_create": "^link_create (\S+) (\S+)$",
    "link_delete": "^link_delete (\S+)$",
    "link_netns": "^link_netns (\S+) (\S+)$",
    "link_set_vtap": "^link_set_vtap (\S+) (\S+)$",
    "ovs_create": "^ovs_create (\S+)$",
    "ovs_delete": "^ovs_delete (\S+)$",
    "ovs_add_port": "^ovs_add_port (\S+) (\S+)$",
    "ovs_port_vlan": "^ovs_port_vlan (\S+) ([0-9]+)$",
    "ovs_add_mirror_port": "^ovs_add_mirror_port (\S+) (\S+)$",
    "ovs_del_port": "^ovs_del_port (\S+) (\S+)$",
    "docker_create": "^docker_create (\S+) (\S+) (\S+)$",
    "docker_start": "^docker_start (\S+)$",
    "docker_stop": "^docker_stop (\S+)$",
    "docker_rm": "^docker_rm (\S+)$",
    "docker_attach_interface": "^docker_attach_interface (\S+) (\S+) (\S+)$",
    "docker_pid": "^docker_pid (\S+)$",
    "docker_cp": "^docker_cp (\S+) (\S+)$",
    "docker_exec": "^docker_exec (\S+) (.+)$",
    "docker_shell": "^docker_shell (\S+) (\S+) (\S+) (\S+) (\S+) (.+)$",
    "docker_capture": "^docker_capture (\S+) (\S+) (\S+) (\S+)$",
    "clean": "^clean (\S+)$",
}


def run_command(cmd_line, check_output=False, shell=False):
    args = shlex.split(cmd_line)
    if check_output:
        try:
            result = subprocess.check_output(args, shell=shell)
        except subprocess.CalledProcessError:
            msg = "Unable to execute command %s" % (cmd_line,)
            logging.error(msg)
            raise NetemError(msg)
        return result.decode("utf-8").strip("\n")
    else:
        ret = subprocess.call(args, shell=shell)
        if ret != 0:
            msg = "Unable to excecute command %s" % (cmd_line,)
            logging.error(msg)
            raise NetemError(msg)


class NetemDaemonHandler(BaseRequestHandler):

    def handle(self):
        cmd = self.request.recv(1024).decode("utf-8").strip()
        logging.debug("Receive data: %s" % cmd)

        msg = ""
        try:
            cmd_args = cmd.split()
            if len(cmd_args) < 1:
                raise NetemError("The sent command is empty")

            cmd_name = cmd_args[0]
            if cmd_name not in CMD_LIST:
                raise NetemError("Unknown command %s" % cmd)
            cmd_regexp = CMD_LIST[cmd_name]
            # verify arguments
            match_obj = re.match(cmd_regexp, cmd)
            if match_obj is None:
                raise NetemError("Wrong number of args for "
                                 "command %s" % cmd_name)
            # execute command
            ret = getattr(self, cmd_name)(*match_obj.groups())
        except NetemError as err:
            msg = "ERROR: %s" % err
        except Exception as ex:
            logging.error(get_exc_desc())
            msg = "ERROR: Unknown exception happen see log for details"
        else:
            msg = "OK"
            if ret is not None:
                msg += " %s" % ret
        self.request.sendall(msg.encode("utf-8"))

    @staticmethod
    def version():
        return __version__

    @staticmethod
    def docker_create(name, container_name, image):
        logging.debug("Create docker container %s" % container_name)
        run_command("docker create --privileged --cap-add=ALL --net=none "
                    "-h %s --name %s %s" % (name, container_name, image))

    @staticmethod
    def docker_attach_interface(container_name, if_name, target_name):
        logging.debug("Docker : attach if %s to container "
                      "%s" % (if_name, container_name))
        run_command("docker exec %s ip link set %s "
                    "name %s" % (container_name, if_name, target_name))
        run_command("docker exec %s ip link set %s "
                    "up" % (container_name, target_name))

    @staticmethod
    def docker_start(container_name):
        logging.debug("Start docker container %s" % container_name)
        run_command("docker start %s" % container_name)

    @staticmethod
    def docker_stop(container_name):
        logging.debug("Stop docker container %s" % container_name)
        run_command("docker stop %s" % container_name)

    @staticmethod
    def docker_rm(container_name):
        logging.debug("Delete docker container %s" % container_name)
        run_command("docker rm %s" % container_name)

    @staticmethod
    def docker_pid(container_name):
        logging.debug("Get PID of docker container %s" % container_name)
        pid = run_command("docker inspect --format '{{.State.Pid}}' "
                          "%s" % container_name, check_output=True)
        return pid

    @staticmethod
    def docker_cp(source, dest):
        logging.debug("Docker cp from %s to %s" % (source, dest))
        run_command("docker cp %s %s" % (source, dest))

    @staticmethod
    def docker_exec(container_name, cmd_line):
        logging.debug("Docker %s : exec %s" % (container_name, cmd_line))
        run_command("docker exec %s %s" % (container_name, cmd_line))

    @classmethod
    def docker_shell(cls, c_name, name, shell, display, xauth, term_cmd):
        logging.debug("Docker open shell for container %s" % c_name)
        term_cmd = term_cmd % {
            "title": name,
            "cmd": "docker exec -it %s %s" % (c_name, shell)
        }
        args = shlex.split(term_cmd)
        subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=False,
                         env=cls.__set_x11_env(display, xauth))

    @classmethod
    def docker_capture(cls, display, xauth, c_name, if_name):
        logging.debug("Docker launch capture on if %s:%s" % (c_name, if_name))
        pretty_name = c_name.split(".", 1)[1]
        cmd = "/bin/bash -c 'docker exec {0} tcpdump -s 0 -U -w - -i {1} "\
              "2>/dev/null | wireshark -o 'gui.window_title:{1}@{2}' "\
              "-k -i - &'".format(c_name, if_name, pretty_name)
        subprocess.call(shlex.split(cmd),
                        env=cls.__set_x11_env(display, xauth))

    @staticmethod
    def tap_create(name, user):
        logging.debug("Create tap %s" % name)
        run_command("tunctl -u %s -t %s" % (user, name))
        run_command("ip link set %s up" % (name,))

    @staticmethod
    def tap_delete(name):
        logging.debug("Delete tap %s" % name)
        run_command("tunctl -d %s" % (name,))

    @staticmethod
    def __is_pid(pid):
        try:
            int(pid)
        except ValueError:
            return False
        else:
            return True

    @classmethod
    def netns_create(cls, name):
        logging.debug("Create netns %s" % name)
        if not cls.__is_pid(name):
            run_command("ip netns add %s" % name)
        else:
            if not os.path.isdir("/var/run/netns"):
                os.mkdir("/var/run/netns")
            run_command("ln -s /proc/%s/ns/net "
                        "/var/run/netns/%s" % (name, name))

    @classmethod
    def netns_delete(cls, name):
        logging.debug("Delete netns %s" % name)
        if not cls.__is_pid(name):
            run_command("ip netns del %s" % name)
        else:
            run_command("rm /var/run/netns/%s" % name)

    @staticmethod
    def link_create(if1, if2):
        logging.debug("Create link %s<-->%s" % (if1, if2))
        run_command("ip link add %s type veth peer name %s" % (if1, if2))

    @staticmethod
    def link_delete(if_name):
        logging.debug("Delete link %s" % if_name)
        run_command("ip link del %s" % if_name)

    @staticmethod
    def link_netns(if_name, netns):
        logging.debug("Attach link %s to namespace %s" % (if_name, netns))
        run_command("ip link set %s netns %s" % (if_name, netns))

    @staticmethod
    def link_set_vtap(if_name, netns):
        logging.debug("Set link %s of namespace %s macvtap" % (if_name, netns))
        run_command("ip netns exec %s ip link add link %s "
                    "type macvtap mode vepa" % (netns, if_name))
        run_command("ip netns exec %s ip link set macvtap0 up" % netns)

    @staticmethod
    def __is_ovsbr_exist(sw_name):
        return cmd_call("ovs-vsctl br-exists %s" % sw_name) != 2

    @classmethod
    def ovs_create(cls, sw_name):
        logging.debug("Create switch %s" % sw_name)
        if cls.__is_ovsbr_exist(sw_name):
            return "EXIST"
        run_command("ovs-vsctl add-br %s" % sw_name)

    @classmethod
    def ovs_delete(cls, sw_name):
        logging.debug("Delete switch %s" % sw_name)
        if cls.__is_ovsbr_exist(sw_name):
            run_command("ovs-vsctl del-br %s" % sw_name)

    @staticmethod
    def ovs_add_port(sw_name, p_name):
        logging.debug("Add port %s to switch %s" % (p_name, sw_name))
        run_command("ovs-vsctl add-port %s %s" % (sw_name, p_name))
        run_command("ip link set %s up" % p_name)

    @staticmethod
    def ovs_port_vlan(p_name, vlan):
        logging.debug("Set port %s to belong to vlan %s" % (p_name, vlan))
        run_command("ovs-vsctl set port %s tag=%s" % (p_name, vlan))

    @staticmethod
    def ovs_del_port(sw_name, p_name):
        logging.debug("Delete port %s from switch %s" % (p_name, sw_name))
        run_command("ovs-vsctl del-port %s %s" % (sw_name, p_name))

    @classmethod
    def clean(cls, prj_id):
        logging.debug("Clean project %s" % prj_id)
        # remove existing docker containers
        d_cmd = "docker container list --format '{{.Names}}' --all"
        containers = run_command(d_cmd, check_output=True).split("\n")
        for container_name in containers:
            if container_name.startswith(prj_id):
                cls.docker_stop(container_name)
                cls.docker_rm(container_name)

        # remove existing ovs switches
        s_cmd = "ovs-vsctl list-br"
        switches = run_command(s_cmd, check_output=True).split("\n")
        for s_name in switches:
            if s_name.startswith(prj_id):
                cls.ovs_delete(s_name)

    @staticmethod
    def __set_x11_env(display, xauth):
        env = {"DISPLAY": display}
        if xauth != "null":
            env["XAUTHORITY"] = xauth
        return env


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
            # before stopping the server, clean the env
            NetemDaemonHandler.clean(NETEM_ID)

            logging.info("Stop pynetem daemon")
            self.__server.shutdown()
            self.__server = None
        self.running = False
