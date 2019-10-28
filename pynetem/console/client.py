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

import asyncio
import logging
from pynetem.server.rpc import loads_response
from pynetem.server.protocol import DELIMITER
from pynetem import NetemError


class NetemClientProtocol(asyncio.Protocol):

    def __init__(self, cmd, on_signal, on_answer, loop):
        self.transport = None
        self.loop = loop
        self.cmd = cmd
        self.msg_chunks = ""
        self.next_msg = ""
        self.on_answer = on_answer
        self.on_signal = on_signal

    def connection_made(self, transport):
        self.transport = transport
        cmd = self.cmd.to_json()
        logging.debug("Send cmd '%s' to prj server" % cmd)
        transport.write(cmd.encode("utf-8")+DELIMITER)

    def connection_lost(self, exc):
        logging.debug("Close connection to server")
        self.loop.stop()

    def data_received(self, msg_chunk):
        msg_chunk = msg_chunk.decode("utf-8")
        delimiter = DELIMITER.decode("utf-8")
        logging.debug("Receive data '%s'" % msg_chunk)

        def split_msg(msg, index):
            return (msg[0:index], msg[index + len(delimiter):len(msg)])

        self.msg_chunks += msg_chunk
        try:
            index = self.msg_chunks.index(delimiter)
        except ValueError:
            return
        else:
            (rawmsg, self.next_msg) = split_msg(self.msg_chunks, index)
            self.msg_chunks = ""
            if self.answer_received(rawmsg):
                return self.transport.close()

            while self.next_msg != '':
                try:
                    index = self.next_msg.index(delimiter)
                except ValueError:
                    self.msg_chunks = self.next_msg
                    self.next_msg = ""
                    break
                else:
                    (rawmsg, self.next_msg) = split_msg(self.next_msg, index)
                    if self.answer_received(rawmsg):
                        return self.transport.close()

    def answer_received(self, rawmsg):
        try:
            ans = loads_response(rawmsg)
        except NetemError:
            logging.error("Unable to parse server answer : %s" % rawmsg)
            self.on_answer(None)
        else:
            if ans["type"] == "signal":
                self.on_signal(ans)
                return False

            self.on_answer(ans)
        return True
