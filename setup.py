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

from distutils.core import setup
import junemule

if __name__ == "__main__":
    setup( name="junemule", version=junemule.__version__,
           url="http://mroy31.dyndns.org/~roy/projects/junemule",
           description="Network simulator based en kvm and vde",
           author="Mikael Royer",
           author_email="mickael.royer@recherche.enac.fr",
           license="GNU GPL v2",
           scripts=["junos-emulator","junemule-daemon"],
           packages=["junemule","junemule.wrapper","junemule.ui",],
           package_data={'junemule.ui': ['defaults.conf'],},
        )

# vim: ts=4 sw=4 expandtab
