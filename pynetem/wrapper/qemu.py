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
import logging
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


class QEMUInstance(_BaseInstance):
    instance_type = ""
    qemu_bin = "qemu-system-i386"
    qemu_img_bin = "qemu-img"

    def __init__(self, config, name, img, base_img, telnet_port):
        super(QEMUInstance, self).__init__(config, name)
        self.shell_process = None
        self.telnet_port = telnet_port
        self.interfaces = []

        self.img = img
        if not os.path.isfile(self.img):
            base_img_dir = config.get("general", "image_dir")
            base_img = os.path.join(base_img_dir, "%s.img" % base_img)

            command = "%s create -f qcow2 -b %s %s" \
                      % (self.qemu_img_bin, base_img, img)
            self._command(command)

    def get_memory(self):
        return self.config.get(self.instance_type, "memory")

    def add_if(self, switch_name):
        if switch_name == "__null__":
            switch_name = None
        self.interfaces.append(
            {
                "mac": parm_attribution.get_mac_address(),
                "name": switch_name,
                "vlan_id": len(self.interfaces),
            }
        )

    def get_interface_cmdline(self):
        result = []
        for i in self.interfaces:
            result.append("-net nic,macaddr=%s,model=e1000,vlan=%d"
                          % (i['mac'], i['vlan_id']))
            if i['name'] is not None:
                result.append("-net vde,sock=%s,vlan=%d"
                              % ("/tmp/%s.ctl" % i['name'], i['vlan_id']))
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


class RouterInstance(QEMUInstance):
    instance_type = "router"

    def build_cmd_line(self):
        return "qemu-system-i386 -enable-kvm -hda %(img)s -m %(mem)s "\
               "-nographic -serial telnet::%(telnet_port)d,server,nowait "\
               "%(interfaces)s" % {
                    "img": self.img,
                    "mem": self.get_memory(),
                    "telnet_port": self.telnet_port,
                    "interfaces": self.get_interface_cmdline()
                }


class HostInstance(QEMUInstance):
    instance_type = "host"

    def build_cmd_line(self):
        return "qemu-system-i386 -no-acpi -enable-kvm -hda %(img)s "\
               "-m %(mem)s -nographic -serial "\
               "telnet::%(telnet_port)d,server,nowait %(interfaces)s" % {
                    "img": self.img,
                    "mem": self.get_memory(),
                    "telnet_port": self.telnet_port,
                    "interfaces": self.get_interface_cmdline()
                }
