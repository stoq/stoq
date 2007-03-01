# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006, 2007 Async Open Source
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Implementation of basic dialogs for searching data """

import gtk
from kiwi.utils import gsignal
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.list import SummaryLabel
from kiwi.argcheck import argcheck
from sqlobject.sresults import SelectResults
from sqlobject.dbconnection import Transaction

from stoqlib.database.database import rollback_and_begin
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.base.searchbar import SearchBar
from stoqlib.lib.component import Adapter
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class _SearchDialogDetailsSlave(GladeSlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'New' and 'Edit' buttons. """

    gladefile = 'SearchDialogDetailsSlave'

    gsignal('details')
    gsignal('print')

    #
    # Kiwi handlers
    #

    def on_details_button__clicked(self, button):
        self.emit('details')

    def on_print_button__clicked(self, button):
        self.emit('print')

#
# Base dialogs for search.
#


class SearchDialog(BasicDialog):
    """  Base class for *all* the search dialogs, responsible for the list
    construction and "Filter" and "Clear" buttons management.

    This class must be subclassed and its subclass *must* implement the methods
    'get_columns' and 'get_query_and_args' (if desired, 'get_query_and_args'
    can be implemented in the user's slave class, so SearchDialog will get its
    slave instance and call the method directly). Its subclass also must
    implement a setup_slaves method and call its equivalent base class method
    as in:

    >>> def setup_slave(self):
    ...    SearchDialog.setup_slaves(self)

    or then, call it in its constructor, like:

    >>> def __init__(self, *args):
    ...     SearchDialog.__init__(self)

    Some important parameters:
    @cvar table: the table type which we will query on to get the objects.
    @cvar searchbar_labels: labels for SearchBar entry and date fields
    @cvar searchbar_result_strings: a tuple where each item has a singular
      and a plural form for searchbar results label
    """
    main_label_text = ''
    title = ''
    table = None
    search_table = None
    selection_mode = gtk.SELECTION_BROWSE
    searchbar_labels = None
    searchbar_result_strings = None
    searching_by_date = False
    size = ()

    @argcheck(Transaction, object, object, bool, basestring, int)
    def __init__(self, conn, table=None, search_table=None, hide_footer=True,
                 title='', selection_mode=None):
        """
        @param conn:
        @param table:
        @param editor_class:
        @param search_table:
        @param hide_footer:
        @param title:
        @param selection_mode:
        """

        self.conn = conn
        search_table = search_table or self.search_table
        table = table or self.table
        if not (table or search_table):
            raise ValueError(
                "%r must define a table or search_table attribute" % self)
        self.search_table = search_table or table

        # For consistency do not allow none or single, in other words,
        # only allowed values are browse and multiple so we always will
        # be able to use both the keyboard and the mouse to select items
        # in the search list.
        selection_mode = selection_mode or self.selection_mode
        if (selection_mode != gtk.SELECTION_BROWSE and
            selection_mode != gtk.SELECTION_MULTIPLE):
            raise ValueError('Invalid selection mode %r' % selection_mode)
        self.selection_mode = selection_mode

        BasicDialog.__init__(self)
        title = title or self.title
        self.summary_label = None
        BasicDialog._initialize(self, hide_footer=hide_footer,
                                main_label_text=self.main_label_text,
                                title=title, size=self.size)
        self.set_ok_label(_('Se_lect Items'))
        self.setup_slaves()

    def _sync(self, *args):
        rollback_and_begin(self.conn)

    def _check_searchbar_settings(self, value, attr_name):
        if not value:
            return False
        if not isinstance(value, tuple):
            raise TypeError("%s attribute must be of typle tuple, "
                            "got %s" % (attr_name, type(value)))
        return True

    def _setup_searchbar(self):
        columns = self.get_columns()
        query_args = self.get_query_args()
        use_dates = self.searching_by_date
        self.search_bar = SearchBar(self.conn, self.search_table,
                                    columns, query_args=query_args,
                                    filter_slave=self.get_filter_slave(),
                                    searching_by_date=use_dates)
        self.search_bar.set_query_callback(self.query)
        extra_query = self.get_extra_query
        if extra_query:
            self.search_bar.register_extra_query_callback(extra_query)
        self.search_bar.connect('before-search-activate', self._sync)
        self.search_bar.connect('search-activate', self.update_klist)
        if self._check_searchbar_settings(self.searchbar_result_strings,
                                          "searchbar_result_strings"):
            self.set_result_strings(*self.searchbar_result_strings)
        if self._check_searchbar_settings(self.searchbar_labels,
                                          "searchbar_labels"):
            self.set_searchbar_labels(*self.searchbar_labels)
        self.after_search_bar_created()
        self.attach_slave('header', self.search_bar)

    def _setup_klist(self):
        self.klist_vbox = gtk.VBox()
        self.klist = ObjectList(self.get_columns(), mode=self.selection_mode)
        self.klist_vbox.pack_start(self.klist)
        self.klist_vbox.show_all()
        # XXX: I think that BasicDialog must be redesigned, if so we don't
        # need this ".remove" crap
        self.main.remove(self.main_label)
        self.main.add(self.klist_vbox)
        self.klist.show()
        self.klist.connect('cell_edited', self.on_cell_edited)
        self.klist.connect('selection-changed', self._on_selection_changed)

    def _setup_details_slave(self):
        # FIXME: Gross hack
        has_details_btn = hasattr(self, 'on_details_button_clicked')
        has_print_btn = hasattr(self, 'on_print_button_clicked')
        if not (has_details_btn or has_print_btn):
            self._details_slave = None
            return
        self._details_slave = _SearchDialogDetailsSlave()
        self.attach_slave('details_holder', self._details_slave)
        if has_details_btn:
            self._details_slave.connect("details",
                                        self.on_details_button_clicked)
        else:
            self._details_slave.details_button.hide()
        if has_print_btn:
            self._details_slave.connect("print", self.on_print_button_clicked)
        else:
            self._details_slave.print_button.hide()

    #
    # Public API
    #

    def set_searchtable(self, search_table):
        self.search_table = search_table
        self.search_bar.set_searchtable(search_table)

    def set_searchbar_columns(self, columns):
        self.search_bar.set_columns(columns)

    def set_searchbar_search_string(self, search_str):
        self.search_bar.set_search_string(search_str)

    def perform_search(self):
        self.search_bar.search_items()

    def setup_summary_label(self, column_name, label_text):
        if self.summary_label is not None:
            self.klist_vbox.remove(self.summary_label)
        value_format = '<b>%s</b>'
        self.clear_klist()
        self.summary_label = SummaryLabel(klist=self.klist,
                                          column=column_name,
                                          label=label_text,
                                          value_format=value_format)
        self.summary_label.show()
        self.klist_vbox.pack_start(self.summary_label, False)

    def setup_slaves(self, **kwargs):
        self.disable_ok()
        self._setup_klist()
        self._setup_searchbar()
        self._setup_details_slave()

    @argcheck(bool)
    def set_details_button_sensitive(self, value):
        self._details_slave.details_button.set_sensitive(value)

    def get_query_args(self):
        """An optional list of SQLObject arguments for select function."""

    def get_extra_query(self):
        """An optional SQLObject.sqlbuilder query for select statement."""

    def get_filter_slave(self):
        """Returns a slave which will be used as filter by SearchBar.
        By default it returns None which means that no filter will be
        attached. Redefine this method in child when it's needed
        """
        return None

    def after_search_bar_created(self):
        """This method will be called after creating the SearchBar
        instance.  Redefine this method in child when it's needed
        """

    def on_cell_edited(self, klist, obj, attr):
        """Override this method on child when it's needed to perform some
        tasks when editing a row.
        """

    def _on_selection_changed(self, klist, selected):
        self.update_widgets()

    def set_searchbar_labels(self, search_entry_lbl, date_search_lbl=None):
        # Second argument is only used by Stoq's SearchableAppWindow
        self.search_bar.set_searchbar_labels(search_entry_lbl,
                                             date_search_lbl)

    def set_result_strings(self, singular_form, plural_form):
        """This method defines strings to be used in the
        search_results_label for SearchBar class.
        """
        self.search_bar.set_result_strings(singular_form, plural_form)

    def get_selection(self):
        mode = self.klist.get_selection_mode()
        if mode == gtk.SELECTION_BROWSE:
            return self.klist.get_selected()
        return self.klist.get_selected_rows()

    def clear_klist(self):
        self.klist.clear()
        self.update_widgets()

    def confirm(self):
        objs = self.get_selection()
        self.retval = objs
        self.close()

    def cancel(self, *args):
        self.retval = []
        self.close()

    #
    # Hooks
    #

    def update_klist(self, slave, objs):
        """A hook called by SearchBar and instances."""
        if not objs:
            self.klist.clear()
            self.disable_ok()
            self.update_widgets()
            return

        if isinstance(objs, (list, tuple)):
            count = len(objs)
        elif isinstance(objs, SelectResults):
            count = objs.count()
        else:
            msg = 'Invalid type for result objects: Type: %s'
            raise TypeError, msg % type(objs)

        if count:
            self.klist.add_list(objs)
            objs = iter(objs)
            selected = objs.next()
            self.klist.select(selected)
            self.enable_ok()
        if self.summary_label:
            self.summary_label.update_total()
        self.update_widgets()

    def update_widgets(self):
        """ Subclass can have an 'update_widgets', and this method will be
        called when a signal is emitted by 'Filter' or 'Clear' buttons and
        also when a list item is selected. """

    def query(self, table, query, queries):
        """Override this to control the queries made by the
        searchbar, see searchbar.set_query_callback for documentation
        """
        return table.select(query, **queries)

    #
    # Specification of methods that all subclasses *must* to implement
    #

    def get_columns(self):
        raise NotImplementedError(
            "get_columns() must be implemented in %r" % self)


