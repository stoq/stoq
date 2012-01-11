# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009-2011 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Dialogs for payment method management"""

import platform

import gtk
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.list import Column

from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.lib.parameters import is_developer_mode
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import yesno
from stoqlib.lib.pluginmanager import get_plugin_manager

_ = stoqlib_gettext


class _PluginModel(object):
    """Temporary model for plugin objects. This model is a minimal
    representation of the plugin information.

    @ivar name: The plugin name.
    @ivar is_active: True if the plugin is installed, False otherwise.
    """

    def __init__(self, plugin_name, is_active):
        self.name = plugin_name
        self.is_active = is_active

    def can_activate(self):
        return not self.is_active


class PluginManagerDialog(BasicDialog):
    size = (500, 350)
    title = _(u'Plugin Manager')
    help_section = 'plugin'

    def __init__(self, conn):
        BasicDialog.__init__(self)
        header = _(u'Select the plugin you want to activate and click in '
                    'the apply button.')
        self._initialize(hide_footer=False, size=PluginManagerDialog.size,
                         title=PluginManagerDialog.title, header_text=header)

        self.conn = conn
        self._manager = get_plugin_manager()
        self._setup_widgets()

    def _update_widgets(self):
        selected = self.klist.get_selected()
        assert selected

        self.ok_button.set_sensitive(selected.can_activate())

    def _setup_widgets(self):
        self.set_ok_label(_(u'Activate'), gtk.STOCK_APPLY)
        self.ok_button.set_sensitive(False)
        plugins = []

        for name in sorted(self._manager.available_plugins_names):
            # FIXME: Remove when magento plugin is functional for end users
            if not is_developer_mode() and name == 'magento':
                continue
            if platform.system() == 'Windows':
                if name in ['ecf', 'tef']:
                    continue
            plugins.append(_PluginModel(name, name in
                                        self._manager.installed_plugins_names))

        self.klist = ObjectList(self._get_columns(), plugins,
                                gtk.SELECTION_BROWSE)
        self.klist.connect("selection-changed",
                           self._on_klist__selection_changed)
        self.main.remove(self.main.get_child())
        self.main.add(self.klist)
        self.klist.show()

    def _get_columns(self):
        return [Column('name', title=_('Plugin'), data_type=str,
                       expand=True),
                Column('is_active', title=_('Active'), data_type=bool)]

    def _enable_plugin(self, plugin_model):
        plugin_name = plugin_model.name
        self._manager.install_plugin(plugin_name)
        self._manager.activate_plugin(plugin_name)

    #
    # BasicDialog
    #

    def confirm(self):
        msg = _("Are you sure you want activate this plugin?\n"
                "Please note that, once activated you will not "
                "be able to disable it.")
        response = yesno(msg, gtk.RESPONSE_NO,
                         _("Not now"), _("Activate plugin"))
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
