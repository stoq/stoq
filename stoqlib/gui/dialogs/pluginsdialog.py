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
from kiwi.ui.objectlist import ObjectList, Column

from stoqlib.api import api
from stoqlib.database.runtime import get_default_store
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.stockicons import STOQ_PLUGIN
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import yesno, info
from stoqlib.lib.pluginmanager import get_plugin_manager

_ = stoqlib_gettext


class _PluginModel(object):
    """Temporary model for plugin objects. This model is a minimal
    representation of the plugin information.

    :attribute name: The plugin name.
    :attribute is_active: True if the plugin is installed, False otherwise.
    """

    def __init__(self, plugin_name, is_active, desc):
        self.name = plugin_name
        self.is_active = is_active
        self.desc = desc
        self.icon = STOQ_PLUGIN

    def can_activate(self):
        return not self.is_active

    @property
    def description(self):
        return '<b>%s</b>\n%s' % (api.escape(self.desc.long_name),
                                  self.desc.description)


class PluginManagerDialog(BasicDialog):
    size = (500, 350)
    title = _(u'Plugin Manager')
    help_section = 'plugin'

    def __init__(self, store):
        header = _(u'Select the plugin you want to activate and click in '
                   'the apply button.')
        BasicDialog.__init__(self, hide_footer=False,
                             size=PluginManagerDialog.size,
                             title=PluginManagerDialog.title,
                             header_text=header)
        self.store = store
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
            if platform.system() == 'Windows':
                if name in ['ecf', 'tef']:
                    continue

            desc = self._manager.get_description_by_name(name)
            plugins.append(_PluginModel(name, name in
                                        self._manager.installed_plugins_names,
                                        desc))

        self.klist = ObjectList(self._get_columns(), plugins,
                                gtk.SELECTION_BROWSE)
        self.klist.set_headers_visible(False)
        self.klist.connect("selection-changed",
                           self._on_klist__selection_changed)
        self.main.remove(self.main.get_child())
        self.main.add(self.klist)
        self.klist.show()

    def _get_columns(self):
        return [Column('is_active', title=_('Active'), width=20, data_type=bool),
                Column('icon', data_type=str, width=24, use_stock=True,
                       icon_size=gtk.ICON_SIZE_BUTTON),
                Column('description', data_type=str, expand=True,
                       use_markup=True)]

    def _enable_plugin(self, plugin_model):
        plugin_name = plugin_model.name
        # This should not really be necessary, but there may be deadlocks when
        # activating the plugin. See bug 5272
        default_store = get_default_store()
        default_store.commit()
        self._manager.install_plugin(plugin_name)
        self._manager.activate_plugin(plugin_name)

        info(_("The plugin %s was successfully activated. Please, restart all "
               "Stoq instances connected to this installation.") % (plugin_name, ))

    #
    # BasicDialog
    #

    def confirm(self):
        msg = _("Are you sure you want activate this plugin?\n"
                "Please note that, once activated you will not "
                "be able to disable it.")
        response = yesno(msg, gtk.RESPONSE_NO,
                         _("Activate plugin"), _("Not now"))

        if response:
            self._enable_plugin(self.klist.get_selected())
            self.close()

    #
    # Callbacks
    #

    def _on_klist__selection_changed(self, list, data):
        self._update_widgets()


if __name__ == '__main__':  # pragma nocover
    ec = api.prepare_test()
    run_dialog(PluginManagerDialog, None, ec.store)
