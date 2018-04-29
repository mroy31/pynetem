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

import cmd
import re
from pynetem import NetemError
from pynetem.project import NetemProject
from pynetem.utils import get_exc_desc


def netmem_cmd(reg_exp=None, require_project=False):
    def cmd_decorator(func):
        def cmd_func(self, arg):
            # first, valid arguments
            match_object = None
            if reg_exp is None and arg.strip() != "":
                self.error("this command does not require any argument.")
                return
            elif reg_exp is not None:
                match_object = re.match(reg_exp, arg.strip())
                if match_object is None:
                    self.error("argument for this cmd does not respect the "
                               "following syntax: %s" % reg_exp)
                    return

            if require_project and self.current_project is None:
                self.error("this command requires a loaded project")
                return
            try:
                if match_object is None:
                    return func(self)
                return func(self, *match_object.groups())
            except NetemError as err:
                self.error("unable to execute cmd: %s" % err)
            except Exception as ex:
                self.error("unhandle exception raises, see traceback below")
                print(get_exc_desc())
                return self.close()

        cmd_func.__name__ = func.__name__
        cmd_func.__doc__ = func.__doc__
        return cmd_func

    return cmd_decorator


class NetemConsole(cmd.Cmd):
    intro = 'Welcome to network emulator. Type help or ? to list commands.\n'
    prompt = '[net-emulator] '

    def __init__(self, daemon, project=None):
        super(NetemConsole, self).__init__()
        self.daemon = daemon
        self.current_project = project

    def __quit(self):
        if self.current_project is not None:
            if self.current_project.is_topology_modified():
                q = input("The topology has been modified, "
                          "are you you want to quit netem (Y/N): ")
                while q not in ("Y", "N"):
                    q = input("Wrong answer, expect Y or N: ")
                if q == "N":
                    return None
            self.current_project.close()
        return True

    @netmem_cmd()
    def do_quit(self):
        "Quit the network emulator"
        return self.__quit()

    @netmem_cmd()
    def do_exit(self):
        "Quit the network emulator"
        return self.__quit()

    @netmem_cmd(reg_exp="^(\S+)$")
    def do_load(self, prj_path):
        """Load a pnet project"""
        if self.current_project is not None:
            self.current_project.close()
        self.current_project = NetemProject.load(self.daemon, prj_path)
        self.current_project.load_topology()

    @netmem_cmd(reg_exp="^(\S+)$")
    def do_create(self, prj_path):
        """Create a pnet project"""
        if self.current_project is not None:
            self.current_project.close()
        self.current_project = NetemProject.create(self.daemon, prj_path)

    @netmem_cmd(require_project=True)
    def do_save(self):
        """Save the project"""
        self.current_project.save()

    @netmem_cmd(require_project=True)
    def do_check(self):
        """Check the network file"""
        try:
            self.current_project.topology.check()
        except NetemError as err:
            print(err)
        else:
            print("Network file is OK")

    @netmem_cmd(reg_exp="^(\S+\.\w+)$", require_project=True)
    def do_capture(self, if_name):
        """Capture traffic on an interface"""
        self.current_project.topology.capture(if_name)

    @netmem_cmd(require_project=True)
    def do_reload(self):
        """Reload the project"""
        self.current_project.topology.reload()

    @netmem_cmd(require_project=True)
    def do_edit(self):
        """Edit the topology"""
        self.current_project.edit_topology()

    @netmem_cmd(require_project=True)
    def do_view(self):
        """View the topology"""
        self.current_project.view_topology()

    @netmem_cmd(reg_exp="^(\S+)$", require_project=True)
    def do_start(self, node_id):
        """Start nodes, you can specify node name or 'all'"""
        for node in self.__get_nodes(node_id):
            node.start()

    @netmem_cmd(reg_exp="^(\S+)$", require_project=True)
    def do_stop(self, node_id):
        """Stop nodes, you can specify node name or 'all'"""
        for node in self.__get_nodes(node_id):
            node.stop()

    @netmem_cmd(reg_exp="^(\S+)$", require_project=True)
    def do_restart(self, node_id):
        """Restart nodes in the network"""
        for node in self.__get_nodes(node_id):
            node.stop()
            node.start()

    @netmem_cmd(require_project=True)
    def do_status(self):
        """Display routeur/host status"""
        print(self.current_project.topology.status())

    @netmem_cmd(reg_exp="^(\S+)$", require_project=True)
    def do_console(self, node_id):
        """Open a console for the given router/host"""
        for node in self.__get_nodes(node_id):
            try:
                node.open_shell()
            except NetemError as err:
                print("WARNING: %s" % err)

    @netmem_cmd(reg_exp="^(\S+\.[0-9]+) (up|down)$", require_project=True)
    def do_ifstate(self, if_name, state):
        """Enable/disable a node interface. The ifname have to 
        follow this syntax : <node_id>.<if_number>"""
        self.current_project.topology.set_if_state(if_name, state)

    def close(self):
        if self.current_project is not None:
            self.current_project.close()
        return True

    def error(self, err):
        print("ERROR: {}".format(err))

    def __get_nodes(self, arg):
        if arg == "all":
            return self.current_project.topology.get_all_nodes()
        else:
            nodes = []
            n_ids = arg.split()
            for n_id in n_ids:
                node = self.current_project.topology.get_node(arg)
                if node is None:
                    print("Warning: node %s not found in the network" % n_id)
                else:
                    nodes.append(node)
            return nodes
