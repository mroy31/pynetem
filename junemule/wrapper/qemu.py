# Deejayd, a media player daemon
# Copyright (C) 2012-2013 Mickael Royer <mickael.royer@gmail.com>
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

import subprocess, os
import logging, shlex

from junemule.wrapper import _BaseInstance
from junemule import JunemuleError

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
    mem = 128
    qemu_bin = "qemu-system-i386"
    qemu_img_bin = "qemu-img"

    def __init__(self, config, name, img, base_img, telnet_port):
        super(QEMUInstance, self).__init__(config, name)
        self.telnet_port = telnet_port
        self.interfaces = []

        self.img = img
        if not os.path.isfile(self.img): # create it
            base_img_dir = config.get("general", "image_dir")
            base_img = os.path.join(base_img_dir, "%s.img" % base_img)

            command = "%s create -f qcow2 -b %s %s" \
                    % (self.qemu_img_bin, base_img, img)
            self._command(command)

    def add_if(self, switch_name):
        if switch_name == "__null__": switch_name = None
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
            result.append("-net nic,macaddr=%s,model=e1000,vlan=%d"\
                    % (i['mac'], i['vlan_id']))
            if i['name'] is not None:
                result.append("-net vde,sock=%s,vlan=%d" \
                        % ("/tmp/%s.ctl" % i['name'], i['vlan_id']))
        return " ".join(result)

    def cmd_line(self):
        raise NotImplementedError

    def start(self):
        if self.is_started():
            return

        logging.debug(self.cmd_line())
        args = shlex.split(self.cmd_line())
        self.process = subprocess.Popen(args ,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                shell=False)


class RouterInstance(QEMUInstance):
    mem = 192

    def cmd_line(self):
        return "qemu-system-i386 -enable-kvm -hda %(img)s -m %(mem)s -nographic -serial telnet::%(telnet_port)d,server,nowait %(interfaces)s" % {
                    "img": self.img,
                    "mem": self.mem,
                    "telnet_port": self.telnet_port,
                    "interfaces": self.get_interface_cmdline()
                }

class HostInstance(QEMUInstance):

    def cmd_line(self):
        return "qemu-system-i386 -no-acpi -enable-kvm -hda %(img)s -m %(mem)s -nographic -serial telnet::%(telnet_port)d,server,nowait %(interfaces)s" % {
                    "img": self.img,
                    "mem": self.mem,
                    "telnet_port": self.telnet_port,
                    "interfaces": self.get_interface_cmdline()
                }

# vim: ts=4 sw=4 expandtab
