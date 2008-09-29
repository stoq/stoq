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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##

import imp
import os

from kiwi.desktopparser import DesktopParser
from kiwi.component import get_utility, provide_utility
from kiwi.log import Logger
from zope.interface import implements

from stoqlib import library
from stoqlib.database.runtime import get_connection, new_transaction
from stoqlib.domain.plugin import InstalledPlugin
from stoqlib.lib.interfaces import IPlugin, IPluginManager

log = Logger('stoq.pluginmanager')


class PluginError(Exception):
    pass


class PluginDescription(object):
    def __init__(self, config, filename):
        self.name = os.path.basename(os.path.dirname(filename))
        self.entry = config.get('Plugin', 'Module')
        self.filename = filename

    @property
    def dirname(self):
        return os.path.dirname(self.filename)


class PluginManager(object):
    implements(IPluginManager)
    def __init__(self):
        self._plugins = {}
        self._plugin_descriptions = {}
        self._plugin_paths = []

        for path in library.get_resource_paths('plugin'):
            self._plugin_paths.append(path)

        self._read_plugin_descriptions()

    #
    # Private
    #

    def _read_plugin_descriptions(self):
        for path in self._plugin_paths:
            for dirname in os.listdir(path):
                if dirname == '.svn':
                    continue
                plugindir = os.path.join(path, dirname)
                if not os.path.isdir(plugindir):
                    continue
                filename = os.path.join(plugindir, dirname + '.plugin')
                if not os.path.exists(filename):
                    continue
                self._register_plugin_description(filename)

    def _register_plugin_description(self, filename):
        dp = DesktopParser()
        dp.read(filename)
        desc = PluginDescription(dp, filename)
        self._plugin_descriptions[desc.name] = desc

    def _import_plugin(self, plugin_desc):
        plugin_name = plugin_desc.name
        fp, pathname, description = imp.find_module(plugin_desc.entry,
                                                    [plugin_desc.dirname])
        log.info("Loading plugin %s" % (plugin_name,))
        imp.load_module(plugin_name, fp, pathname, description)

        assert plugin_name in self._plugins

    def _get_plugin(self, plugin_name):
        if not plugin_name in self._plugin_descriptions:
            raise PluginError("%s plugin not found" % (plugin_name,))

        if not plugin_name in self._plugins:
            self._import_plugin(self._plugin_descriptions[plugin_name])

        return self._plugins[plugin_name]

    #
    # Public API
    #

    def register_plugin(self, plugin):
        """Registers a plugin, this is normally called in the plugin itself
        @param plugin: the plugin
        @param type: an object implementing L{IPlugin}
        """
        if not IPlugin.providedBy(plugin):
            raise TypeError
        self._plugins[plugin.name] = plugin

    def activate_plugins(self):
        """Activates all enabled plugins
        """
        log.info("Activating plugins")
        installed_plugins = InstalledPlugin.select(connection=get_connection())
        for installed_plugin in installed_plugins:
            plugin = self._get_plugin(installed_plugin.plugin_name)
            plugin.activate()

    def enable_plugin(self, plugin_name):
        """Enables a plugin.
        This makes sure that the plugin is inserted into the database
        and that it always will be loaded on startup
        @param plugin_name: The name of the plugin
        """
        plugin = self._get_plugin(plugin_name)
        trans = new_transaction()
        if InstalledPlugin.selectOneBy(plugin_name=plugin_name,
                                       connection=trans):
            trans.close()
            return
        InstalledPlugin(connection=trans,
                        plugin_name=plugin_name,
                        plugin_version=1)
        trans.commit(close=True)

        migration = plugin.get_migration()
        if migration:
            migration.apply_all_patches()

    def get_active_plugins(self):
        """Gets a list of all active/enabled plugins
        @returns: a sequence of plugins
        """
        for p in InstalledPlugin.select(connection=get_connection()):
            yield self._get_plugin(p.plugin_name)

    def has_plugin(self, plugin_name):
        """Verify if the plugin is available or not.
        @param plugin_name: name of plugin
        @returns: True or False
        """
        return plugin_name in self._plugin_descriptions

    def get_plugin_names(self):
        """Gets a list of plugin names of available plugins.
        @returns: list of plugin names.
        """
        return self._plugin_descriptions.keys()


def register_plugin(plugin_class):
    """Registers a plugin, a convenience function
    for getting the plugin manager and calling regiser_plugin
    @param plugin_class: class to register, must implement L{IPlugin}
    """
    manager = get_utility(IPluginManager)
    manager.register_plugin(plugin_class())

def provide_plugin_manager():
    """Provides the plugin manager, this can only be called once
    """
    manager = PluginManager()
    provide_utility(IPluginManager, manager)
    return manager
