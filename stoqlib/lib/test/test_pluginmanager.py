# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

"""Test for stoqlib.lib.pluginmanager module"""

import contextlib
import io
import os
import shutil
import tempfile

import mock
from kiwi.python import Settable
from zope.interface import implementer

from stoqlib.database.runtime import new_store
from stoqlib.domain.plugin import InstalledPlugin, PluginEgg
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.interfaces import IPlugin, IPluginManager
from stoqlib.lib.pluginmanager import (PluginError, register_plugin,
                                       PluginManager, get_plugin_manager,
                                       PluginDescription)

plugin_desc = """
[Plugin]
Module=testplugin
Version=1
Name=Test plugin
Description=Test plugin description
Dependencies=test1, test2, test3
Replaces=test4
Authors=Stoq Team <stoq-devel@async.com.br>
Copyright=Copyright © 2007 Async Open Source
Website=http://www.stoq.com.br/
"""


@implementer(IPlugin)
class _TestPlugin(object):

    name = u'test_plugin'

    def __init__(self):
        self.reset()

    def reset(self):
        self.was_activated = False
        self.had_migration_gotten = False

    #
    #  IPlugin
    #

    def activate(self):
        self.was_activated = True

    def get_migration(self):
        self.had_migration_gotten = True
        return None


class _TestDependentPlugin(_TestPlugin):
    name = u'test_dependent_plugin'


class TestPluginDescription(DomainTest):

    @mock.patch('stoqlib.lib.pluginmanager.ZipFile')
    @mock.patch('stoqlib.lib.pluginmanager.is_zipfile')
    def test_constructor_is_egg(self, is_zipfile, ZipFile):
        ZipFile.return_value = mock.MagicMock()
        egg = ZipFile.return_value.__enter__.return_value
        egg.namelist.return_value = ['test.plugin']
        egg.open.return_value = io.BytesIO(plugin_desc)

        desc = PluginDescription('tmpfile', is_egg=True)

        is_zipfile.assert_called_once_with('tmpfile')
        self.assertEquals(desc.filename, 'test.plugin')
        self.assertEquals(desc.plugin_path, 'tmpfile')
        self.assertEquals(desc.long_name, 'Test plugin')


