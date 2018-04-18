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
            "docker_shell": "^docker_shell (\S+) (\S+) (\S+) (.+)$",
        }

    def handle(self):
        cmd = self.request.recv(1024).decode("utf-8").strip()
        logging.debug("Receive data: %s" % cmd)

        try:
            cmd_name = cmd.split()[0]
            if cmd_name not in self.__cmd_list:
                raise NetemError("Unknown command %s" % cmd)
            cmd_regexp = self.__cmd_list[cmd_name]
            # verify arguments
            match_obj = re.match(cmd_regexp, cmd)
            if match_obj is None:
                raise NetemError("Wrong number of args for "
                                 "command %s" % cmd_name)
            # execute command
            ret = getattr(self, cmd_name)(*match_obj.groups())
        except NetemError as err:
            msg = "ERROR: %s" % err
            self.request.sendall(msg.encode("utf-8"))
        else:
            ans = "OK"
            if ret is not None:
                ans += " %s" % ret
            self.request.sendall(ans.encode("utf-8"))

    def docker_create(self, name, container_name, image):
        logging.debug("Create docker container %s" % container_name)
        self.__command("docker create --privileged --cap-add=ALL --net=none "
                       "-h %s --name %s %s" % (name, container_name, image))

    def docker_attach_interface(self, container_name, if_name, target_name):
        logging.debug("Docker : attach if %s to container "
                      "%s" % (if_name, container_name))
        self.__command("docker exec %s ip link set %s "
                       "name %s" % (container_name, if_name, target_name))
        self.__command("docker exec %s ip link set %s "
                       "up" % (container_name, target_name))

    def docker_start(self, container_name):
        logging.debug("Start docker container %s" % container_name)
        self.__command("docker start %s" % container_name)

    def docker_stop(self, container_name):
        logging.debug("Stop docker container %s" % container_name)
        # before stop shell if exist
        if container_name in self.__docker_shells:
            ps = self.__docker_shells[container_name]
            if ps.poll() is None:
                ps.terminate()
            del self.__docker_shells[container_name]
        self.__command("docker stop %s" % container_name)

    def docker_rm(self, container_name):
        logging.debug("Delete docker container %s" % container_name)
        self.__command("docker rm %s" % container_name)

    def docker_pid(self, container_name):
        logging.debug("Get PID of docker container %s" % container_name)
        pid = self.__command("docker inspect --format '{{.State.Pid}}' "
                             "%s" % container_name, check_output=True)
        return pid

    def docker_cp(self, source, dest):
        logging.debug("Docker cp from %s to %s" % (source, dest))
        self.__command("docker cp %s %s" % (source, dest))

    def docker_exec(self, container_name, cmd_line):
        logging.debug("Docker %s : exec %s" % (container_name, cmd_line))
        self.__command("docker exec %s %s" % (container_name, cmd_line))

    def docker_shell(self, c_name, name, shell, term_cmd):
        logging.debug("Docker open shell for container %s" % c_name)
        term_cmd = term_cmd % {
            "title": name,
            "cmd": "docker exec -it %s %s" % (c_name, shell)
        }
        args = shlex.split(term_cmd)
        subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=False)

    def tap_create(self, name, user):
        logging.debug("Create tap %s" % name)
        self.__command("tunctl -u %s -t %s" % (user, name))
        self.__command("ip link set %s up" % (name,))

    def tap_delete(self, name):
        logging.debug("Delete tap %s" % name)
        self.__command("tunctl -d %s" % (name,))

    def __is_pid(self, pid):
        try:
            int(pid)
        except ValueError:
            return False
        else:
            return True

    def netns_create(self, name):
        logging.debug("Create netns %s" % name)
        if not self.__is_pid(name):
            self.__command("ip netns add %s" % name)
        else:
            if not os.path.isdir("/var/run/netns"):
                os.mkdir("/var/run/netns")
            self.__command("ln -s /proc/%s/ns/net /var/run/netns/%s" % (name, name))

    def netns_delete(self, name):
        logging.debug("Delete netns %s" % name)
        if not self.__is_pid(name):
            self.__command("ip netns del %s" % name)
        else:
            self.__command("rm /var/run/netns/%s" % name)

    def link_create(self, if1, if2):
        logging.debug("Create link %s<-->%s" % (if1, if2))
        self.__command("ip link add %s type veth peer name %s" % (if1, if2))

    def link_delete(self, if_name):
        logging.debug("Delete link %s" % if_name)
        self.__command("ip link del %s" % if_name)

    def link_netns(self, if_name, netns):
        logging.debug("Attach link %s to namespace %s" % (if_name, netns))
        self.__command("ip link set %s netns %s" % (if_name, netns))

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

    def __command(self, cmd_line, check_output=False, shell=False):
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
