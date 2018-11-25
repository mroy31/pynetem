# pyNetmem, a network emulator
# Copyright (C) 2016-2018 Mickael Royer <mickael.royer@enac.fr>
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
import time
import telnetlib
from shlex import quote
from pynetem.ui.config import NetemConfig
from pynetem.wrapper.node.qemu import QEMUInstance, QEMU_IMG


class JunosTelnetClient(object):
    username = b"root"
    password = b"Juniper"
    hostname = b"generic"

    def __init__(self, name, port):
        self.name = name
        self.port = port

    def load(self, conf_file):
        # wait some seconds before initiate the connection
        time.sleep(3.0)
        try:
            tn = telnetlib.Telnet("localhost", port=self.port)
        except ConnectionRefusedError:
            logging.error("Unable to connect to %s router" % self.name)
            return

        # wait the router is ready
        tn.write(b"\n")
        tn.read_until(b"login: ")
        # login and load the configuration
        if os.path.isfile(conf_file):
            self.login(tn, self.hostname, cli=False)
            tmp_path = b"/tmp/netem.conf"
            with open(conf_file, "rb") as hd:
                data = hd.readlines()
                for l in data:
                    tn.write(
                        b"echo %s >> %s\n"
                        % (self.__format_line(l), tmp_path)
                    )
                    tn.read_until(b"%s@%s" % (self.username, self.hostname))
            tn.write(b"cli\n")
            tn.write(b"configure\n")
            tn.write(b"load override %s\n" % tmp_path)
        else:
            self.login(tn, self.hostname, cli=True)
            tn.write(b"configure\n")
            # just update the hostname
            tn.write(b"set system host-name %b\n" % self.name.encode('ascii'))
        tn.write(b"commit\n")
        # logout
        self.logout(tn)
        tn.close()

    def save(self, conf_file):
        try:
            tn = telnetlib.Telnet("localhost", port=self.port)
        except ConnectionRefusedError:
            logging.error("Unable to connect to %s router" % self.name)
            return
        self.logout(tn)
        self.login(tn, self.name.encode("ascii"))
        tn.write(b"configure\n")
        with open(conf_file, "bw") as hd:
            tn.write(b"save terminal\n")
            data = tn.read_until(b"Wrote")
            hd.write(self.__format_conf(data))
        tn.close()

    def logout(self, tn):
        while True:
            tn.write(b"\n")
            data = tn.read_until(b"login: ", timeout=0.5)
            if data.endswith(b"login: "):
                break
            else:
                tn.write(b"exit\n")

    def login(self, tn, router_name, cli=True):
        tn.write(self.username+b"\n")
        tn.read_until(b"Password:")
        tn.write(self.password+b"\n")
        tn.read_until(b"%s@%s" % (self.username, router_name))
        if cli:
            tn.write(b"cli\n")

    def __format_line(self, line):
        line = line.replace(b"\r", b"")
        line = line.replace(b"\n", b"")
        return quote(line.decode('ascii')).encode('ascii')

    def __format_conf(self, data):
        lines = data.split(b"\n")
        c_lines = []
        c_started = False
        for l in lines:
            if l.startswith(b"##"):
                c_started = True
            elif l.startswith(b"Wrote"):
                c_started = False
            if c_started:
                c_lines.append(l)
        return b"\n".join(c_lines)


class JunosInstance(QEMUInstance):

    def __init__(self, p2p_sw, prj_id, conf_dir, img_type, name, node_config):
        super(QEMUInstance, self).__init__(prj_id, name)

        self.conf_dir = conf_dir
        self.p2p_sw = p2p_sw
        self.kvm = NetemConfig.instance().getboolean("qemu", "enable_kvm")
        self.img_type = img_type
        self.memory = "memory" in node_config and node_config["memory"] or None
        self.need_acpi = "acpi" not in node_config and True \
                         or node_config.as_bool("acpi")
        self.shell_process = None
        self.telnet_port = node_config.as_int("console")
        self.img = os.path.join("/tmp", "%s-%s.img" % (prj_id, name))
        self.interfaces = []
        self.capture_processes = {}

    def __fmt_conf_path(self, conf_path):
        return os.path.join(
            conf_path or self.conf_dir,
            "%s.net.conf" % self.name
        )

    def get_type(self):
        return "node.junos"

    def start(self):
        base_img_dir = NetemConfig.instance().get("general", "image_dir")
        b_img = os.path.join(
            base_img_dir,
            "junos-pynetem-%s.img" % self.img_type
        )
        cmd = "%s create -f qcow2 -b %s %s" % (QEMU_IMG, b_img, self.img)
        self._command(cmd)

        super(JunosInstance, self).start()

    def load_configuration(self):
        j_client = JunosTelnetClient(self.name, self.telnet_port)
        j_client.load(self.__fmt_conf_path(None))

    def stop(self):
        super(JunosInstance, self).stop()
        if os.path.isfile(self.img):
            os.unlink(self.img)

    def save(self, conf_path=None):
        if self.shell_process is not None \
                and self.shell_process.poll() is None:
            self.shell_process.terminate()
        j_client = JunosTelnetClient(self.name, self.telnet_port)
        j_client.save(self.__fmt_conf_path(conf_path))
