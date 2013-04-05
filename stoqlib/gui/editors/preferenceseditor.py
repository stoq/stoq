# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

"""Editors for user preferences"""

import gio
import gtk

from stoqlib.api import api
from stoqlib.gui.editors.baseeditor import BaseEditor, BaseEditorSlave
from stoqlib.gui.editors.shortcutseditor import ShortcutsEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _PrefField(object):
    def __init__(self, pref):
        self.pref = pref

    def __set__(self, obj, value):
        obj._set_preference(self.pref, value)

    def __get__(self, obj, class_):
        if obj is None:
            return
        return obj._get_preference(self.pref)


class _PreferencesModel(object):

    #
    #  Properties
    #

    language = _PrefField('user-locale')
    toolbar_style = _PrefField('toolbar-style')
    spreadsheet = _PrefField('spreadsheet-action')

    #
    #  Private
    #

    def _get_preference(self, pref_name):
        return api.user_settings.get(pref_name, None)

    def _set_preference(self, pref_name, value):
        api.user_settings.set(pref_name, value)


class PreferencesEditor(BaseEditor):
    """An editor for managing preferences in a tab style"""

    gladefile = 'PreferencesEditor'
    model_type = _PreferencesModel
    model_name = _('Preferences')
    size = (600, 400)
    proxy_widgets = ['toolbar_style',
                     'language',
                     'spreadsheet']

    def __init__(self, store, *args, **kwargs):
        BaseEditor.__init__(self, store, *args, **kwargs)
        self._setup_widgets()

    #
    #  Public API
    #

    def add_extra_tab(self, tab_name, slave_class, *args, **kwargs):
        """Add an extra tab on preferences

        :param tab_name: the name of the tab
        :param slave_class: the slave that will be attached to the new tab
        :param args: additional args to slave
        :param kwargs: additional kwargs to slave
        """
        event_box = gtk.EventBox()
        event_box.set_border_width(6)
        self.preferences_notebook.append_page(event_box,
                                              gtk.Label(tab_name))

        slave = slave_class(*args, **kwargs)
        if isinstance(slave, BaseEditorSlave):
            main_dialog = slave.main_dialog
        else:
            main_dialog = slave
        # Hide both ok and cancel button. We could just hide footer, but
        # there are some functional buttons we don't want to hide.
        main_dialog.ok_button.hide()
        main_dialog.cancel_button.hide()

        self.attach_slave(tab_name, slave, event_box)
        event_box.show()

    #
    #  BaseEditor Hooks
    #

    def create_model(self, store):
        return _PreferencesModel()

    def setup_proxies(self):
        self._prefill_toolbar_style_combo()
        self._prefill_language_combo()
        self._prefill_spreadsheet()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def setup_slaves(self):
        self._setup_extra_tabs()

    #
    #  Private
    #

    def _setup_widgets(self):
        self.preferences_notebook.set_show_tabs(True)
        self.preferences_notebook.set_show_border(True)
        self.preferences_notebook.set_tab_label(self.general_tab,
                                                gtk.Label(_('General')))
        # Hide cancel button as the model isn't on a db store and
        # therefore there's nothing to rollback.
        self.main_dialog.cancel_button.hide()

    def _setup_extra_tabs(self):
        for tab_name, slave, args, kwargs in [
                (_('Shortcuts'), ShortcutsEditor, [], {})]:
            self.add_extra_tab(tab_name, slave, *args, **kwargs)

    def _prefill_toolbar_style_combo(self):
        self.toolbar_style.prefill([
            (_("System default"), None),
            (_("Icons only"), 'icons'),
            (_("Text only"), 'text'),
            (_("Both"), 'both'),
            (_("Both horizontal (default)"), 'both-horizontal'),
        ])

    def _prefill_language_combo(self):
        self.language.prefill([
            (_("System default"), None),
            (_("English"), 'en'),
            (_("English (Australia)"), 'en_AU'),
            (_("English (United Kingdom)"), 'en_GB'),
            (_("English (United States)"), 'en_US'),
            (_("Portuguese"), 'pt'),
            (_("Portuguese (Brazil)"), 'pt_BR'),
        ])

    def _prefill_spreadsheet(self):
        app_info = gio.app_info_get_default_for_type(
            'application/vnd.ms-excel', False)

        options = [(_("Ask (default)"), None)]
        if app_info:
            options.append((_("Open with %s") % app_info.get_name(), 'open'))

        options.append((_("Save to disk"), 'save'))
        self.spreadsheet.prefill(options)
