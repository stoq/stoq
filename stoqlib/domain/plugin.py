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


# pylint: enable=E1101

from storm.expr import Eq, Ne
from stoqlib.domain.base import Domain
from stoqlib.database.properties import UnicodeCol, IntCol, BLOBCol


class InstalledPlugin(Domain):
    """This object represent an installed and activated plugin.

    :cvar plugin_name: name of the plugin
    :cvar plugin_version: version of the plugin, if the version is `None`,
                          it means that the plugin still need to be enabled
                          later.
    """
    __storm_table__ = 'installed_plugin'

    plugin_name = UnicodeCol()
    plugin_version = IntCol()

    @classmethod
    def get_plugin_names(cls, store):
        """Fetchs a list of installed plugin names
        :param store: a store
        :returns: list of strings
        """
        return [p.plugin_name for p in store.find(cls,
                                                  Ne(cls.plugin_version, None))]

    @classmethod
    def create(cls, store, plugin_name):
        """Add a valid InstalledPlugin into the database

        This method sets plugin_version to 0 if a there is a Pre-Installed
        Plugin on the database, or creates a InstalledPlugin with
        plugin_version set to 0 if None is available.
        """
        from stoqlib.lib.pluginmanager import PluginError

        # First, try to find a plugin with the given name
        plugin = store.find(cls, plugin_name=plugin_name).one()

        # If no plugin was found, just create it and return it
        if plugin is None:
            return cls(store=store,
                       plugin_name=plugin_name,
                       plugin_version=0)

        # If the plugin was found and its plugin_version is None it is a
        # pre-installed plugin, so just set its plugin_version to 0
        if plugin.plugin_version is None:
            plugin.plugin_version = 0
            return plugin

        # If none of the other cases were true, the plugin is already installed
        raise PluginError("Plugin %s is already installed." % (plugin_name, ))

    @classmethod
    def get_pre_plugin_names(cls, store):
        """Returns a list of pre enabled plugin names
        :param store: a store
        :returns: names of the pre enabled plugins
        """
        query = Eq(cls.plugin_version, None)
        return [p.plugin_name for p in store.find(cls, query)]


class PluginEgg(Domain):
    """A cache for plugins eggs"""

    __storm_table__ = 'plugin_egg'

    plugin_name = UnicodeCol()
    egg_content = BLOBCol(default=None)
    egg_md5sum = UnicodeCol(default=None)
