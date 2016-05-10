# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
""" Classes for product stock details """

import datetime
from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ObjectList, SummaryLabel

from stoqlib.api import api
from stoqlib.domain.inventory import InventoryItemsView
from stoqlib.domain.person import Branch
from stoqlib.domain.product import StorableBatchView
from stoqlib.domain.sale import ReturnedSaleItemsView
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.transfer import TransferItemView
from stoqlib.domain.views import (ReceivingItemView, SaleItemsView,
                                  LoanItemView, StockDecreaseItemsView)
from stoqlib.lib.formatters import get_formatted_cost, format_quantity
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn

_ = stoqlib_gettext


class ProductStockHistoryDialog(BaseEditor):
    """This dialog shows some important history details about products:

    * received products
    * sales about a determined product
    * transfers
    * loans
    * manual decreases
    """

    title = _("Product History")
    hide_footer = True
    size = (-1, 400)
    model_type = Sellable
    gladefile = "ProductStockHistoryDialog"

    def __init__(self, store, model, branch):
        product = model.product
        self._is_batch = product and product.storable and product.storable.is_batch
        self._branch = branch
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def add_tab(self, name):
        box = gtk.HBox()
        box.set_border_width(6)
        box.show()
        olist = ObjectList()
        box.pack_start(olist)
        olist.show()
        self.history_notebook.append_page(box, gtk.Label(name))
        return olist

    def _add_batches_tab(self):
        olist = self.add_tab(_('Batches'))
        olist.set_columns(self._get_batches_columns())

        items = StorableBatchView.find_by_storable(
            store=self.store,
            storable=self.model.product.storable,
            branch=self._branch)
        olist.add_list(list(items))

    def _setup_widgets(self):
        if self._is_batch:
            self._add_batches_tab()

        self.receiving_list.set_columns(self._get_receiving_columns())
        self.sales_list.set_columns(self._get_sale_columns())
        self.transfer_list.set_columns(self._get_transfer_columns())
        self.loan_list.set_columns(self._get_loan_columns())
        self.decrease_list.set_columns(self._get_decrease_columns())
        self.inventory_list.set_columns(self._get_inventory_columns())
        self.returned_list.set_columns(self._get_returned_columns())

        current_branch = api.get_current_branch(self.store)
        items = self.store.find(ReceivingItemView, sellable_id=self.model.id)
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            items = items.find(Branch.id == current_branch.id)
        self.receiving_list.add_list(list(items))

        items = SaleItemsView.find_confirmed(self.store,
                                             sellable=self.model)
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            items = items.find(Branch.id == current_branch.id)
        self.sales_list.add_list(list(items))

        items = TransferItemView.find_by_branch(self.store, self.model, current_branch)
        self.transfer_list.add_list(list(items))

        items = self.store.find(LoanItemView, sellable_id=self.model.id)
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            items = items.find(Branch.id == current_branch.id)
        self.loan_list.add_list(list(items))

        items = self.store.find(StockDecreaseItemsView, sellable=self.model.id)
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            items = items.find(Branch.id == current_branch.id)
        self.decrease_list.add_list(list(items))

        items = InventoryItemsView.find_by_product(self.store, self.model.product)
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            items = items.find(Branch.id == current_branch.id)
        self.inventory_list.add_list(items)

        items = self.store.find(ReturnedSaleItemsView, sellable_id=self.model.id)
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            items = items.find(Branch.id == current_branch.id)
        self.returned_list.add_list(items)

        value_format = '<b>%s</b>'
        total_label = "<b>%s</b>" % api.escape(_("Total:"))
        receiving_summary_label = SummaryLabel(klist=self.receiving_list,
                                               column='quantity',
                                               label=total_label,
                                               value_format=value_format)
        receiving_summary_label.show()
        self.receiving_vbox.pack_start(receiving_summary_label, False)

        sales_summary_label = SummaryLabel(klist=self.sales_list,
                                           column='quantity',
                                           label=total_label,
                                           value_format=value_format)
        sales_summary_label.show()
        self.sales_vbox.pack_start(sales_summary_label, False)

        transfer_summary_label = SummaryLabel(klist=self.transfer_list,
                                              column='item_quantity',
                                              label=total_label,
                                              value_format=value_format)
        transfer_summary_label.show()
        self.transfer_vbox.pack_start(transfer_summary_label, False)

        loan_summary_label = SummaryLabel(klist=self.loan_list,
                                          column='quantity',
                                          label=total_label,
                                          value_format=value_format)
        self.loan_vbox.pack_start(loan_summary_label, False)

        decrease_summary_label = SummaryLabel(klist=self.decrease_list,
                                              column='quantity',
                                              label=total_label,
                                              value_format=value_format)
        decrease_summary_label.show()
        self.decrease_vbox.pack_start(decrease_summary_label, False)

    def _get_receiving_columns(self):
        return [IdentifierColumn("order_identifier", title=_('Receiving #'), sorted=True),
                Column('batch_number', title=_('Batch'), data_type=str,
                       visible=self._is_batch),
                Column('batch_date', title=_('Batch Date'),
                       data_type=datetime.date, visible=False),
                Column("receival_date", title=_("Date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                IdentifierColumn("purchase_identifier",
                                 title=_("Purchase #")),
                Column("supplier_name", title=_("Supplier"), expand=True,
                       data_type=str),
                Column("invoice_number", title=_("Invoice"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("quantity", title=_("Quantity"), data_type=Decimal,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("cost", title=_("Cost"), data_type=currency),
                Column("unit_description", title=_("Unit"), data_type=str)]

    def _get_sale_columns(self):
        return [IdentifierColumn("sale_identifier", title=_('Sale #'), sorted=True),
                Column('batch_number', title=_('Batch'), data_type=str,
                       visible=self._is_batch),
                Column('batch_date', title=_('Batch Date'),
                       data_type=datetime.date, visible=False),
                Column("sale_date",
                       title=_("Date Started"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("client_name",
                       title=_("Client"), expand=True, data_type=str),
                Column("quantity", title=_("Sold"),
                       data_type=int),
                Column("unit_description",
                       title=_("Unit"), data_type=str)
                ]

    def _get_transfer_columns(self):
        return [IdentifierColumn("transfer_order.identifier", title=_('Transfer #'),
                                 sorted=True),
                Column('batch_number', title=_('Batch'), data_type=str,
                       visible=self._is_batch),
                Column('batch_date', title=_('Batch Date'),
                       data_type=datetime.date, visible=False),
                Column("transfer_order.open_date",
                       title=_("Date Created"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("transfer_order.source_branch_name",
                       title=_("Source"), expand=True,
                       data_type=str),
                Column("transfer_order.destination_branch_name",
                       title=_("Destination"), expand=True,
                       data_type=str),
                Column("transfer_order.source_responsible_name",
                       title=_("Responsible"), expand=True,
                       data_type=str),
                Column("item_quantity", title=_("Transfered"),
                       data_type=Decimal)]

    def _get_loan_columns(self):
        return [IdentifierColumn("loan_identifier", title=('Loan #'), sorted=True),
                Column('batch_number', title=_('Batch'), data_type=str,
                       visible=self._is_batch),
                Column('batch_date', title=_('Batch Date'),
                       data_type=datetime.date, visible=False),
                Column("opened", title=_(u"Opened"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column("code", title=_(u"Code"), data_type=str, visible=False),
                Column("category_description", title=_(u"Category"),
                       data_type=str, visible=False),
                Column("description", title=_(u"Description"), data_type=str,
                       expand=True),
                Column("unit_description", title=_(u"Unit"), data_type=str),
                Column("quantity", title=_(u"Loaned"), data_type=Decimal),
                Column("sale_quantity", title=_(u"Sold"), data_type=Decimal),
                Column("return_quantity", title=_(u"Returned"),
                       data_type=Decimal)]

    def _get_decrease_columns(self):
        return [IdentifierColumn("decrease_identifier", title=_('Decrease #'), sorted=True),
                Column('batch_number', title=_('Batch'), data_type=str,
                       visible=self._is_batch),
                Column('batch_date', title=_('Batch Date'),
                       data_type=datetime.date, visible=False),
                Column("date", title=_("Date"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("removed_by_name", title=_("Removed By"), expand=True,
                       data_type=str),
                Column("quantity", title=_("Quantity"), data_type=int),
                Column("unit_description", title=_("Unit"), data_type=str)]

    def _get_inventory_columns(self):
        return [IdentifierColumn("inventory_identifier", title=_('Inventory #'), sorted=True),
                Column('batch_number', title=_('Batch'), data_type=str,
                       visible=self._is_batch),
                Column('batch_date', title=_('Batch Date'),
                       data_type=datetime.date, visible=False),
                Column("responsible_name", title=_("Responsible"),
                       data_type=str),
                Column("open_date", title=_("Open date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column("close_date", title=_("Close date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column("recorded_quantity", title=_("Recorded qty"),
                       data_type=Decimal, format_func=format_quantity),
                Column("actual_quantity", title=_("Counted qty"),
                       data_type=Decimal, format_func=format_quantity),
                Column("product_cost", title=_("Cost"), data_type=currency,
                       format_func=get_formatted_cost)]

    def _get_returned_columns(self):
        return [IdentifierColumn("returned_identifier", title=_('Returned #'), sorted=True),
                Column('batch_number', title=_('Batch'), data_type=str,
                       visible=self._is_batch),
                Column('batch_date', title=_('Batch Date'),
                       data_type=datetime.date, visible=False),
                Column("reason", title=_(u"Reason"),
                       data_type=str, expand=True),
                Column("quantity", title=_(u"Quantity"),
                       data_type=Decimal, format_func=format_quantity),
                Column("invoice_number", title=_(u"Invoice"),
                       data_type=int, visible=False),
                Column("price", title=_(u"Price"), data_type=currency,
                       format_func=get_formatted_cost),
                Column("return_date", title=_(u"Return Date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT)]

    def _get_batches_columns(self):
        return [Column('batch_number', title=_('Batch'), data_type=str,
                       expand=True),
                Column('create_date', title=_('Batch Date'),
                       data_type=datetime.date),
                Column("stock", title=_("Quantity"), data_type=int),
                ]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, ['description'])

        storable = self.model.product_storable
        self.add_proxy(storable, ['full_balance'])
