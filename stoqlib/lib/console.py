#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Stoq Team   <stoq-devel@async.com.br>
##
""" A debug session for domain objects.  """

import code
import datetime
import readline
import rlcompleter
rlcompleter # pyflakes

from stoqlib.api import api
from stoqlib.database.tables import get_table_types

from stoq import version as stoq_version


class Console(object):
    def __init__(self):
        self.conn = api.get_connection()
        self.trans = api.new_transaction()
        self.ns = {}

    def populate_namespace(self, bare):
        for table in get_table_types():
            self.ns[table.__name__] = table

        self.ns['conn'] = self.conn
        self.ns['trans'] = self.trans
        self.ns['sysparam'] = api.sysparam
        self.ns['api'] = api

        if not bare:
            self.ns['branch'] = api.get_current_branch(self.conn)
            self.ns['station'] = api.get_current_station(self.conn)
            self.ns['now'] = datetime.datetime.now
            self.ns['today'] = datetime.date.today

            for name in ('sqlobject', 'sqlobject.sqlbuilder',
                         'stoqlib.database.runtime',
                         'stoqlib.lib.interfaces',
                         'stoqlib.domain.interfaces'):
                mod = __import__(name, {}, {}, ' ')
                self.ns.update(mod.__dict__)

    def get_console_banner(self):
        db_string = '%s on %s:%s (%s)' % (api.db_settings.dbname,
                                          api.db_settings.address,
                                          api.db_settings.port,
                                          api.db_settings.rdbms)
        return 'Stoq version %s, connected to %s' % (
            stoq_version, db_string)

    def interact(self, vars=None):
        if vars is not None:
            self.ns.update(vars)

        readline.parse_and_bind("tab: complete")

        banner = self.get_console_banner()
        code.interact(local=self.ns, banner=banner)

    def execute(self, filename):
        execfile(filename, self.ns)