class TestPluginManager(DomainTest):

    def setUp(self):
        super(TestPluginManager, self).setUp()

        # Generate 2 instances of plugins that will be used for testing later.
        # '_dependent_plugin' will require 'independent_plugin' activation prior
        # to it's own.
        self._independent_plugin = _TestPlugin()
        self._dependent_plugin = _TestDependentPlugin()

        # Since the plugins are commited inside pluginmanager, try to remove
        # it first, or we will have problems if STOQLIB_TEST_QUICK is set.
        store = new_store()
        plugins = set(InstalledPlugin.get_plugin_names(store=self.store))
        expected = set([u'ecf', u'nfe', u'optical'])
        self.assertTrue(expected.issubset(plugins))

        ind_name = self._independent_plugin.name
        dep_name = self._dependent_plugin.name
        plugin_names = [ind_name, dep_name]

        test_plugins = store.find(InstalledPlugin,
                                  InstalledPlugin.plugin_name.is_in(plugin_names))
        for plugin in test_plugins:
            store.remove(plugin)
            store.commit()
        store.close()

        self._manager = get_plugin_manager()
        self._register_test_plugin()

    #
    #  Tests
    #

    @mock.patch('stoqlib.lib.pluginmanager.get_application_dir')
    @mock.patch('stoqlib.lib.pluginmanager.get_default_store')
    def test_create_eggs_cache(self, get_default_store, get_application_dir):
        temp_dir = tempfile.mkdtemp()
        try:
            get_default_store.return_value = self.store
            get_application_dir.return_value = temp_dir
            plugins_dir = os.path.join(temp_dir, 'plugins')
            os.makedirs(plugins_dir)

            with open(os.path.join(plugins_dir, 'foobar.egg'), 'wb') as f:
                f.write('wrong_content')

            with open(os.path.join(plugins_dir, 'foo.egg'), 'wb') as f:
                f.write('foo_content')

            PluginEgg(store=self.store, plugin_name=u'foobar',
                      egg_content='right_content',
                      egg_md5sum=u'e194544df936c31ebf9b4c2d4a6ef213')
            PluginEgg(store=self.store, plugin_name=u'foo',
                      egg_content='will_not_be_overwritten',
                      egg_md5sum=u'2b3bd636ec90eb39c3c171dd831b8c30')
            PluginEgg(store=self.store, plugin_name=u'bar',
                      egg_content='bar_content',
                      egg_md5sum=u'5f084b7281515082703bd903708c977a')

            self._manager._create_eggs_cache()

            # foobar didn't match md5 so it should have been overwritten
            with open(os.path.join(plugins_dir, 'foobar.egg')) as f:
                self.assertEqual(f.read(), 'right_content')

            # foo matched so it should be untouched
            with open(os.path.join(plugins_dir, 'foo.egg')) as f:
                self.assertEqual(f.read(), 'foo_content')

            # bar didn't exist so it should have been created
            with open(os.path.join(plugins_dir, 'bar.egg')) as f:
                self.assertEqual(f.read(), 'bar_content')

            self.assertEqual(set(self._manager.egg_plugins_names),
                             {'foobar', 'foo', 'bar'})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @mock.patch('stoqlib.lib.webservice.WebService.download_plugin')
    @mock.patch('stoqlib.lib.pluginmanager.new_store')
    def test_download_plugin(self, new_store, download_plugin):
        new_store.return_value = self.store

        self._manager.download_plugin(u'foo')
        args, kwargs = download_plugin.call_args
        plugin_name = args[0]
        callback = kwargs['callback']
        self.assertEqual(plugin_name, u'foo')

        with contextlib.nested(
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close'),
                mock.patch.object(self._manager, '_reload')):
            with tempfile.NamedTemporaryFile() as f:
                f.write('foo bar baz')
                f.flush()
                callback(f.name)

        plugin_egg = self.store.find(PluginEgg, plugin_name=u'foo').one()
        self.assertEqual(plugin_egg.egg_content, 'foo bar baz')
        self.assertEqual(plugin_egg.egg_md5sum,
                         u'ab07acbb1e496801937adfa772424bf7')

    def test_get_plugin_manager(self):
        # PluginManager should be a singleton
        self.assertEqual(self._manager, get_plugin_manager())
        self.assertEqual(id(self._manager), id(get_plugin_manager()))

        # Just check if it really provides IPluginManager
        self.assertTrue(IPluginManager.providedBy(self._manager))
        self.assertTrue(isinstance(self._manager, PluginManager))

    def test_get_plugin(self):
        p_name = _TestPlugin.name

        # Test if _TestPlugin is available
        self.assertTrue(p_name in self._manager.available_plugins_names)

        # Test getting _TestPlugin
        plugin = self._manager.get_plugin(_TestPlugin.name)
        self.assertTrue(isinstance(plugin, _TestPlugin))
        self.assertTrue(IPlugin.providedBy(plugin))

        # Test getting an inexistent plugin
        self.assertRaises(PluginError, self._manager.get_plugin, '_null_')

    def test_register_plugin(self):
        p_name = _TestPlugin.name
        p_name_ = p_name

        # Simulates a new plugin and try registering on manager
        p_name_ += '_'
        _TestPlugin.name = p_name_
        self.assertFalse(p_name_ in self._manager.available_plugins_names)
        self._manager._plugin_descriptions[p_name_] = p_name_
        self._manager.register_plugin(_TestPlugin())
        _TestPlugin.name = p_name
        self.assertTrue(p_name_ in self._manager.available_plugins_names)
        self.assertTrue(p_name_ in self._manager._plugins)

        # Simulates a new plugin and try registering using register_plugin
        p_name_ += '_'
        _TestPlugin.name = p_name_
        self.assertFalse(p_name_ in self._manager.available_plugins_names)
        self._manager._plugin_descriptions[p_name_] = p_name_
        register_plugin(_TestPlugin)
        _TestPlugin.name = p_name
        self.assertTrue(p_name_ in self._manager.available_plugins_names)
        self.assertTrue(p_name_ in self._manager._plugins)

        # Try to register to invalid plugins
        self.assertRaises(TypeError, self._manager.register_plugin, object())
        self.assertRaises(TypeError, register_plugin, object)

    def test_install_plugin(self):
        ind_name = self._independent_plugin.name
        dep_name = self._dependent_plugin.name

        ind_plugin = self._manager.get_plugin(ind_name)
        dep_plugin = self._manager.get_plugin(dep_name)

        # First it is needed to verify if both plugins are uninstalled
        self._check_plugin_installed(ind_plugin, False)
        self._check_plugin_installed(dep_plugin, False)

        # Both the dependend and independent plugins should not be
        # installed yet.
        self.assertFalse(ind_name in self._manager.installed_plugins_names)
        self.assertFalse(dep_name in self._manager.installed_plugins_names)

        self.assertFalse(ind_plugin.had_migration_gotten)
        self.assertFalse(dep_plugin.had_migration_gotten)

        self.assertFalse(self._manager.is_installed(ind_name))
        self.assertFalse(self._manager.is_installed(dep_name))

        # Install the dependent plugin, this should install both plugins
        self._manager.install_plugin(dep_name)

        # So it is checked if both plugins were installed
        self._check_plugin_installed(ind_plugin, True)
        self._check_plugin_installed(dep_plugin, True)

        # Plugins were installed, but its's activate method was not called yet
        self.assertFalse(ind_plugin.was_activated)
        self.assertFalse(dep_plugin.was_activated)

        # Test if both plugins are installed
        self.assertTrue(ind_name in self._manager.installed_plugins_names)
        self.assertTrue(dep_name in self._manager.installed_plugins_names)

        ind_plugin.reset()
        dep_plugin.reset()

    def test_activate_plugin(self):
        # Register first plugin description
        ind_name = self._independent_plugin.name
        dep_name = self._dependent_plugin.name

        ind_plugin = self._manager.get_plugin(ind_name)
        dep_plugin = self._manager.get_plugin(dep_name)

        # Both the dependend and independent plugins should not be
        # active yet.
        self._check_plugin_active(ind_plugin, False)
        self._check_plugin_active(dep_plugin, False)

        # This should activate both the dependent and the independent plugin
        self._manager.activate_plugin(dep_name)

        # Checking if in fact both plugins were activated
        self._check_plugin_active(ind_plugin, True)
        self._check_plugin_active(dep_plugin, True)

        # As the plugins were not installed, migration method was not executed
        self.assertFalse(ind_plugin.had_migration_gotten)
        self.assertFalse(dep_plugin.had_migration_gotten)

        # Test trying to activate again
        self.assertRaises(PluginError, self._manager.activate_plugin, ind_name)
        self.assertRaises(PluginError, self._manager.activate_plugin, dep_name)

        # Both plugins should remain active
        self._check_plugin_active(ind_plugin, True)
        self._check_plugin_active(dep_plugin, True)

        ind_plugin.reset()
        dep_plugin.reset()

    def test_activate_installed_plugins(self):
        fake_desc = mock.Mock()
        fake_desc.replaces = []
        fake_desc_c = mock.Mock()
        fake_desc_c.replaces = ['e']

        with contextlib.nested(
                mock.patch.dict(self._manager._plugin_descriptions,
                                {'a': fake_desc, 'b': fake_desc,
                                 'c': fake_desc_c, 'd': fake_desc,
                                 'e': fake_desc}),
                mock.patch.object(PluginManager, 'available_plugins_names'),
                mock.patch.object(PluginManager, 'installed_plugins_names'),
                mock.patch.object(PluginManager, 'activate_plugin')) as ctx:
            desc, available_plugins, installed_plugins, activate_plugin = ctx

            available_plugins.__get__ = mock.Mock(
                return_value=['a', 'b', 'c', 'd', 'e'])
            installed_plugins.__get__ = mock.Mock(
                return_value=['b', 'c', 'e'])

            self._manager.activate_installed_plugins()

            self.assertEqual(activate_plugin.call_count, 2)
            activate_plugin.assert_has_calls(
                [mock.call('b'), mock.call('c')])

            installed_plugins.__get__ = mock.Mock(
                return_value=['b', 'c', 'f'])

            with self.assertRaisesRegexp(
                    AssertionError,
                    ("Plugin 'f' not found on the system. "
                     "Available plugins: \['a', 'b', 'c', 'd', 'e'\]")):
                self._manager.activate_installed_plugins()

    #
    #  Private
    #

    def _check_plugin_active(self, plugin, status):
        self.assertEquals(plugin.was_activated, status)
        self.assertEquals(self._manager.is_active(plugin.name), status)

    def _check_plugin_installed(self, plugin, status):
        contained = plugin.name in self._manager.installed_plugins_names
        self.assertEquals(contained, status)

        self.assertEquals(plugin.had_migration_gotten, status)
        self.assertEquals(self._manager.is_installed(plugin.name), status)

    def _register_test_plugin(self):
        # Workaround to register _TestPlugin since it is not really a plugin.
        # Two plugins are instanced and setup to be used on this class' tests.
        # _dependend_plugin depends on _independent_plugin.
        ind_name = self._independent_plugin.name
        dep_name = self._dependent_plugin.name

        # Creating independent plugin description
        ind_desc = Settable(dependencies=[])

        # Description that sets the dependency to the independent plugin.
        dep_desc = Settable(dependencies=[ind_name])

        self._manager._plugin_descriptions[ind_name] = ind_desc
        self._manager._plugin_descriptions[dep_name] = dep_desc

        register_plugin(_TestPlugin)
        register_plugin(_TestDependentPlugin)
