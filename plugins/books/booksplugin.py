# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import os
import sys

from kiwi.environ import environ
from zope.interface import implements

from stoqlib.database.migration import PluginSchemaMigration
from stoqlib.lib.interfaces import IPlugin
from stoqlib.lib.pluginmanager import register_plugin

plugin_root = os.path.dirname(__file__)
sys.path.append(plugin_root)

from booksui import BooksUI


class BooksPlugin(object):
    implements(IPlugin)
    name = 'books'
    has_product_slave = True

    def __init__(self):
        self.ui = None

    def get_migration(self):
        environ.add_resource('booksql', os.path.join(plugin_root, 'sql'))
        return PluginSchemaMigration(self.name, 'booksql', ['*.sql'])

    def get_tables(self):
        return [('bookdomain', ['PersonAdaptToPublisher', 'ProductAdaptToBook'])]

    def activate(self):
        environ.add_resource('glade', os.path.join(plugin_root, 'glade'))
        self.ui = BooksUI()

    #
    # Custom accessors
    #

    def get_product_slave_class(self):
        if self.ui is not None:
            return self.ui.get_book_slave()


register_plugin(BooksPlugin)
