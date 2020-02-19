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

import os
import logging
import shlex
import subprocess
import zipfile
import tempfile
import shutil
from pynetem import NetemError
from pynetem.topology import TopologieManager

TOPOLOGY_FILE = "network.ini"


def create_project(prj_path):
    # create an empty project
    with zipfile.ZipFile(prj_path, mode="w") as net_zip:
        net_zip.writestr(TOPOLOGY_FILE, """
[config]
image_dir = images
config_dir = configs

[nodes]

[switches]

[bridges]
""")


class NetemProject(object):

    def __init__(self, daemon, netid, prj_path):
        self.__id = netid
        self.daemon = daemon
        self.prj_path = prj_path
        self.tmp_folder = tempfile.mkdtemp(prefix=netid)
        with zipfile.ZipFile(prj_path) as prj_zip:
            prj_zip.extractall(path=self.tmp_folder)

        # init topology
        topology_file = os.path.join(self.tmp_folder, TOPOLOGY_FILE)
        if not os.path.isfile(topology_file):
            raise NetemError("Project %s does not contain "
                             "a topology file" % prj_path)
        self.topology = TopologieManager(self.__id, topology_file)

    def get_id(self):
        return self.__id

    def get_path(self):
        return self.prj_path

    def get_status(self):
        return {
            "project": {
                "path": self.prj_path,
                "running": self.topology.is_loaded
            },
            "nodes": self.topology.get_nodes_status()
        }

    def load_topology(self):
        self.topology.load()

    def get_topology_file(self):
        return os.path.join(self.tmp_folder, TOPOLOGY_FILE)

    def is_topology_modified(self):
        # sometime project is corrupted
        # in this case, do not test topology
        if not zipfile.is_zipfile(self.prj_path):
            return False

        tmp_file = os.path.join(self.tmp_folder, TOPOLOGY_FILE)
        with open(tmp_file) as tmp_hd:
            tmp_content = tmp_hd.read().encode("utf-8")
        with zipfile.ZipFile(self.prj_path, mode="r") as prj_zip:
            with prj_zip.open(TOPOLOGY_FILE) as rec_file:
                rec_content = rec_file.read()
        return tmp_content != rec_content

    def save(self):
        with zipfile.ZipFile(self.prj_path, mode="w") as prj_zip:
            self.topology.save()
            for root, dirs, files in os.walk(self.tmp_folder):
                for f in files:
                    f_path = os.path.join(root, f)
                    arch_path = self.__strip_path(f_path)
                    prj_zip.write(f_path, arcname=arch_path)

    def save_config(self, conf_path):
        self.topology.save(conf_path=conf_path)

    def close(self):
        try:
            self.topology.close()
        except Exception as ex:
            logging.error("Unable to close the project properly: %s" % ex)
        # what happen before, clean the project
        self.daemon.clean(self.get_id())
        shutil.rmtree(self.tmp_folder)

    def __command(self, cmd_line):
        args = shlex.split(cmd_line)
        ret = subprocess.call(args)
        if ret != 0:
            msg = "Unable to execute command %s" % (cmd_line,)
            raise NetemError(msg)

    def __strip_path(self, path):
        return path.replace(self.tmp_folder, "")
