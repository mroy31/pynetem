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
from pynetem.ui.config import NetemConfig
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

    def __init__(self, p2p_sw, image_dir, img_type, name, node_config):
        super(QEMUInstance, self).__init__(name)

        self.p2p_sw = p2p_sw
        self.memory = "memory" in node_config and node_config["memory"] or None
        self.need_acpi = "acpi" not in node_config and True \
                         or node_config.as_bool("acpi")
        self.shell_process = None
        self.telnet_port = node_config.as_int("console")
        self.img = os.path.join(image_dir, "%s.img" % name)
        self.interfaces = []
        self.capture_processes = {}

        if not os.path.isfile(self.img):
            base_img_dir = NetemConfig.instance().get("general", "image_dir")
            b_img = os.path.join(base_img_dir, "%s.img" % img_type)
            cmd = "%s create -f qcow2 -b %s %s" % (QEMU_IMG, b_img, self.img)
            self._command(cmd)

    def get_type(self):
        return "node.qemu"

    def get_memory(self):
        if self.memory is not None:
            return self.memory
        return NetemConfig.instance().get("qemu", "memory")

    def __add_if(self, peer_type, peer_instance, peer_if=None):
        self.interfaces.append({
            "mac": parm_attribution.get_mac_address(),
            "peer": peer_type,
            "peer_instance": peer_instance,
            "peer_if": peer_if,
            "tap": None,
            "vlan_id": len(self.interfaces),
        })

    def add_null_if(self):
        self.__add_if("switch", None)

    def add_sw_if(self, sw_instance):
        self.__add_if("switch", sw_instance)

    def add_node_if(self, node_instance, if_number):
        self.__add_if("node", node_instance, peer_if=if_number)

    def __sw_if_cmdline(self, if_config):
        cmd_line = "-net nic,macaddr=%s,model=e1000,"\
                   "vlan=%d" % (if_config['mac'], if_config['vlan_id'])
        if if_config['peer_instance'] is not None:
            sw_type = if_config["peer_instance"].get_type()
            if sw_type == "switch.vde":
                sw_name = if_config["peer_instance"].get_name()
                cmd_line += " -net vde,sock=%s,"\
                            "vlan=%d" % ("/tmp/%s.ctl" % sw_name,
                                         if_config['vlan_id'])
            elif sw_type == "switch.ovs":
                # create tap and attach to ovswitch
                tap_name = self.gen_ifname(if_config["vlan_id"],
                                           if_config["peer_instance"])
                self.daemon.tap_create(tap_name, os.environ["LOGNAME"])
                if_config["peer_instance"].attach_interface(tap_name)
                cmd_line += " -net tap,ifname=%s,script=no,"\
                            "downscript=no,"\
                            "vlan=%d" % (tap_name, if_config["vlan_id"])
                if_config["tap"] = tap_name
        return cmd_line

    def __node_if_cmdline(self, if_config):
        cmd_line = "-net nic,macaddr=%s,model=e1000,"\
                   "vlan=%d" % (if_config['mac'], if_config['vlan_id'])
        # create tap and attach to ovswitch
        tap_name = self.gen_ifname(if_config["vlan_id"],
                                   if_config["peer_instance"],
                                   if_config["peer_if"])
        self.daemon.tap_create(tap_name, os.environ["LOGNAME"])
        self.p2p_sw.add_connection(tap_name)
        cmd_line += " -net tap,ifname=%s,script=no,"\
                    "downscript=no,vlan=%d" % (tap_name, if_config["vlan_id"])
        if_config["tap"] = tap_name
        return cmd_line

    def get_interface_cmdline(self):
        result = []
        for i in self.interfaces:
            if i["peer"] == "switch":
                result.append(self.__sw_if_cmdline(i))
            if i["peer"] == "node":
                result.append(self.__node_if_cmdline(i))
        return " ".join(result)

    def capture(self, if_number):
        if len(self.interfaces) > if_number:
            if if_number in self.capture_processes:
                process = self.capture_processes[if_number]
                if process.poll() is None:
                    raise NetemError("Capture process is already running")

            if_obj = self.interfaces[if_number]
            if if_obj["peer"] == "switch" \
                    and if_obj["peer_instance"] is not None:
                sw_type = if_obj["peer_instance"].get_type()
                if sw_type == "switch.ovs":
                    if_name = if_obj["tap"]
                elif sw_type == "switch.vde":
                    if_name = if_obj["peer_instance"].get_tap_name()
                    if if_name is None:
                        raise NetemError("Unable to launch capture, no tap"
                                         "if exists on this switch")
                cmd_ln = shlex.split("wireshark -k -i %s" % if_name)
                self.capture_processes[if_number] = subprocess.Popen(cmd_ln)
            elif if_obj["peer"] == "node":
                if_name = if_obj["tap"]
                cmd_ln = shlex.split("wireshark -k -i %s" % if_name)
                self.capture_processes[if_number] = subprocess.Popen(cmd_ln)
            else:
                raise NetemError("%s: interface %d is not "
                                 "plugged" % (self.name, if_number))
        else:
            raise NetemError("%s: interface %d does not "
                             "exist" % (self.name, if_number))

    def set_if_state(self, if_number, state):
        raise NetemError("ifstate command is not supported for qemu nodes.")

    def open_shell(self, debug=False):
        if self.shell_process is not None \
                and self.shell_process.poll() is None:
            raise NetemError("The console is already opened")
        term_cmd = NetemConfig.instance().get("general", "terminal") % {
            "title": self.name,
            "cmd": "telnet localhost %d" % self.telnet_port,
        }
        args = shlex.split(term_cmd)
        self.shell_process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
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
        for k in self.capture_processes:
            self.capture_processes[k].terminate()
            self.capture_processes = {}
        for if_c in self.interfaces:
            if if_c["tap"] is not None:
                if if_c["peer"] == "switch":
                    if_c["peer_instance"].detach_interface(if_c["tap"])
                elif if_c["peer"] == "node":
                    self.p2p_sw.delete_connection(if_c["tap"])
                self.daemon.tap_delete(if_c["tap"])

    def save(self):
        pass  # nothing to do
