#!/usr/bin/python3
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
import shutil
from distutils.core import setup
from distutils.command.clean import clean as distutils_clean
import pynetem


def force_unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def force_rmdir(path):
    try:
        shutil.rmtree(path)
    except OSError:
        pass


class netem_clean(distutils_clean):
    def run(self):
        distutils_clean.run(self)

        commands = list(self.distribution.command_obj.values())
        for cmd in commands:
            if hasattr(cmd, 'clean'):
                cmd.clean()

        force_unlink('MANIFEST')
        force_rmdir('build')
        force_rmdir('docs/build')


if __name__ == "__main__":
    setup(
        name="pynetem", version=pynetem.__version__,
        url="http://mroy31.dyndns.org/~roy/repositories.git/pynetem",
        description="Network simulator based on qemu/docker and vde/ovs",
        author="Mikael Royer",
        author_email="mickael.royer@recherche.enac.fr",
        license="GNU GPL v2",
        scripts=["pynetem-emulator", "pynetem-daemon"],
        packages=["pynetem", "pynetem.check", "pynetem.daemon",
                  "pynetem.wrapper", "pynetem.wrapper.node",
                  "pynetem.wrapper.switch", "pynetem.ui"],
        package_data={
            'pynetem.ui': ['defaults.conf']
        },
        cmdclass={
            "clean": netem_clean,
        }
    )
