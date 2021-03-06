# pynetem: network emulator
# Copyright (C) 2015-2019 Mickael Royer <mickael.royer@recherche.enac.fr>
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
import asyncio
import re
from pynetem import NetemError
from pynetem.server.rpc import loads_request, RPCResponse, RPCSignal
from pynetem.ui.config import NetemConfig
from pynetem.daemon.client import NetemDaemonClient
from pynetem.signals import ALL_SIGNALS
from pynetem.project import NetemProject
from pynetem.utils import get_exc_desc

DELIMITER = b"ENDNETEM\n"


def cmd(cmd_args=[]):
    def cmd_decorator(func):
        def cmd_func(self, *args, **kwargs):
            # test args
            if len(cmd_args) != len(args):
                raise NetemError("Wrong number of arguments")
            # run original func
            return func(self, *args, **kwargs)

        cmd_func.__name__ = func.__name__
        return cmd_func

    return cmd_decorator


class NetemProtocol(asyncio.Protocol):

    def __init__(self, project):
        super(NetemProtocol, self).__init__()
        self.project = project
        self.__need_to_quit = False

    def connection_made(self, transport):
        self.transport = transport
        self.factory.set_signals(self)

    def connection_lost(self, exc):
        self.factory.close_signals(self)

    def data_received(self, line):
        # use str instead of bytes to decode json commands
        # and return answer
        line = line.strip(DELIMITER).decode("utf-8")
        delimiter = DELIMITER.decode("utf-8")

        logging.debug("Receive command '%s'" % line)
        try:
            parsed = loads_request(line)
            args, method = parsed['params'], parsed["method"]
            function = getattr(self, "do_%s" % method)
        except NetemError as err:
            try:
                r_id = parsed["id"]
            except Exception:
                r_id = None
            ans = RPCResponse(r_id, "error", str(err))
        except AttributeError:
            ans = RPCResponse(
                None, "error", "Method %s not found" % parsed["method"]
            )
        else:
            try:
                result = function(*args)
            except NetemError as err:
                ans = RPCResponse(parsed["id"], "error", str(err))
            except Exception:
                logging.error(get_exc_desc())
                msg = "Unknown exception happen see log for details"
                ans = RPCResponse(parsed["id"], "error", msg)
            else:
                ans = RPCResponse(parsed["id"], "OK", result or "")

        logging.debug("send back answer '%s'" % ans.to_json())
        self.send_buffer(ans.to_json()+delimiter)
        if self.__need_to_quit:
            self.factory.stop()

    def send_buffer(self, buf):
        if isinstance(buf, str):
            buf = buf.encode("utf-8")
        self.transport.write(buf)

    @cmd()
    def do_quit(self):
        self.project.close()
        self.__need_to_quit = True

    @cmd()
    def do_projectPath(self):
        return self.project.get_path()

    @cmd()
    def do_load(self):
        self.project.load_topology()

    @cmd()
    def do_reload(self):
        self.project.topology.reload()

    @cmd()
    def do_save(self):
        self.project.save()

    @cmd(cmd_args=[r"^[^\0]+$", r"^[^\0]+$"])
    def do_copy(self, source, dest):
        def get_path_type(p):
            docker_re = r"^(\w+):([^\0]+)$"
            args = re.match(docker_re, p)
            if args is None:
                return "host", None, p
            else:
                return "docker", args.group(1), args.group(2)

        def get_node(name):
            node = self.project.topology.get_node(name)
            if node is None:
                raise NetemError("Node {} does not exist".format(name))
            elif node.get_type() != "node.docker":
                raise NetemError("Copy cmd works only with docker nodes")
            return node

        s_type, s_name, s_path = get_path_type(source)
        d_type, d_name, d_path = get_path_type(dest)
        if s_type == d_type:
            raise NetemError("Can not do copy {0}/{0}".format(s_type))

        if s_type == "docker":  # d_type = host
            node = get_node(s_name)
            node.source_copy(s_path, d_path)

        else:  # s_type = host
            if not os.path.exists(s_path):
                raise NetemError("Host path {} does not exist".format(d_path))
            node = get_node(d_name)
            node.dest_copy(s_path, d_path)

    @cmd(cmd_args=[r"^\S+$"])
    def do_config(self, conf_path):
        conf_path = os.path.abspath(conf_path)
        if not os.path.isdir(conf_path):
            raise NetemError("%s is not a valid path" % conf_path)
        self.project.save_config(conf_path)

    @cmd(cmd_args=[r"^\S+$"])
    def do_capture(self, if_name):
        self.project.topology.capture(if_name)

    @cmd()
    def do_check(self):
        self.project.topology.check()
        return True

    @cmd()
    def do_topologyFile(self):
        return self.project.get_topology_file()

    @cmd()
    def do_isTopologyModified(self):
        return self.project.is_topology_modified()

    @cmd()
    def do_view(self):
        return self.project.view_topology()

    @cmd(cmd_args=[r"^\S+$"])
    def do_start(self, node_id):
        topo = self.project.topology
        for node in self.__get_nodes(node_id):
            topo.start(node.get_name())

    @cmd(cmd_args=[r"^\S+$"])
    def do_stop(self, node_id):
        topo = self.project.topology
        for node in self.__get_nodes(node_id):
            topo.stop(node.get_name())

    @cmd(cmd_args=[r"^\S+$"])
    def do_restart(self, node_id):
        topo = self.project.topology
        for node in self.__get_nodes(node_id):
            topo.stop(node.get_name())
            topo.start(node.get_name())

    @cmd()
    def do_status(self):
        return self.project.get_status()

    def __open_shell(self, node_id, bash):
        nodes = self.__get_nodes(node_id)
        if len(nodes) == 0:
            raise NetemError("Node '%s' does not exist" % node_id)
        for node in nodes:
            node.open_shell(bash=bash)

    @cmd(cmd_args=[r"^\S+$"])
    def do_console(self, node_id):
        self.__open_shell(node_id, False)

    @cmd(cmd_args=[r"^\S+$"])
    def do_shell(self, node_id):
        self.__open_shell(node_id, True)

    @cmd(cmd_args=[r"^\S+$", r"^\S+$"])
    def do_ifstate(self, if_name, state):
        self.project.topology.set_if_state(if_name, state)

    def __get_nodes(self, arg):
        if arg == "all":
            return self.project.topology.get_all_nodes()
        else:
            nodes = []
            n_ids = arg.split()
            for n_id in n_ids:
                node = self.project.topology.get_node(arg)
                if node is not None:
                    nodes.append(node)
            return nodes


