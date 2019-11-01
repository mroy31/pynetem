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

from cmd2 import Cmd
import re
import os
import asyncio
import subprocess
import shlex
from pynetem import NetemError
from pynetem.ui.config import NetemConfig
from pynetem.console.client import NetemClientProtocol
from pynetem.server.rpc import RPCRequest
from pynetem.utils import cmd_check_output
from pynetem.console.color import GREEN, ORANGE, DEFAULT
from pynetem.console.spinner import Spinner


def netmem_cmd(reg_exp=None, catch_error=True):
    def cmd_decorator(func):
        def cmd_func(self, arg):
            # first, valid arguments
            match_object = None
            if reg_exp is None and arg.strip() != "":
                self.perror("this command does not require any argument.")
                return
            elif reg_exp is not None:
                match_object = re.match(reg_exp, arg.strip())
                if match_object is None:
                    self.perror("argument for this cmd does not respect the "
                                "following syntax: %s" % reg_exp)
                    return

            try:
                if match_object is None:
                    return func(self)
                return func(self, *match_object.groups())
            except NetemError as err:
                if not catch_error:
                    raise err
                self.perror("%s" % err)
            except Exception as err:
                if not catch_error:
                    raise err
                self.perror("unhandle error happens, %s" % err)

        cmd_func.__name__ = func.__name__
        cmd_func.__doc__ = func.__doc__
        return cmd_func

    return cmd_decorator


