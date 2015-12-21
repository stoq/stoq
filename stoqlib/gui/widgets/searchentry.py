# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
"""A gadget that will transform a regular entry in an advanced entry, that
allows the user to select the object using a regular search."""

import gtk
from kiwi.ui.entry import ENTRY_MODE_DATA

from stoqlib.api import api
from stoqlib.database.queryexecuter import QueryExecuter
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.search.searchfilters import StringSearchFilter
from stoqlib.gui.search.personsearch import BasePersonSearch, ClientSearch
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.translation import stoqlib_gettext as _


class SearchEntryGadget(object):
    find_tooltip = _('Search')
    edit_tooltip = _('Edit')
    new_tooltip = _('Create')

    def __init__(self, entry, store, model, model_property,
                 search_columns, search_class, parent, run_editor=None):
        """
        This gadget modifies a ProxyEntry turning it into a replacement for
        ProxyComboEntry.

        When instanciated, the gadget will remove the entry from the editor, add
        a gtk.HBox on its place, and re-attach the entry to the newly created
        hbox. This hbox will also have two buttons: One for showing the related
        search dialog (or search editor), and another one to add/edit a new
        object.

        There are a few advantages in using this instead of a combo:

        - There is no need to prefill the combo with all the options, which can
          be very slow depending on the number of objects.
        - This allows the user to use a better search mechanism, allowing him to
          filter using multiple keywords and even candidade keys (like a client
          document)

        :param entry: The entry that we should modify
        :param store: The store that will be used for database queries
        :param model: The model that we are updating
        :param model_property: Property name of the model that should be updated
        :param search_columns: Columns that will be queried when the user
          activates the entry
        :param search_class: Class of the search editor/dialog that will be
          displayed when more than one object is found
        :param parent: The parent that should be respected when running other
          dialogs
        :param find_tooltip: the tooltip to use for the search button
        :param edit_tooltip: the tooltip to use for the edit button
        :param new_tooltip: the tooltip to use for the new button
        """
        self.store = store
        self._entry = entry
        self._model = model
        # TODO: Maybe this two variables shoulb be a list of properties of the
        # table instead of strings
        self._model_property = model_property
        self._search_columns = search_columns
        self._search_class = search_class
        self._parent = parent
        self._on_run_editor = run_editor

        # TODO: Respect permission manager
        self._editor_class = search_class.editor_class

        # If the search is for a person, the editor is called with a special
        # function
        if issubclass(search_class, BasePersonSearch):
            self._is_person = True
        else:
            self._is_person = False

        self._setup_widgets()
        self._setup_callbacks()

    #
    #   Private API
    #

    def _setup_widgets(self):
        self._replace_widget()

        # Add the two buttons
        self.find_button = self._create_button(gtk.STOCK_FIND)
        self.edit_button = self._create_button(gtk.STOCK_NEW)
        can_edit = self._entry.get_editable() and self._entry.get_sensitive()
        self.find_button.set_sensitive(can_edit)

        self.find_button.set_tooltip_text(self.find_tooltip)
        self.edit_button.set_tooltip_text(self.new_tooltip)

        # the entry needs a completion to work in MODE_DATA
        self._completion = gtk.EntryCompletion()
        self._entry.set_completion(self._completion)
        self._entry.set_mode(ENTRY_MODE_DATA)

        initial_value = getattr(self._model, self._model_property)
        self.set_value(initial_value)

        # The filter that will be used. This is not really in the interface. We
        # will just use it to perform the search.
        self._filter = StringSearchFilter('')
        self._executer = QueryExecuter(self.store)
        self._executer.set_search_spec(self._search_class.search_spec)
        self._executer.set_filter_columns(self._filter, self._search_columns)

    def _create_button(self, stock):
        image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.set_image(image)
        button.show()
        self.box.pack_start(button, False, False)
        return button

    def _replace_widget(self):
        # This will remove the entry, add a hbox in the entry old position, and
        # reattach the entry to this box. The box will then be used to add two
        # new buttons (one for searching, other for editing/adding new objects
        container = self._entry.parent

        # stolen from gazpacho code (widgets/base/base.py):
        props = {}
        for pspec in gtk.container_class_list_child_properties(container):
            props[pspec.name] = container.child_get_property(self._entry, pspec.name)

        self.box = gtk.HBox()
        self.box.show()
        self._entry.reparent(self.box)
        container.add(self.box)

        for name, value in props.items():
            container.child_set_property(self.box, name, value)

    def _setup_callbacks(self):
        self._entry.connect('activate', self._on_entry_activate)
        self._entry.connect('changed', self._on_entry_changed)
        self._entry.connect('notify::sensitive', self._on_entry_sensitive)
        self.find_button.connect('clicked', self._on_find_button__clicked)
        self.edit_button.connect('clicked', self._on_edit_button__clicked)

    def _run_search(self):
        text = self._entry.get_text()
        value = run_dialog(self._search_class, self._parent, self.store,
                           double_click_confirm=True,
                           initial_string=text)
        if value:
            self.set_value(self.get_model_obj(value))

    def _run_editor(self):
        with api.new_store() as store:
            model = getattr(self._model, self._model_property)
            model = store.fetch(model)
            if self._on_run_editor:
                value = self._on_run_editor(store, model)
            elif self._is_person:
                value = run_person_role_dialog(self._editor_class, self._parent, store, model)
            else:
                value = run_dialog(self._editor_class, self._parent, store, model)

        if value:
            value = self.store.fetch(self.get_model_obj(value))
            self.set_value(value)

    #
    #   Public API
    #

    def set_value(self, obj):
        if obj:
            display_value = obj.get_description()
            self._entry.prefill([(display_value, obj)])
            self.update_edit_button(gtk.STOCK_INFO, self.edit_tooltip)
        else:
            display_value = ''
            self._entry.prefill([])
            self.update_edit_button(gtk.STOCK_NEW, self.new_tooltip)

        self._value = obj
        self._entry.update(obj)
        self._entry.set_text(display_value)

    def get_model_obj(self, obj):
        return obj

    def update_edit_button(self, stock, tooltip):
        image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        self.edit_button.set_image(image)
        self.edit_button.set_tooltip_text(tooltip)

    #
    #   Callbacks
    #

    def _on_entry_activate(self, entry):
        if not self._entry.get_property('editable'):
            return
        text = entry.get_text()
        self._filter.set_state(text)
        state = self._filter.get_state()
        results = list(self._executer.search([state])[:2])
        if len(results) != 1:
            # XXX: If nothing is found in the query above, runing the search
            # will cause the query to be executed a second time. Refactor the
            # search to allow us to send the initial results avoiding this
            # second query.
            return self._run_search()

        # This means the search returned only one result.
        self.set_value(self.get_model_obj(results[0]))

    def _on_entry_changed(self, entry):
        # If the user edits the value in the entry, it invalidates the value.
        if self._value:
            self.set_value(None)

    def _on_entry_sensitive(self, entry, pspec):
        can_edit = self._entry.get_editable() and self._entry.get_sensitive()
        self.find_button.set_sensitive(can_edit)
        self.edit_button.set_sensitive(can_edit)

    def _on_edit_button__clicked(self, entry):
        self._run_editor()

    def _on_find_button__clicked(self, entry):
        self._run_search()


class ClientSearchEntryGadget(SearchEntryGadget):
    find_tooltip = _('Search for clients')
    edit_tooltip = _('Edit the selected client')
    new_tooltip = _('Create a new client')

    def __init__(self, entry, store, model, parent, model_property='client',
                 search_class=ClientSearch, run_editor=None):
        search_columns = ['name', 'cpf', 'phone_number', 'mobile_number']
        SearchEntryGadget.__init__(self, entry=entry, store=store, model=model,
                                   parent=parent, model_property=model_property,
                                   search_class=search_class,
                                   search_columns=search_columns,
                                   run_editor=run_editor)

    def get_model_obj(self, obj):
        return obj and obj.client

    def set_editable(self, can_edit):
        self.find_button.set_sensitive(can_edit)
        self.edit_button.set_sensitive(can_edit)
        self._entry.set_property('editable', can_edit)