class NetemFactory(object):

    def __init__(self, netid, project, loop):
        # init daemon client
        daemon = NetemDaemonClient.instance()
        s_name = NetemConfig.instance().get("general", "daemon_socket")
        daemon.set_socket_path(s_name)

        self.server = None
        self.project = NetemProject(daemon, netid, project)
        self.loop = loop
        self.clients = []

    def build_protocol(self):
        p = NetemProtocol(self.project)
        p.factory = self

        return p

    def stop(self):
        self.clients = []
        self.loop.stop()
        if self.server is not None:
            self.server.close()

    def start(self, port_number):
        for s_name in ALL_SIGNALS:
            ALL_SIGNALS[s_name].connect(self.receiver)
        coro = self.loop.create_server(
            self.build_protocol, '127.0.0.1', port_number)
        self.server = self.loop.run_until_complete(coro)

    def receiver(self, signal=None, sender=None, **kwargs):
        if len(self.clients) > 0:
            j_sig = RPCSignal(kwargs["name"], kwargs["attrs"])
            buf = j_sig.to_json().encode('utf-8') + DELIMITER
            for client in self.clients:
                client.send_buffer(buf)

    def set_signals(self, connector):
        self.clients.append(connector)

    def close_signals(self, connector):
        if connector in self.clients:
            self.clients.remove(connector)

    def close(self):
        self.project.close()
