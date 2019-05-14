#!/usr/bin/python3
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


import socket
import sys
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean pynetem project')
    parser.add_argument("-p", "--prefix", type=str, dest="prefix",
                        default="ntm", help="Specify the socket path")
    parser.add_argument("-s", "--socket", type=str, dest="s_path",
                        metavar="FILE", default="/tmp/pynetem-socket.ctl",
                        help="Specify the socket path")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(args.s_path)
    except socket.error as err:
        sys.exit("Error: unable to connect "
                 "to socket %s - %s" % (args.s_path, err))

    # send the clean command to pynetem daemon
    try:
        cmd = "clean %s" % args.prefix
        sock.sendall(cmd.encode("utf-8"))
        ans = sock.recv(1024).decode("utf-8").strip()
        if not ans.startswith("OK"):
            print("Error: daemon returns an error: %s" % ans)
        else:
            print("OK")
    finally:
        sock.close()
