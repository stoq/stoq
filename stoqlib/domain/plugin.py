# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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


from stoqlib.domain.base import Domain
from stoqlib.database.orm import StringCol, IntCol


class InstalledPlugin(Domain):
    """This object represent an installed and activated plugin.

    @cvar plugin_name: name of the plugin
    @cvar plugin_version: version of the plugin
    """
    plugin_name = StringCol()
    plugin_version = IntCol()

    @classmethod
    def get_plugin_names(cls, conn):
        """Fetchs a list of installed plugin names
        @param conn: a connection
        @returns: list of strings
        """
        return [p.plugin_name for p in cls.select(connection=conn)]
