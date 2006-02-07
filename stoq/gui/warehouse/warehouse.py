# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/warehouse/warehouse.py:

    Main gui definition for warehouse application.
"""

import gettext

import gtk
from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.gui.base.columns import AccessorColumn, ForeignKeyColumn
from stoqlib.database import rollback_and_begin
from stoqlib.lib.defaults import ALL_ITEMS_INDEX, ALL_BRANCHES

from stoq.gui.application import SearchableAppWindow
from stoq.gui.wizards.receiving import ReceivingOrderWizard
from stoqlib.lib.validators import get_price_format_str
from stoq.domain.person import Person
from stoq.domain.product import Product
from stoq.domain.sellable import AbstractSellable, BaseSellableInfo
from stoq.domain.interfaces import ISellable, IStorable, IBranch

_ = gettext.gettext


class WarehouseApp(SearchableAppWindow):
    app_name = _('Warehouse')
    app_icon_name = 'stoq-warehouse-app'
    gladefile = "warehouse"
    searchbar_table = AbstractSellable
    searchbar_result_strings = (_('product'), _('products'))
    searchbar_labels = (_('Matching:'),)
    filter_slave_label = _('Show products at:')
    klist_selection_mode = gtk.SELECTION_MULTIPLE
    klist_name = 'products'

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self.table = Product.getAdapterClass(ISellable)
        self._setup_widgets()
        self._update_view()

    def _setup_widgets(self):
        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary_label = SummaryLabel(klist=self.products,
                                          column='quantity',
                                          label=_('<b>Stock Total:</b>'),
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def get_filter_slave_items(self):
        items = [(o.get_adapted().name, o)
                  for o in Person.iselect(IBranch, connection=self.conn)]
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        items.append(ALL_BRANCHES)
        return items

    def _update_view(self, *args):
        has_stock = len(self.products) > 0
        self.retention_button.set_sensitive(has_stock)
        one_selected = len(self.products.get_selected_rows()) == 1
        self.history_button.set_sensitive(one_selected)
        self._update_stock_total()

    def on_searchbar_activate(self, slave, objs):
        # We are going to improve accessor columns soon, so we will not need
        # to clear the list here any more. Bug 2275
        self._klist.clear()
        SearchableAppWindow.on_searchbar_activate(self, slave, objs)
        self._update_view()

    def _update_stock_total(self):
        self.summary_label.update_total()

    def _update_filter_slave(self, slave):
        self.searchbar.search_items()
        self._update_stock_total()

    def get_on_filter_slave_status_changed(self):
        return self._update_filter_slave

    def get_columns(self):
        return [Column('code', title=_('Code'), sorted=True,
                       data_type=str, width=100),
                ForeignKeyColumn(BaseSellableInfo, 'description',
                                 title=_('Description'), data_type=str,
                                 obj_field='base_sellable_info',
                                 expand=True, searchable=True),
                AccessorColumn('supplier', self._get_supplier,
                               title=_('Supplier'), data_type=str),
                AccessorColumn('quantity', self._get_stock_balance,
                               title=_('Quantity'), data_type=float)]
    #
    # Accessor
    #

    def _get_supplier(self, instance):
        """Accessor called by AccessorColumn"""
        adapted = instance.get_adapted()
        main_supplier_info = adapted.get_main_supplier_info()
        if not main_supplier_info:
            return ''
        if not main_supplier_info.supplier:
            raise DatabaseInconsistency('A ProductSupplierInfo object must '
                                        'have a supplier set. Found None '
                                        'instead')
        person = main_supplier_info.supplier.get_adapted()
        return person.name

    def _get_storable(self, instance):
        adapted = instance.get_adapted()
        conn = adapted.get_connection()
        return IStorable(adapted, connection=conn)

    def _get_stock_balance(self, instance):
        branch = self.filter_slave.get_selected_status()
        if branch == ALL_ITEMS_INDEX:
            branch = None
        storable = self._get_storable(instance)
        return storable.get_full_balance(branch)

    #
    # Hooks
    #

    def get_extra_query(self):
        """Hook called by SearchBar"""
        # TODO search by supplier name too. Bug 2180
        return (AbstractSellable.q.base_sellable_infoID ==
                BaseSellableInfo.q.id)

    def filter_results(self, sellables):
        """Hook called by SearchBar"""
        return [sellable for sellable in sellables
                        if isinstance(sellable, self.table)]

    #
    # Callbacks
    #


    def on_products__selection_changed(self, *args):
        self._update_view()

    def _on_receive_action_clicked(self, *args):
        model = self.run_dialog(ReceivingOrderWizard, self.conn)
        if not model:
            rollback_and_begin(self.conn)
        self.conn.commit()
