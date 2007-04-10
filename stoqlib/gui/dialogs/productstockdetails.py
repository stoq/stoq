# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Lincoln Molica                  <lincolnn@gmail.com>
##              Ariqueli Tejada Fonseca         <ariqtf@yahoo.com.br>
##              Evandro Vale Miquelito          <evandro@async.com.br>
##
##
""" Classes for product stock details """

import datetime
from decimal import Decimal

import gtk
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.list import SummaryLabel

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.product import (ProductAdaptToSellable,
                                    ProductSellableItem)
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.receiving import ReceivingOrderItem
from stoqlib.domain.sellable import ASellableItem

_ = stoqlib_gettext


class ProductStockHistoryDialog(BaseEditor):
    """This dialog shows some important details about products like:
    -history of received products
    -history of sales about a determined product
    """

    title = _("Product Stock History")
    hide_footer = True
    size = (700, 400)
    model_type = ProductAdaptToSellable
    gladefile = "ProductStockHistoryDialog"

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.receiving_list.set_columns(self._get_receiving_columns())
        self.sales_list.set_columns(self._get_sale_columns())

        items = ReceivingOrderItem.selectBy(sellableID=self.model.id,
                                            connection=self.conn)
        self.receiving_list.add_list(list(items))

        query = ASellableItem.q.sellableID == self.model.id
        items = ProductSellableItem.select(query, connection=self.conn)
        self.sales_list.add_list(list(items))

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

    def _get_receiving_columns(self):
        return [Column("receiving_order.id",
                       title=_("#"), data_type=int, sorted=True,
                       justify=gtk.JUSTIFY_RIGHT, width=45),
                Column("receiving_order.receival_date", title=_("Date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT,
                       width=80),
                Column("receiving_order.id",
                       title=_("Purchase Order"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=140),
                Column("receiving_order.supplier_name",
                       title=_("Supplier"), expand=True, data_type=str),
                Column("receiving_order.invoice_number", title=_("Invoice"),
                       width=80, data_type=str),
                Column("quantity", title=_("Quantity"),
                       data_type=Decimal, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("unit_description", title=_("Unit"), data_type=str,
                       width=70)]

    def _get_sale_columns(self):
        return [Column("sale.id", title=_("#"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       width=45, sorted=True),
                Column("sale.open_date",
                       title=_("Date Started"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT, width=130),
                Column("sale.client_name",
                       title=_("Client"), expand=True, data_type=str),
                Column("quantity", title=_("Quantity"),
                       width=90, data_type=int),
                Column("sellable.unit_description",
                       title=_("Unit"), width=70, data_type=str)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, ['product'])

        adaptable = self.model.get_adapted()
        storable = IStorable(adaptable)
        self.add_proxy(storable, ['full_balance'])