class SearchEditorToolBar(GladeSlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'New' and 'Edit' buttons. """

    toplevel_name = 'ToolBar'
    gladefile = 'SearchEditor'
    domain = 'stoqlib'

    gsignal('edit')
    gsignal('add')

    #
    # Kiwi handlers
    #

    def on_edit_button__clicked(self, button):
        self.emit('edit')

    def on_new_button__clicked(self, button):
        self.emit('add')



class SearchEditor(SearchDialog):
    """ Base class for a search "editor" dialog, that offers a 'new' and
    'edit' button on the dialog footer. The 'new' and 'edit' buttons will
    call 'editor_class' sending as its parameters a new connection and the
    object to edit for 'edit' button.

    This is also a subclass of SearchDialog and the same rules are required.

    Simple example:

    >>> class CarSearch(SearchEditor):
    ...     title = _("Car Search")
    ...     table = Car
    ...     editor_class = CarEditor
    ...     size = (465, 390)
    ...     searchbar_result_strings = _("Car"), _("Cars")
    ...
    ...     def get_columns(self):
    ...         return [Column('brand', _('Brand'), data_type=str, width=90),
    ...                 Column('description', _('Description'), data_type=str,
    ...                         expand=True)]

    This will create a new editor called CarSearch.
      - It will be populated using the table Car.
      - The title of the editor is "Car Search".
      - To create new Car objects or to edit an existing Car object the
        CarEditor table will be used, which needs to be a subclass of BaseEditor.
      - The size of the new dialog will be 465 pixels wide and 390 pixels high.
      - When displaying results, the verb car and cars will be used, eg:
        1 car or 34 cars.
      - The get_columns() methods is required to be implemented, otherwise
        there's no way to know which data is going to be displayed.
        get_columns must return a list of kiwi objectlist columns.
        In this case we will display two columns, brand and description.
        They will be fetched from the car object using the attribute brand or
        description. Both of them are strings (data_type=str), the width of
        the first column is 90 pixels and the second column is expanded so
        it uses the rest of the available width.

    """
    model_editor_lookup_attr = 'id'
    has_new_button = has_edit_button = True
    model_list_lookup_attr = 'id'

    def __init__(self, conn, table=None, editor_class=None, interface=None,
                 search_table=None, hide_footer=True,
                 title='', selection_mode=gtk.SELECTION_BROWSE,
                 hide_toolbar=False):
        """
        @param conn:
        @param table:
        @param editor_class:
        @param interface: The interface which we need to apply to the objects in
          kiwi list to get adapter for the editor.
        @param search_table:
        @param hide_footer:
        @param title:
        @param selection_mode:
        @param hide_toolbar:
        """

        self.interface = interface

        SearchDialog.__init__(self, conn, table, search_table,
                              hide_footer=hide_footer, title=title,
                              selection_mode=selection_mode)

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
        self.klist.connect('double_click', self._on_list__double_click)
        self.update_widgets()

    def setup_slaves(self):
        SearchDialog.setup_slaves(self)
        self._toolbar = SearchEditorToolBar()
        self.attach_slave('extra_holder', self._toolbar)
        self._toolbar.connect("edit", self._on_toolbar__edit)
        self._toolbar.connect("add", self._on_toolbar__new)

    # Public API

    @argcheck(bool)
    def set_edit_button_sensitive(self, value):
        """Control sensitivity of button edit"""
        self._toolbar.edit_button.set_sensitive(value)

    def update_widgets(self, *args):
        self._toolbar.edit_button.set_sensitive(len(self.klist))

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
            selected.sync()
            self.klist.update(selected)
        else:
            # user just added a new instance
            selected = self.get_searchlist_model(model)
            self.klist.append(selected)
        self.klist.select(selected)

    def run(self, obj=None):
        self._selected = obj
        if obj:
            obj = self.get_editor_model(obj)
        if obj and self.interface:
            if isinstance(obj, Adapter):
                adapted = obj.get_adapted()
            else:
                adapted = obj
            obj = self.interface(adapted)
        rv = self.run_editor(obj)
        if not rv:
            rollback_and_begin(self.conn)
            return

        if self.editor_class.model_iface:
            rv = rv.get_adapted()

        self.conn.commit()
        self.update_edited_item(rv)
        self.enable_ok()

    def run_editor(self, obj):
        return run_dialog(self.editor_class, self, self.conn, obj)

    # Private

    def _edit(self, obj):
        if not self.accept_edit_data:
            return

        if obj is None:
            if self.klist.get_selection_mode() == gtk.SELECTION_MULTIPLE:
                obj = self.klist.get_selected_rows()
                qty = len(obj)
                if qty != 1:
                    raise AssertionError(
                      "There should be only one item selected. Got %s items"
                      % qty)
            else:
                obj = self.klist.get_selected()
                if not obj:
                    raise AssertionError(
                        "There should be at least one item selected")

        self.run(obj)

    # Callbacks

    def _on_toolbar__edit(self, toolbar):
        self._edit(None)

    def _on_toolbar__new(self, toolbar):
        self.run()

    def _on_list__double_click(self, list, obj):
        self._edit(obj)

    #
    # Hooks
    #

    def get_searchlist_model(self, model):
        # Ideally we want to use selectOneBy here, but it is not
        # yet implemented on viewable.
        items = self.search_table.select(
            getattr(self.search_table.q,
                    self.model_list_lookup_attr) == model.id,
            connection=self.conn)
        if items.count() != 1:
             raise DatabaseInconsistency(
                 "There should be exactly one item for %r " % model)
        return items[0]

    def get_editor_model(self, model):
        """This hook must be redefined on child when changing the type of
        the model is a requirement for edit method.
        """
        return model
