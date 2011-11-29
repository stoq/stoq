# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
from nfeui import NFeUI
from utils import get_cities_by_name


class NFePlugin(object):
    implements(IPlugin)
    name = 'nfe'
    has_product_slave = False

    def __init__(self):
        self.ui = None

    def get_migration(self):
        environ.add_resource('nfecsv', os.path.join(plugin_root, 'csv'))
        environ.add_resource('nfesql', os.path.join(plugin_root, 'sql'))
        return PluginSchemaMigration(self.name, 'nfesql', ['*.sql', '*.py'])

    def get_tables(self):
        return [('nfedomain', ['NFeCityData'])]

    def activate(self):
        self.ui = NFeUI()

    #
    # Accessors
    #

    def get_matching_cities(self, city):
        return get_cities_by_name(city)


register_plugin(NFePlugin)
