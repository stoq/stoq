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
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.list import SummaryLabel

from stoqlib.api import api
from stoqlib.domain.inventory import InventoryItemsView
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.transfer import TransferOrderItem
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
    size = (700, 400)
    model_type = Sellable
    gladefile = "ProductStockHistoryDialog"

    def __init__(self, store, model, branch):
        self._branch = branch
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.receiving_list.set_columns(self._get_receiving_columns())
        self.sales_list.set_columns(self._get_sale_columns())
        self.transfer_list.set_columns(self._get_transfer_columns())
        self.loan_list.set_columns(self._get_loan_columns())
        self.decrease_list.set_columns(self._get_decrease_columns())
        self.inventory_list.set_columns(self._get_inventory_columns())

        items = self.store.find(ReceivingItemView, sellable_id=self.model.id)

        self.receiving_list.add_list(list(items))

        items = self.store.find(SaleItemsView, sellable_id=self.model.id)
        self.sales_list.add_list(list(items))

        items = self.store.find(TransferOrderItem, sellable_id=self.model.id)
        self.transfer_list.add_list(list(items))

        items = self.store.find(LoanItemView, sellable_id=self.model.id)
        self.loan_list.add_list(list(items))

        items = self.store.find(StockDecreaseItemsView, sellable=self.model.id)
        self.decrease_list.add_list(list(items))

        self.inventory_list.add_list(
            InventoryItemsView.find_by_product(self.store, self.model.product))

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
                                              column='quantity',
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
        return [IdentifierColumn("order_identifier", sorted=True),
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
                Column("unit_description", title=_("Unit"), data_type=str)]

    def _get_sale_columns(self):
        return [IdentifierColumn("sale_identifier", sorted=True),
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
        return [IdentifierColumn("transfer_order.identifier", sorted=True),
                Column("transfer_order.open_date",
                       title=_("Date Created"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("transfer_order.destination_branch_name",
                       title=_("Destination"), expand=True,
                       data_type=str),
                Column("transfer_order.source_responsible_name",
                       title=_("Responsible"), expand=True,
                       data_type=str),
                Column("quantity", title=_("Transfered"),
                       data_type=Decimal)]

    def _get_loan_columns(self):
        return [IdentifierColumn("loan_identifier", title=_("Loan #"),
                                 sorted=True),
                Column("opened", title=_(u"Opened"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column("code", title=_(u"Code"), data_type=str, visible=False),
                Column("category_description", title=_(u"Category"),
                       data_type=str, visible=False),
                Column("description", title=_(u"Description"), data_type=str,
                       expand=True),
                Column("unit_description", title=_(u"Unit"), data_type=str),
                Column("quantity", title=_(u"Loaned"), data_type=Decimal),
                Column("return_quantity", title=_(u"Returned"),
                       data_type=Decimal)]

    def _get_decrease_columns(self):
        return [IdentifierColumn("decrease_identifier", sorted=True),
                Column("date", title=_("Date"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("removed_by_name", title=_("Removed By"), expand=True,
                       data_type=str),
                Column("quantity", title=_("Quantity"), data_type=int),
                Column("unit_description", title=_("Unit"), data_type=str)]

    def _get_inventory_columns(self):
        return [IdentifierColumn("inventory_identifier", sorted=True),
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

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, ['description'])

        storable = self.model.product_storable
        self.add_proxy(storable, ['full_balance'])
