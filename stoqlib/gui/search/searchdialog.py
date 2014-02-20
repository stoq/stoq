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
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.base.gtkadds import button_set_image_with_label
from stoqlib.gui.dialogs.spreadsheetexporterdialog import SpreadSheetExporter
from stoqlib.gui.events import SearchDialogSetupSearchEvent
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.gui.search.searchslave import SearchSlave
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.decorators import public
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
    search_spec = None

    #: The label that will be used for the main filter in this dialog
    search_label = None

    #: Selection mode to use (if its possible to select more than one row)
    selection_mode = gtk.SELECTION_BROWSE

    #: Default size for this dialog
    size = ()

    #: If the advanced search is enabled or disabled. When ``True`` we will
    #: instrospect the columns returned by :meth:`get_columns`,and use those
    #: that are subclasses of :class:`stoqlib.gui.search.searchcolumns.SearchColumn`
    #: to add as options for the user to filter the results.
    advanced_search = True

    #: the report class used to print a report for the results.
    #: If ``None``, the print button will not even be created
    report_class = None

    tree = False

    def __init__(self, store, search_spec=None, hide_footer=True,
                 title='', selection_mode=None, double_click_confirm=False):
        """
        A base class for search dialog inheritance

        :param store: a store
        :param search_spec:
        :param hide_footer:
        :param title:
        :param selection_mode:
        :param double_click_confirm: If double click a item in the list should
          automatically confirm
        """

        self.store = store
        self.search_spec = search_spec or self.search_spec
        if not self.search_spec:
            raise ValueError("%r needs a search table" % self)
        self.selection_mode = self._setup_selection_mode(selection_mode)
        self.summary_label = None
        self.double_click_confirm = double_click_confirm
        self.csv_button = None

        BasicDialog.__init__(self, hide_footer=hide_footer,
                             main_label_text=self.main_label_text,
                             title=title or self.title,
                             size=self.size)

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
        self.columns = self.get_columns()
        SearchDialogSetupSearchEvent.emit(self)
        self.search = SearchSlave(
            self.columns,
            tree=self.tree,
            restore_name=self.__class__.__name__,
            store=self.store,
            search_spec=self.search_spec,
        )
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
        has_print_btn = self.report_class is not None
        self.results.connect('has-rows', self._has_rows)
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
            self._details_slave.connect("print", self._on_print_button__clicked)
            self.set_print_button_sensitive(False)
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
        self.action_area.set_layout(gtk.BUTTONBOX_END)
        self.action_area.pack_start(button, False, False, 6)
        self.action_area.set_child_secondary(button, True)
        return button

    def add_csv_button(self, name, prefix):
        self._csv_name = name
        self._csv_prefix = prefix
        self.csv_button = self.add_button(label=_("Export to spreadsheet..."))
        self.csv_button.connect('clicked', self._on_export_csv_button__clicked)
        self.csv_button.show()
        self.csv_button.set_sensitive(False)

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

    def print_report(self):
        print_report(self.report_class, self.results, list(self.results),
                     filters=self.search.get_search_filters())

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

    def add_extension(self, extension):
        """Adds the extention to this search.

        See :class:`stoqlib.gui.search.searchextention.SearchExtention for more
        information
        """
        extension.attach(self)

    def add_columns(self, columns):
        """Add some columns to the default ones.

        Note that this method must be called during the setup of this search,
        which right now is only possible for those who capture the
        `<stoqlib.gui.events.SearchDialogSetupSearchEvent>`
        """
        self.columns.extend(columns)

    #
    # Filters
    #

    def create_branch_filter(self, label=None):
        from stoqlib.domain.person import Branch
        current = api.get_current_branch(self.store)
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            items = [(current.get_description(), current.id)]
        else:
            branches = Branch.get_active_branches(self.store)
            items = [(b.get_description(), b.id) for b in branches]
            items.insert(0, (_("Any"), None))

        if not label:
            label = _('Branch:')
        branch_filter = ComboSearchFilter(label, items)
        if current:
            branch_filter.select(current.id)

        return branch_filter

    def create_sellable_filter(self, label=None):
        from stoqlib.domain.sellable import Sellable
        items = [(desc, status) for status, desc in Sellable.statuses.items()]
        items.insert(0, (_(u"Any"), None))

        if label is None:
            label = _('With status:')
        sellable_filter = ComboSearchFilter(label, items)
        # Select status available by default
        sellable_filter.select(Sellable.STATUS_AVAILABLE)

        return sellable_filter

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

    def create_salesperson_filter(self, label=None):
        from stoqlib.domain.person import SalesPerson
        items = SalesPerson.get_active_items(self.store)
        items.insert(0, (_("Any"), None))

        if not label:
            label = _('Salesperson:')
        return ComboSearchFilter(label, items)

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
        if self._details_slave:
            self.set_print_button_sensitive(obj)

        if self.csv_button:
            self.csv_button.set_sensitive(bool(obj))

    def _on_export_csv_button__clicked(self, widget):
        sse = SpreadSheetExporter()
        sse.export(object_list=self.results,
                   name=self._csv_name,
                   filename_prefix=self._csv_prefix)

    def _on_print_button__clicked(self, button):
        self.print_report()

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
