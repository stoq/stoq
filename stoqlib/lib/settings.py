# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Routines for parsing user configuration settings"""

import errno
import json
import os
from decimal import Decimal

from kiwi.log import Logger

from stoqlib.lib.osutils import get_application_dir

log = Logger('stoqlib.lib.settings')


def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


def _encode_object(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)

    raise TypeError(
        'Object of type %s with value of %r '
        'is not JSON serializable' % (type(obj), obj))


class UserSettings(object):
    domain = 'stoq'

    def __init__(self):
        self._root = {}
        self._read()

    def set(self, name, value):
        name = name.replace('_', '-')
        self._root[name.encode('utf-8')] = value

    def get(self, name, default=None):
        if not name in self._root:
            self.set(name, default)
        return self._root[name]

    def remove(self, name):
        del self._root[name]

    def items(self):
        return self._root.items()

    def flush(self):
        data = json.dumps(self._root,
                          indent=2,
                          sort_keys=True,
                          default=_encode_object)
        self._write(data)

    def get_filename(self):
        config_dir = get_application_dir(self.domain)
        return os.path.join(config_dir, 'settings')

    # Private

    def _read(self):
        filename = self.get_filename()
        try:
            fd = open(filename)
        except IOError, e:
            if e.errno == errno.ENOENT:
                self._migrate()
                return
            raise
        data = fd.read()
        fd.close()

        self._root = json.loads(data, object_hook=_decode_dict)

    def _write(self, data):
        filename = self.get_filename()
        fd = open(filename, 'w')
        try:
            fd.write(data + '\n')
        except OSError, e:
            # Permission denied, oh well.
            if e.errno == errno.EACCES:
                return
            # configuration directory missing, don't try to
            # recreate it as someone probably just removed it
            elif e.errno == errno.ENOENT:
                return
        fd.close()

    def _migrate(self):
        log.info("Migrating settings from Stoq.conf")

        # Migrate from old configuration settings
        from stoqlib.api import api

        self.set('hide-demo-warning',
                 api.config.get('UI', 'hide_demo_warning') == 'True')

        width = int(api.config.get('Launcher', 'window_width') or -1)
        height = int(api.config.get('Launcher', 'window_height') or -1)
        x = int(api.config.get('Launcher', 'window_x') or -1)
        y = int(api.config.get('Launcher', 'window_y') or -1)
        self.set('launcher-geometry',
                 dict(width=width, height=height, x=x, y=y))

        self.set('last-version-check',
                 api.config.get('General', 'last-version-check'))

        self.set('latest-version',
                 api.config.get('General', 'latest-version'))

        self.set('show-welcome-dialog',
                 api.config.get('General', 'show_welcome_dialog') != 'False')

        d = {}
        for k, v in api.config.items('Shortcuts'):
            d[k] = v
        self.set('shortcuts', d)

_settings = None


def get_settings():
    global _settings
    if _settings is None:
        _settings = UserSettings()
    return _settings

if __name__ == '__main__':
    s = UserSettings()
    columns = s.get('list-columns', [])
    columns.append({})
    columns.append({"foo": {}})
    s.flush()
