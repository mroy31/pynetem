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

import locale

__version__ = "0.1.1"

class JunemuleError(Exception):
    """General purpose error structure."""

    def __init__(self, *args, **kwargs):
        super(JunemuleError, self).__init__(*args, **kwargs)
        if len(args) > 0:
            self._message = args[0]

    # Handle unicode messages, what Exceptions cannot. See Python issue at
    # http://bugs.python.org/issue2517
    def __str__(self):
        if type(self._message) is unicode:
            try:
                return str(self._message.encode(locale.getpreferredencoding()))
            except UnicodeError:
                # perharps prefered encoding not correctly set, force to UTF-8
                return str(self._message.encode("utf-8"))
        else:
            return str(self._message)

    def __unicode__(self):
        if type(self._message) is unicode:
            return self._message
        else:
            return unicode(self._message)


# vim: ts=4 sw=4 expandtab
