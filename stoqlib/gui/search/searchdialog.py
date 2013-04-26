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

import logging

import gtk
from kiwi.environ import environ
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.database.queryexecuter import QueryExecuter
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.gui.search.searchslave import SearchSlave
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.base.gtkadds import button_set_image_with_label
from stoqlib.lib.decorators import public
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = logging.getLogger(__name__)


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


@public(since="1.5.0")
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
    """
    main_label_text = ''

    #: Title that will appear in the window, for instance 'Product Search'
    title = ''

    # The table type which we will query on to get the objects.
    search_table = None

    #: The label that will be used for the main filter in this dialog
    search_label = None

    #: Selection mode to use (if its possible to select more than one row)
    selection_mode = gtk.SELECTION_BROWSE

    #: Default size for this dialog
    size = ()

    #: If the advanced search is enabled or disabled. When ``True`` we will
    #: instrospect the columns returned by :meth:`get_columns`,and use those
    #: that are subclasses of :class:`stoqlib.gui.columns.SearchColumn` to add
    #: as options for the user to filter the results.
    advanced_search = True

    tree = False

    def __init__(self, store, search_table=None, hide_footer=True,
                 title='', selection_mode=None, double_click_confirm=False):
        """
        A base class for search dialog inheritance

        :param store: a store
        :param table:
        :param search_table:
        :param hide_footer:
        :param title:
        :param selection_mode:
        :param double_click_confirm: If double click a item in the list should
          automatically confirm
        """

        self.store = store
        self.search_table = search_table or self.search_table
        if not self.search_table:
            raise ValueError("%r needs a search table" % self)
        self.selection_mode = self._setup_selection_mode(selection_mode)
        self.summary_label = None
        self.double_click_confirm = double_click_confirm

        BasicDialog.__init__(self, hide_footer=hide_footer,
                             main_label_text=self.main_label_text,
                             title=title or self.title,
                             size=self.size)

        self.executer = QueryExecuter(store)
        # FIXME: Remove this limit, but we need to migrate all existing
        #        searches to use lazy lists first. That in turn require
        #        us to rewrite the queries in such a way that count(*)
        #        will work properly.
        self.executer.set_limit(sysparam(self.store).MAX_SEARCH_RESULTS)
        self.set_table(self.search_table)

        self.enable_window_controls()
        self.disable_ok()
        self.set_ok_label(_('Se_lect Items'))
        self._setup_search()
        self._setup_details_slave()

        self.create_filters()
        self.setup_widgets()
        if self.search_label:
            self.set_searchbar_label(self.search_label)

    def _setup_selection_mode(self, selection_mode):
        # For consistency do not allow none or single, in other words,
        # only allowed values are browse and multiple so we always will
        # be able to use both the keyboard and the mouse to select items
        # in the search list.
        selection_mode = selection_mode or self.selection_mode
        if (selection_mode != gtk.SELECTION_BROWSE and
            selection_mode != gtk.SELECTION_MULTIPLE):
            raise ValueError('Invalid selection mode %r' % selection_mode)
        return selection_mode

    def _setup_search(self):
        self.search = SearchSlave(
            self.get_columns(),
            tree=self.tree,
            restore_name=self.__class__.__name__,
        )
        self.search.set_query_executer(self.executer)
        if self.advanced_search:
            self.search.enable_advanced_search()
        self.attach_slave('main', self.search)
        self.header.hide()

        self.results = self.search.result_view
        self.results.set_selection_mode(self.selection_mode)
        self.results.connect('cell-edited', self._on_results__cell_edited)
        self.results.connect('selection-changed',
                             self._on_results__selection_changed)
        self.results.connect('row-activated', self._on_results__row_activated)

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
            self.set_print_button_sensitive(False)
            self.results.connect('has-rows', self._has_rows)
        else:
            self._details_slave.print_button.hide()

    #
    # Public API
    #

    def add_button(self, label, stock=None, image=None):
        """Adds a button in the bottom of the dialog.

        :param label: the text that will be displayed by the button.
        :param stock: the gtk stock id to be used in the button.
        :param image: the image filename.
        """
        button = gtk.Button(label=label)
        if image:
            image_widget = gtk.Image()
            image_widget.set_from_file(
                environ.find_resource('pixmaps', image))
            image_widget.show()
            button.set_image(image_widget)
        elif stock:
            button_set_image_with_label(button, stock, label)
        self.action_area.set_layout(gtk.BUTTONBOX_START)
        self.action_area.pack_start(button, False, False, 6)
        return button

    def set_details_button_sensitive(self, value):
        self._details_slave.details_button.set_sensitive(value)

    def set_print_button_sensitive(self, value):
        self._details_slave.print_button.set_sensitive(value)

    def get_selection(self):
        mode = self.results.get_selection_mode()
        if mode == gtk.SELECTION_BROWSE:
            return self.results.get_selected()
        return self.results.get_selected_rows()

    def confirm(self, retval=None):
        """Confirms the dialog
        :param retval: optional parameter which will be selected when the
          dialog is closed
        """
        if retval is None:
            retval = self.get_selection()
        self.retval = retval
        self.search.save_columns()
        # FIXME: This should chain up so the "confirm" signal gets emitted
        self.close()

    def cancel(self, *args):
        self.retval = []
        self.search.save_columns()
        # FIXME: This should chain up so the "cancel" signal gets emitted
        self.close()

    def set_table(self, table):
        self.executer.set_table(table)
        self.search_table = table

    # FIXME: -> remove/use

    # TODO: Check if we can remove
    def set_searchbar_label(self, label):
        search_filter = self.search.get_primary_filter()
        search_filter.set_label(label)

    def set_searchbar_search_string(self, string):
        if string == self.get_searchbar_search_string():
            return
        search_filter = self.search.get_primary_filter()
        search_filter.entry.set_text(string)

    def get_searchbar_search_string(self):
        search_filter = self.search.get_primary_filter()
        return search_filter.get_state().text

    def set_text_field_columns(self, columns):
        """See :class:`SearchSlave.set_text_field_columns`
        """
        self.search.set_text_field_columns(columns)

    def disable_search_entry(self):
        """See :class:`SearchSlave.disable_search_entry`
        """
        self.search.disable_search_entry()

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None):
        """See :class:`SearchSlave.add_filter`
        """
        self.search.add_filter(search_filter, position, columns, callback)

    def row_activate(self, obj):
        """This is called when an item in the results list is double clicked.

        :param obj: the item that was double clicked.
        """
        if self.double_click_confirm:
            # But only if its also confirmable with ok_button
            if self.ok_button.props.sensitive:
                self.confirm()

    #
    # Filters
    #

    def create_branch_filter(self, label=None):
        from stoqlib.domain.person import Branch
        branches = Branch.get_active_branches(self.store)
        items = [(b.person.name, b.id) for b in branches]
        # if not items:
        #    raise ValueError('You should have at least one branch at '
        #                      'this point')
        items.insert(0, (_("Any"), None))

        if not label:
            label = _('Branch:')
        branch_filter = ComboSearchFilter(label, items)
        current = api.get_current_branch(self.store)
        if current:
            branch_filter.select(current.id)

        return branch_filter

    def create_payment_filter(self, label=None):
        from stoqlib.domain.payment.method import PaymentMethod
        methods = PaymentMethod.get_active_methods(self.store)
        items = [(_('Any'), None)]
        for method in methods:
            if method.method_name == 'multiple':
                continue
            items.append((method.description, method))

        if not label:
            label = _('Method:')
        payment_filter = ComboSearchFilter(label, items)
        payment_filter.select(None)

        return payment_filter

    def create_provider_filter(self, label=None):
        from stoqlib.domain.payment.card import CreditProvider
        providers = CreditProvider.get_card_providers(self.store)
        items = [(p.short_name, p) for p in providers]
        items.insert(0, (_("Any"), None))

        if not label:
            label = _('Provider:')
        provider_filter = ComboSearchFilter(label, items)

        return provider_filter

    #
    # Callbacks
    #

    def on_search__search_completed(self, search, results, states):
        self.search_completed(results, states)

    def _on_results__cell_edited(self, results, obj, attr):
        """Override this method on child when it's needed to perform some
        tasks when editing a row.
        """

    def _on_results__selection_changed(self, results, selected):
        self.update_widgets()
        if selected:
            self.enable_ok()
        else:
            self.disable_ok()

    def _on_results__row_activated(self, results, obj):
        self.row_activate(obj)

    def _has_rows(self, results, obj):
        self.set_print_button_sensitive(obj)

    #
    # Hooks
    #

    def create_filters(self):
        raise NotImplementedError(
            "create_filters() must be implemented in %r" % self)

    def setup_widgets(self):
        pass

    def get_columns(self):
        raise NotImplementedError(
            "get_columns() must be implemented in %r" % self)

    def update_widgets(self):
        """Subclass can have an 'update_widgets', and this method will be
        called when a signal is emitted by 'Filter' or 'Clear' buttons and
        also when a list item is selected. """

    def search_completed(self, results, states):
        pass


class SearchDialogPrintSlave(GladeSlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'print_price_button' buttons. """

    gladefile = 'SearchDialogPrintSlave'

    gsignal('print')

    #
    # Kiwi handlers
    #

    def on_print_price_button__clicked(self, button):
        self.emit('print')


class SearchDialogButtonSlave(GladeSlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing buttons. """

    gladefile = 'SearchDialogButtonSlave'

    gsignal('click')

    #
    # Kiwi handlers
    #

    def on_button__clicked(self, button):
        self.emit('click')
