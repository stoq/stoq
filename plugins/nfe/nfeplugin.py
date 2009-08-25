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
## Author(s):   George Y. Kussumoto     <george@async.com.br>
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


class NFePlugin(object):
    implements(IPlugin)
    name = 'nfe'

    #TODO: implement nfe domain first

    def get_migration(self):
        environ.add_resource('nfecsv', os.path.join(plugin_root, 'csv'))
        environ.add_resource('nfetemplates',
                             os.path.join(plugin_root, 'templates'))
        environ.add_resource('nfesql', os.path.join(plugin_root, 'sql'))
        return PluginSchemaMigration(self.name, 'nfesql', ['*.sql', '*.py',])

    def activate(self):
        pass


register_plugin(NFePlugin)