class NetemConsole(Cmd):
    intro = '\nWelcome to network emulator. Type help or ? to list commands.\n'
    prompt = '[net-emulator] '

    def __init__(self, s_port):
        self.allow_cli_args = False
        self.s_port = s_port
        self.current_response = None
        self.spinner = None
        self.loop = asyncio.get_event_loop()

        super(NetemConsole, self).__init__()
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0.0"
        self.__open_display()

    def pinfo(self, msg):
        self.poutput(GREEN + msg + DEFAULT)

    def pwarning(self, msg):
        self.poutput(ORANGE + msg + DEFAULT)

    def __open_display(self):
        try:
            cmd_check_output("xhost si:localuser:root")
        except Exception as ex:
            self.perror("Unable to disable X11 access control -> %s" % ex)

    def __close_display(self):
        try:
            cmd_check_output("xhost -si:localuser:root")
        except Exception:
            pass

    def __on_answer(self, ans):
        self.current_response = ans

    def __on_signal(self, sig):
        if sig["name"] == "node":
            attrs = sig["attrs"]
            if attrs["state"] == "loading":
                if self.spinner is not None:
                    self.spinner.error()
                text = {
                    "node": "Start all nodes of the topology ... ",
                    "switch_bridge": "Start all switches/bridges ... ",
                    "config": "Load configuration of junos routers ... ",
                }[attrs["type"]]
                self.spinner = Spinner(text)
            elif attrs["state"] == "error" and self.spinner is not None:
                self.spinner.error(attrs["msg"])
                self.spinner = None
            elif attrs["state"] == "loaded" and self.spinner is not None:
                self.spinner.stop()
                self.spinner = None
        elif sig["name"] == "watch":
            attrs = sig["attrs"]
            if attrs["state"] == "error":
                if self.spinner is not None and self.spinner.is_running():
                    self.spinner.error()
                self.perror(attrs["msg"])

    def __send_cmd(self, cmd_name, args=[]):
        request = RPCRequest(cmd_name, args)
        self.current_response = None

        coro = self.loop.create_connection(
            lambda: NetemClientProtocol(request, self.__on_signal,
                                        self.__on_answer, self.loop),
            '127.0.0.1',
            self.s_port
        )
        t = self.loop.create_task(coro)
        if not t.done():
            self.loop.run_forever()

        if self.current_response is None:
            raise NetemError("No valid answer has been received from server")
        if self.current_response["state"] == "error":
            raise NetemError(self.current_response["content"])

        return self.current_response["content"]

    def __command(self, cmd_line):
        args = shlex.split(cmd_line)
        ret = subprocess.call(args)
        if ret != 0:
            msg = "Unable to execute command %s" % (cmd_line,)
            raise NetemError(msg)

    def __spinner_cmd(self, text, cmd, args=[], color=DEFAULT):
        spinner = Spinner(text, color=color)
        try:
            self.__send_cmd(cmd, args=args)
        except Exception as ex:
            spinner.error(str(ex))
        else:
            spinner.stop()

    def __quit(self):
        if self.__send_cmd("isTopologyModified"):
            q = input("The topology has been modified, "
                        "are you you want to quit netem (Y/N): ")
            while q not in ("Y", "N"):
                q = input("Wrong answer, expect Y or N: ")
            if q == "N":
                return None
        self.__spinner_cmd(
            "Close the project, please wait ... ", "quit",
            color=ORANGE)
        self.__close_display()
        self.loop.close()
        return True

    def emptyline(self):
        # do nothing when an empty line is entered
        pass

    @netmem_cmd(catch_error=False)
    def do_quit(self):
        "Quit the network emulator"
        return self.__quit()

    @netmem_cmd(catch_error=False)
    def do_exit(self):
        "Quit the network emulator"
        return self.__quit()

    @netmem_cmd()
    def do_projectPath(self):
        "Display the path of the openning project"
        prj_path = self.__send_cmd("projectPath")
        self.poutput(os.path.abspath(prj_path))

    @netmem_cmd(catch_error=False)
    def do_run(self):
        """Check the project and start all nodes"""
        self.pinfo("Run the project, please wait ... ")
        self.__send_cmd("load")

    @netmem_cmd(catch_error=False)
    def do_save(self):
        """Save the project"""
        self.__spinner_cmd("Save the project, please wait ... ", "save")

    @netmem_cmd(reg_exp="^(\S+)$", catch_error=False)
    def do_config(self, conf_path):
        """Save configurations in a specific folder"""
        if not os.path.isdir(conf_path):
            self.perror("%s is not a valid path")
            return
        self.__spinner_cmd(
            "Save the config in %s, please wait ... " % conf_path,
            "config", args=[conf_path])

    @netmem_cmd()
    def do_check(self):
        """Check the network file"""
        if self.__send_cmd("check"):
            self.pinfo("Network file is OK")

    @netmem_cmd(reg_exp="^(\S+\.\w+)$")
    def do_capture(self, if_name):
        """Capture trafic on an interface"""
        self.__send_cmd("capture", args=[if_name])

    @netmem_cmd(catch_error=False)
    def do_reload(self):
        """Reload the project"""
        self.pinfo("Reload the project, please wait ... ")
        self.__send_cmd("reload")

    @netmem_cmd()
    def do_edit(self):
        """Edit the topology"""
        f_path = self.__send_cmd("topologyFile")
        cmd_line = "%s %s" % \
            (NetemConfig.instance().get("general", "editor"), f_path)
        self.__command(cmd_line)

    @netmem_cmd()
    def do_view(self):
        """View the topology"""
        f_path = self.__send_cmd("topologyFile")
        with open(f_path) as t_hd:
            self.poutput(t_hd.read())

    @netmem_cmd(reg_exp="^(\S+)$")
    def do_start(self, node_id):
        """Start nodes, you can specify node name or 'all'"""
        self.__send_cmd("start", args=[node_id])

    @netmem_cmd(reg_exp="^(\S+)$")
    def do_stop(self, node_id):
        """Stop nodes, you can specify node name or 'all'"""
        self.__send_cmd("stop", args=[node_id])

    @netmem_cmd(reg_exp="^(\S+)$")
    def do_restart(self, node_id):
        """Restart nodes in the network"""
        self.__send_cmd("restart", args=[node_id])

    @netmem_cmd()
    def do_status(self):
        """Display routeur/host status"""
        status = self.__send_cmd("status")
        p_state = status["project"]["running"] \
            and GREEN+"running"+DEFAULT or ORANGE+"stopped"+DEFAULT
        self.poutput("Project:\n\tpath: {}\n\tstate: {}\n".format(
            status["project"]["path"], p_state))

        if status["project"]["running"]:
            self.poutput("Nodes:\n")

            def format_node(n):
                n_state = n["isRunning"] \
                    and GREEN+"running"+DEFAULT or ORANGE+"stopped"+DEFAULT
                self.poutput("\t{}: {}\n".format(n["name"], n_state))
                if "interfaces" in n:
                    for if_obj in n["interfaces"]:
                        i_state = if_obj["isUp"] \
                            and GREEN+"up"+DEFAULT or ORANGE+"down"+DEFAULT
                        self.poutput("\t\t{}: {}\n".format(
                            if_obj["name"], i_state))

            for n in status["nodes"]:
                format_node(n)

    @netmem_cmd(reg_exp="^(\S+)$")
    def do_console(self, node_id):
        """Open a console for the given router/host"""
        self.__send_cmd("console", args=[node_id])

    @netmem_cmd(reg_exp="^(\S+)$")
    def do_debug(self, node_id):
        """Open a debug console (meaning bash) for the given router/host"""
        self.__send_cmd("debug", args=[node_id])

    @netmem_cmd(reg_exp="^(\S+\.[0-9]+) (up|down)$")
    def do_ifstate(self, if_name, state):
        """Enable/disable a node interface. The ifname have to
        follow this syntax : <node_id>.<if_number>"""
        self.__send_cmd("ifstate", args=[if_name, state])
