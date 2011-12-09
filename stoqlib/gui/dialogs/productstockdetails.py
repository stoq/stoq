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
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.list import SummaryLabel

from stoqlib.database.orm import AND
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.loan import Loan
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.transfer import TransferOrderItem
from stoqlib.domain.views import (ReceivingItemView, SaleItemsView,
                                  LoanItemView, StockDecreaseItemsView)

_ = stoqlib_gettext


class ProductStockHistoryDialog(BaseEditor):
    """This dialog shows some important details about products like:
    -history of received products
    -history of sales about a determined product
    """

    title = _("Product History")
    hide_footer = True
    size = (700, 400)
    model_type = Sellable
    gladefile = "ProductStockHistoryDialog"

    def __init__(self, conn, model, branch):
        self._branch = branch
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.receiving_list.set_columns(self._get_receiving_columns())
        self.sales_list.set_columns(self._get_sale_columns())
        self.transfer_list.set_columns(self._get_transfer_columns())
        self.loan_list.set_columns(self._get_loan_columns())
        self.decrease_list.set_columns(self._get_decrease_columns())

        items = ReceivingItemView.select(
            ReceivingItemView.q.sellable_id == self.model.id,
            connection=self.conn)

        self.receiving_list.add_list(list(items))

        items = SaleItemsView.select(
                    SaleItemsView.q.sellable_id == self.model.id,
                    connection=self.conn)
        self.sales_list.add_list(list(items))

        items = TransferOrderItem.selectBy(sellableID=self.model.id,
                                            connection=self.conn)
        self.transfer_list.add_list(list(items))

        items = LoanItemView.select(AND(
            LoanItemView.q.sellable_id == self.model.id,
            LoanItemView.q.loan_status == Loan.STATUS_OPEN),
            connection=self.conn)
        self.loan_list.add_list(list(items))

        items = StockDecreaseItemsView.select(
                    StockDecreaseItemsView.q.sellable == self.model.id,
                    connection=self.conn)

        self.decrease_list.add_list(list(items))

        value_format = '<b>%s</b>'
        total_label = "<b>%s</b>" % _("Total:")
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
        return [Column("order_id", title=_("#"), data_type=int, sorted=True,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("receival_date", title=_("Date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column("purchase_id", title=_("Purchase Order"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("supplier_name", title=_("Supplier"), expand=True,
                       data_type=str),
                Column("invoice_number", title=_("Invoice"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("quantity", title=_("Quantity"), data_type=Decimal,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("unit_description", title=_("Unit"), data_type=str)]

    def _get_sale_columns(self):
        return [Column("sale_id", title=_("#"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       sorted=True),
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
        return [Column("transfer_order.id", title=_("#"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       sorted=True),
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
        return [Column("loan_id", title=_("Loan"), data_type=int,
                        justify=gtk.JUSTIFY_RIGHT, sorted=True),
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
        return [Column("id", title=_("#"), data_type=int,
                        justify=gtk.JUSTIFY_RIGHT, sorted=True),
                Column("date", title=_("Date"), data_type=datetime.date,
                        justify=gtk.JUSTIFY_RIGHT),
                Column("removed_by_name", title=_("Removed By"), expand=True,
                        data_type=str),
                Column("quantity", title=_("Quantity"), data_type=int),
                Column("unit_description", title=_("Unit"), data_type=str)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, ['description'])

        storable = IStorable(self.model.product)
        self.add_proxy(storable, ['full_balance'])
