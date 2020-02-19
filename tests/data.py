# pynetem: network emulator
# Copyright (C) 2019 Mickael Royer <mickael.royer@recherche.enac.fr>
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
import zipfile
import string
import random

random.seed()


def gen_rnd_string(min_size=8, max_size=12):
    assert min_size <= max_size
    size = random.choice(range(min_size, max_size+1))
    return "".join(random.choices(string.ascii_letters, k=size))


def create_project(nodes, switches=[], bridges=[]):
    prj_name = os.path.join()