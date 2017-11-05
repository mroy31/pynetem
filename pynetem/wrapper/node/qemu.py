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

import subprocess
import os
import shlex
from pynetem import NetemError
from pynetem.wrapper import _BaseInstance


class DynamicParmAttribution(object):
    base_mac = "00:aa:00:60:00:%02X"

    def __init__(self):
        self.last_given_mac = None

    def get_mac_address(self):
        if self.last_given_mac is None:
            self.last_given_mac = 1
        else:
            self.last_given_mac += 1
        return self.base_mac % self.last_given_mac


parm_attribution = DynamicParmAttribution()
QEMU_IMG = "qemu-img"


class QEMUInstance(_BaseInstance):
    instance_type = ""
    qemu_bin = "qemu-system-i386"

    def __init__(self, config, image_dir, name, node_config):
        super(QEMUInstance, self).__init__(config, name)

        self.memory = "memory" in node_config and node_config["memory"] or None
        self.need_acpi = "acpi" not in node_config and True or node_config.as_bool("acpi")
        self.shell_process = None
        self.telnet_port = node_config.as_int("console")
        self.img = os.path.join(image_dir, "%s.img" % name)
        self.interfaces = []

        if not os.path.isfile(self.img):
            base_img_dir = config.get("general", "image_dir")
            b_img = os.path.join(base_img_dir, "%s.img" % node_config["type"])
            cmd = "%s create -f qcow2 -b %s %s" % (QEMU_IMG, b_img, self.img)
            self._command(cmd)

    def get_memory(self):
        if self.memory is not None:
            return self.memory
        return self.config.get("qemu", "memory")

    def add_sw_if(self, sw_instance):
        if_parms = {
            "mac": parm_attribution.get_mac_address(),
            "peer": "switch",
            "sw_instance": sw_instance,
            "tap": None,
            "vlan_id": len(self.interfaces),
        }
        self.interfaces.append(if_parms)

    def __sw_if_cmdline(self, if_config):
        cmd_line = "-net nic,macaddr=%s,model=e1000,"\
                   "vlan=%d" % (if_config['mac'], if_config['vlan_id'])
        if if_config['sw_instance'] is not None:
            sw_type = if_config["sw_instance"].get_sw_type()
            if sw_type == "vde":
                sw_name = if_config["sw_instance"].get_name()
                cmd_line += " -net vde,sock=%s,"\
                            "vlan=%d" % ("/tmp/%s.ctl" % sw_name,
                                         if_config['vlan_id'])
            elif sw_type == "ovs":
                # create tap and attach to ovswitch
                tap_name = "%s.%s.%s" % (self.name, if_config["vlan_id"],
                                         if_config["sw_instance"].get_name())
                self._daemon_command("tap_create "
                                     "%s %s" % (tap_name,
                                                os.environ["LOGNAME"]))
                if_config["sw_instance"].attach_interface(tap_name)
                cmd_line += " -net tap,ifname=%s,script=no,"\
                            "downscript=no,vlan=%d" % (tap_name, if_config["vlan_id"])
                if_config["tap"] = tap_name
        return cmd_line

    def get_interface_cmdline(self):
        result = []
        for i in self.interfaces:
            if i["peer"] == "switch":
                result.append(self.__sw_if_cmdline(i))
        return " ".join(result)

    def open_shell(self):
        if self.shell_process is not None and self.shell_process.poll() is None:
            raise NetemError("The console is already opened")
        term_cmd = self.config.get("general", "terminal")
        cmd_line = "%s telnet localhost %d" % (term_cmd, self.telnet_port)
        args = shlex.split(cmd_line)
        self.shell_process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE,
                                              shell=False)

    def build_cmd_line(self):
        noacpi = "-no-acpi"
        if self.need_acpi:
            noacpi = ""
        return "qemu-system-i386 %(noacpi)s -enable-kvm -hda %(img)s "\
               "-m %(mem)s -nographic -serial "\
               "telnet::%(telnet_port)d,server,nowait %(interfaces)s" % {
                   "noacpi": noacpi,
                   "img": self.img,
                   "mem": self.get_memory(),
                   "telnet_port": self.telnet_port,
                   "interfaces": self.get_interface_cmdline()
                }

    def stop(self):
        super(QEMUInstance, self).stop()
        for if_c in self.interfaces:
            if if_c["tap"] is not None:
                if_c["sw_instance"].detach_interface(if_c["tap"])
                self._daemon_command("tap_delete %s" % if_c["tap"])