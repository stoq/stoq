# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   George Y. Kussumoto  <george@async.com.br>
##
##
""" Dialogs for payment method management"""

import gtk

from kiwi.component import get_utility
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.plugin import InstalledPlugin
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.lib.interfaces import IPluginManager
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import yesno

_ = stoqlib_gettext


class _PluginModel(object):
    """Temporary model for plugin objects. This model is a minimal
    representation of the plugin information.

    @cvar blacklist: The list of plugin names that can not be activated.
    @ivar name: The plugin name.
    @ivar is_active: True if the plugin is installed, False otherwise.
    """
    blacklist = ['ecf',]

    def __init__(self, plugin_name, conn):
        self.name = plugin_name
        self.is_active = self._get_plugin_is_active(conn)

    def _get_plugin_is_active(self, conn):
        return InstalledPlugin.selectOneBy(plugin_name=self.name) is not None

    def can_activate(self):
        activate = self.name in _PluginModel.blacklist
        if activate:
            return False
        return not self.is_active


class PluginManagerDialog(BasicDialog):
    size = (400, 400)
    title = _(u'Plugin Manager')

    def __init__(self, conn):
        BasicDialog.__init__(self)
        self._initialize(hide_footer=False, size=PluginManagerDialog.size,
                         title=PluginManagerDialog.title)
        self._manager = get_utility(IPluginManager)
        assert self._manager

        self.conn = conn
        self._setup_widgets()

    def _update_widgets(self):
        selected = self.klist.get_selected()
        assert selected

        self.ok_button.set_sensitive(selected.can_activate())

    def _setup_widgets(self):
        self.ok_button.set_label('gtk-apply')
        self.ok_button.set_sensitive(False)
        plugins = [_PluginModel(p, self.conn)
                            for p in self._manager.get_plugin_names()]
        self.klist = ObjectList(self._get_columns(), plugins,
                                gtk.SELECTION_BROWSE)
        self.klist.connect("selection-changed",
                           self._on_klist__selection_changed)
        self.main.remove(self.main.get_child())
        self.main.add(self.klist)
        self.klist.show()

    def _get_columns(self):
        return [Column('name', title=_('Plugin'), data_type=str,
                       expand=True, sorted=True),
                Column('is_active', title=_('Active'), data_type=bool)]

    def _enable_plugin(self, plugin):
        trans = new_transaction()
        self._manager.enable_plugin(plugin.name)
        finish_transaction(trans, True)
        trans.close()

    #
    # BasicDialog
    #

    def confirm(self):
        msg = _(u'Are you sure you want activate this plugin ?\nOnce '
                'activated you will not be able to disable it.')
        response = yesno(msg, gtk.RESPONSE_NO, _(u'Cancel'), _(u'Activate'))
        if response:
            self.retval = False
        else:
            self._enable_plugin(self.klist.get_selected())
            self.close()

    #
    # Callbacks
    #

    def _on_klist__selection_changed(self, list, data):
        self._update_widgets()
