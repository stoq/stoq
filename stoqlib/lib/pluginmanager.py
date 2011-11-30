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
    """A class responsible for administrating plugins

    This class is responsible for administrating plugins, like,
    controlling which one is available/installed/actived or not.
    @important: Never instantialize this class. Always use
    """

    implements(IPluginManager)

    def __init__(self):
        self._plugins = {}
        self._active_plugins = {}
        self._plugin_descriptions = {}

        self._read_plugin_descriptions()

    #
    # Properties
    #

    @property
    def available_plugins_names(self):
        """A list of names of all available plugins"""
        return self._plugin_descriptions.keys()

    @property
    def installed_plugins_names(self):
        """A list of names of all installed plugins"""
        return [installed_plugin.plugin_name for installed_plugin in
                InstalledPlugin.select(connection=get_connection())]

    @property
    def active_plugins_names(self):
        """A list of names of all active plugins"""
        return self._active_plugins.keys()

    #
    # Private
    #

    def _read_plugin_descriptions(self):
        for path in library.get_resource_paths('plugin'):
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
        log.info("Loading plugin %s" % (plugin_name, ))
        imp.load_module(plugin_name, fp, pathname, description)

        assert plugin_name in self._plugins

    #
    # Public API
    #

    def get_plugin(self, plugin_name):
        """Returns a plugin by it's name

        @param plugin_name: the plugin's name
        @returns: the L{IPlugin} implementation of the plugin
        """
        if not plugin_name in self._plugin_descriptions:
            raise PluginError("%s plugin not found" % (plugin_name, ))

        if not plugin_name in self._plugins:
            self._import_plugin(self._plugin_descriptions[plugin_name])

        return self._plugins[plugin_name]

    def register_plugin(self, plugin):
        """Registers a plugin on manager

        This needs to be called by every plugin, or else, the manager
        won't know it's existence. It's usually a good idea to
        use L{register_plugin} function on plugin code, so the
        plugin will be registered as soon as it's module gets read
        by python.

        @param plugin: the L{IPlugin} implementation of the plugin
        """
        if not IPlugin.providedBy(plugin):
            raise TypeError("The object %s does not implement IPlugin "
                            "interface" % (plugin, ))
        self._plugins[plugin.name] = plugin

    def activate_plugin(self, plugin_name):
        """Activates a plugin

        This will activate the C{plugin}, calling it's C{activate}
        method and possibly doing some extra logic (e.g. logging).
        @important: Always activate a plugin using this method because
            the manager keeps track of all active plugins. Else you
            probably will activate the same plugin twice, and that
            probably won't be good :)

        @param plugin: the L{IPlugin} implementation of the plugin
        """
        if self.is_active(plugin_name):
            raise PluginError("Plugin %s is already active" % (plugin_name, ))

        plugin = self.get_plugin(plugin_name)
        log.info("Activating plugin %s" % (plugin_name, ))
        plugin.activate()
        self._active_plugins[plugin_name] = plugin

    def install_plugin(self, plugin_name):
        """Install and enable a plugin

        @important: Calling this makes a plugin installed, but, it's
            your responsability to activate it!

        @param plugin: the L{IPlugin} implementation of the plugin
        """
        # Try to get the plugin first. If it was't registered yet,
        # PluginError will be raised.
        plugin = self.get_plugin(plugin_name)

        if plugin_name in self.installed_plugins_names:
            raise PluginError("Plugin %s is already installed on database"
                              % (plugin_name, ))

        trans = new_transaction()
        InstalledPlugin(connection=trans,
                        plugin_name=plugin_name,
                        plugin_version=0)
        trans.commit(close=True)

        migration = plugin.get_migration()
        if migration:
            migration.apply_all_patches()

    def activate_installed_plugins(self):
        """Activate all installed plugins

        A helper method to activate all installed plugins in just one
        call, without having to get and activate one by one.
        """
        # FIXME: Get intersection to avoid trying to activate a plugin that
        #        isn't available. We should do something to remove such ones.
        for plugin_name in (set(self.installed_plugins_names) &
                            set(self.available_plugins_names)):
            self.activate_plugin(plugin_name)

    def is_active(self, plugin_name):
        """Returns if a plugin with a certain name is active or not.

        @returns: True if the given plugin name is active, False otherwise.
        """
        return plugin_name in self.active_plugins_names

    def is_installed(self, plugin_name):
        """Returns if a plugin with a certain name is installed or not

        @returns: True if the given plugin name is active, False otherwise.
        """
        return plugin_name in self.installed_plugins_names


def register_plugin(plugin_class):
    """Registers a plugin on IPluginManager

    Just a convenience function that can be added at the end of each
    plugin class definition to register it on manager.

    @param plugin_class: class to register, must implement L{IPlugin}
    """
    manager = get_plugin_manager()
    manager.register_plugin(plugin_class())


def get_plugin_manager():
    """Provides and returns the plugin manager

    @attention: Try to always use this instead of getting the utillity
        by hand, as that could not have been provided before.

    @returns: an L{PluginManager} instance
    """
    manager = get_utility(IPluginManager, None)
    if not manager:
        manager = PluginManager()
        provide_utility(IPluginManager, manager)

    return manager
