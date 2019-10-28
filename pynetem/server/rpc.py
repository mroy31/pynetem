# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
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

import json
import time
from pynetem import NetemError


class _RPC(object):

    def dump(self):
        raise NotImplementedError

    def to_json(self):
        return json.dumps(self.dump())


class RPCRequest(_RPC):
    """
    Build RPC Request
    """

    def __init__(self, method_name, params):
        self.method = method_name
        self.params = params
        self.id = int(time.time())

    def dump(self):
        return {"method": self.method, "params": self.params, "id": self.id}

    def get_id(self):
        return self.id


class RPCResponse(_RPC):
    """
    Build RPC Response
    """

    def __init__(self, id, state, content):
        self.id = id
        self.state = state
        self.content = content

    def dump(self):
        return {
            "type": "answer",
            "state": self.state,
            "content": self.content,
            "id": self.id
        }


class RPCSignal(_RPC):

    def __init__(self, signal_name, attrs):
        self.name = signal_name
        self.attrs = attrs

    def dump(self):
        return {
            "type": "signal",
            "name": self.name,
            "attrs": self.attrs,
            "id": None
        }


def loads_request(request, **kws):
    err = NetemError("Malformed request")
    try:
        unmarshalled = json.loads(request, **kws)
    except ValueError:
        raise err

    if (isinstance(unmarshalled, dict)):
        for key in ("method", "params", "id"):
            if key not in unmarshalled:
                raise err
        return unmarshalled
    raise err


def loads_response(response, **kws):
    err = NetemError("Malformed response")
    try:
        unmarshalled = json.loads(response, **kws)
    except ValueError:
        raise err

    if (isinstance(unmarshalled, dict)):
        for key in ("type", "id"):
            if key not in unmarshalled:
                raise err
        return unmarshalled
    raise err
