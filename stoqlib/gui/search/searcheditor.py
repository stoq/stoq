# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Implementation of basic dialogs for searching data """

import gtk
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal
from storm.store import Store

from stoqlib.api import api
from stoqlib.database.orm import ORMObject
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SearchEditor(SearchDialog):
    """ Base class for a search "editor" dialog, that offers a 'new' and
    'edit' button on the dialog footer. The 'new' and 'edit' buttons will
    call 'editor_class' sending as its parameters a new connection and the
    object to edit for 'edit' button.

    This is also a subclass of SearchDialog and the same rules are required.

    Simple example:

    >>> from kiwi.ui.objectlist import Column
    >>> from stoqlib.domain.person import ClientView
    >>> from stoqlib.gui.editors.personeditor import ClientEditor

    >>> class ClientSearch(SearchEditor):
    ...     title = _("Client Search")
    ...     search_spec = ClientView
    ...     editor_class = ClientEditor
    ...     size = (465, 390)
    ...
    ...     def get_columns(self):
    ...         return [Column('name', _('Client name'), data_type=str, width=90),
    ...                 Column('status', _('Status'), data_type=str,
    ...                         expand=True)]

    This will create a new editor called ClientSearch:

      - It will be populated using the table ClientView.
      - The title of the editor is "Client Search".
      - To create new Client objects or to edit an existing Client object the
        ClientEditor table will be used, which needs to be a subclass of BaseEditor.
      - The size of the new dialog will be 465 pixels wide and 390 pixels high.
      - When displaying results, the verb client and clients will be used, eg:
        ``1 client`` or ``34 clients``.
      - The get_columns() methods is required to be implemented, otherwise
        there's no way to know which data is going to be displayed.
        get_columns must return a list of kiwi objectlist columns.
        In this case we will display two columns, brand and description.
        They will be fetched from the client object using the attribute brand or
        description. Both of them are strings (data_type=str), the width of
        the first column is 90 pixels and the second column is expanded so
        it uses the rest of the available width.

    """
    editor_class = None
    has_new_button = has_edit_button = True
    model_list_lookup_attr = 'id'

    def __init__(self, store, editor_class=None, interface=None,
                 search_spec=None, hide_footer=True,
                 title='', selection_mode=None,
                 hide_toolbar=False, double_click_confirm=False,
                 initial_string=''):
        """
        Create a new SearchEditor object.
        :param store:
        :param search_spec:
        :param editor_class:
        :param interface: The interface which we need to apply to the objects in
          kiwi list to get adapter for the editor.
        :param search_spec:
        :param hide_footer:
        :param title:
        :param selection_mode:
        :param hide_toolbar:
        :param double_click_confirm: If double click a item in the list should
          automatically confirm. Double click confirms takes precedence over
          editor_class (ie, if double_click_confirmis is True, it will
          confirm the dialog, instead of opening the editor).
        :param initial_string: The string that should be initialy filtered
        """

        if selection_mode is None:
            selection_mode = gtk.SELECTION_BROWSE
        self.interface = interface
        self._read_only = False
        self._message_bar = None

        SearchDialog.__init__(self, store, search_spec,
                              hide_footer=hide_footer, title=title,
                              selection_mode=selection_mode,
                              double_click_confirm=double_click_confirm,
                              initial_string=initial_string)

        self._setup_slaves()
        if hide_toolbar:
            self.accept_edit_data = False
            self._toolbar.get_toplevel().hide()
        else:
            if not (self.has_new_button or self.has_edit_button):
                raise ValueError("You must set hide_footer=False instead "
                                 "of disable these two attributes.")

            editor_class = editor_class or self.editor_class
            if not editor_class:
                raise ValueError('An editor_class argument is required')
            if not issubclass(editor_class, BaseEditor):
                raise TypeError("editor_class must be a BaseEditor subclass")
            self.editor_class = editor_class

            self.accept_edit_data = self.has_edit_button
            if not self.has_new_button:
                self.hide_new_button()
            if not self.has_edit_button:
                self.hide_edit_button()
        self._selected = None
        self.update_widgets()

        self.set_edit_button_sensitive(False)
        self.results.connect('selection-changed', self._on_selection_changed)
        self._check_permissions()

    def _setup_slaves(self):
        self._toolbar = SearchEditorToolBar()
        self._toolbar.connect("edit", self._on_toolbar__edit)
        self._toolbar.connect("add", self._on_toolbar__new)
        self.attach_slave('extra_holder', self._toolbar)

    def _check_permissions(self):
        if not self.editor_class:
            return

        pm = PermissionManager.get_permission_manager()
        key = self.editor_class.model_type.__name__
        if not pm.can_create(key):
            self.hide_new_button()

        if not pm.can_edit(key):
            if pm.can_see_details(key):
                # Replace edit button with a details button. self._read_only
                # will activate visual_mode for the editor
                self._read_only = True
                self._toolbar.edit_button_label.set_text(_('Details'))
                self._toolbar.edit_button_image.set_from_stock('gtk-info', gtk.ICON_SIZE_BUTTON)
            else:
                self.hide_edit_button()

    # Public API

    def set_edit_button_sensitive(self, value):
        """Control sensitivity of button edit"""
        self._toolbar.edit_button.set_sensitive(value)

    def set_edit_button_label(self, label, stock=None):
        """Edits label and icon of the edit button
        """
        self._toolbar.edit_button_label.set_label(label)
        if stock:
            self._toolbar.edit_button_image.set_from_stock(stock,
                                                           gtk.ICON_SIZE_BUTTON)

    def update_widgets(self, *args):
        self._toolbar.edit_button.set_sensitive(len(self.results))

    def hide_edit_button(self):
        self.accept_edit_data = False
        self._toolbar.edit_button.hide()

    def hide_new_button(self):
        self._toolbar.new_button.hide()

    def update_edited_item(self, model):
        """Update the edited item to its proper type and select it on the
        list results.
        This method must be overwritten on subclasses when editors don't
        return a valid instance or when returning more than one model.
        """
        if self._selected:
            selected = self._selected
            Store.of(selected).flush()
            self.results.update(selected)
        else:
            # user just added a new instance
            selected = self.get_searchlist_model(model)
            self.results.append(selected)
        self.results.select(selected)

    def run(self, obj=None):
        self._selected = obj
        if obj:
            obj = self.get_editor_model(obj)
        if obj and self.interface:
            obj = self.interface(obj)

        rv = self.run_editor(obj)
        if rv:
            self.search.refresh()
            self.enable_ok()

    def run_dialog(self, editor_class, parent, *args, **kwargs):
        return run_dialog(editor_class, parent, *args, **kwargs)

    def get_editor_class_for_object(self, obj):
        return self.editor_class

    def run_editor(self, obj):
        store = api.new_store()
        retval = self.run_dialog(self.get_editor_class_for_object(obj), self,
                                 store, store.fetch(obj),
                                 visual_mode=self._read_only)
        if store.confirm(retval):
            # If the return value is an ORMObject, fetch it from
            # the right connection
            if isinstance(retval, ORMObject):
                retval = self.store.get(type(retval), retval.id)
        store.close()
        return retval

    def row_activate(self, obj):
        """See :class:`SearchDialog.row_activate`
        """
        if self.double_click_confirm:
            SearchDialog.row_activate(self, obj)
        elif self.accept_edit_data:
            self._edit(obj)

    def _edit(self, obj):
        if obj is None:
            if self.results.get_selection_mode() == gtk.SELECTION_MULTIPLE:
                obj = self.results.get_selected_rows()
                qty = len(obj)
                if qty != 1:
                    raise AssertionError(
                        "There should be only one item selected. Got %s items"
                        % qty)
            else:
                obj = self.results.get_selected()
                if not obj:
                    raise AssertionError(
                        "There should be at least one item selected")

        self.run(obj)

    # Callbacks

    def _on_toolbar__edit(self, toolbar):
        self._edit(None)

    def _on_toolbar__new(self, toolbar):
        self.run()

    def _on_selection_changed(self, results, selected):
        can_edit = bool(selected)
        self.set_edit_button_sensitive(can_edit)

    #
    # Hooks
    #

    def get_searchlist_model(self, model):
        query = (getattr(self.search_spec, self.model_list_lookup_attr) == model.id)
        return self.store.find(self.search_spec, query).one()

    def get_editor_model(self, model):
        """This hook must be redefined on child when changing the type of
        the model is a requirement for edit method.
        """
        return model


class SearchEditorToolBar(GladeSlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'New' and 'Edit' buttons. """

    toplevel_name = 'ToolBar'
    gladefile = 'SearchEditor'
    domain = 'stoq'

    gsignal('edit')
    gsignal('add')

    #
    # Kiwi handlers
    #

    def on_edit_button__clicked(self, button):
        self.emit('edit')

    def on_new_button__clicked(self, button):
        self.emit('add')
