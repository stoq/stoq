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
                                    ProductRetentionHistory)
from stoqlib.domain.interfaces import IStorable, IProduct
from stoqlib.domain.receiving import ReceivingOrderItem
from stoqlib.domain.sale import SaleItem
from stoqlib.domain.transfer import TransferOrderItem

_ = stoqlib_gettext


class ProductStockHistoryDialog(BaseEditor):
    """This dialog shows some important details about products like:
    -history of received products
    -history of sales about a determined product
    """

    title = _("Product History")
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
        self.transfer_list.set_columns(self._get_transfer_columns())
        self.retention_list.set_columns(self._get_retention_columns())

        items = ReceivingOrderItem.selectBy(sellableID=self.model.id,
                                            connection=self.conn)
        self.receiving_list.add_list(list(items))

        items = SaleItem.selectBy(sellable=self.model, connection=self.conn)
        self.sales_list.add_list(list(items))

        items = TransferOrderItem.selectBy(sellableID=self.model.id,
                                            connection=self.conn)
        self.transfer_list.add_list(list(items))

        product = IProduct(self.model)
        items = ProductRetentionHistory.selectBy(product=product,
                                                 connection=self.conn)
        self.retention_list.add_list(list(items))

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

        retention_summary_label = SummaryLabel(klist=self.retention_list,
                                               column='quantity',
                                               label=total_label,
                                               value_format=value_format)
        retention_summary_label.show()
        self.retention_vbox.pack_start(retention_summary_label, False)

    def _get_receiving_columns(self):
        return [Column("receiving_order.id",
                       title=_("#"), data_type=int, sorted=True,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("receiving_order.receival_date", title=_("Date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column("receiving_order.id",
                       title=_("Purchase Order"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("receiving_order.supplier_name",
                       title=_("Supplier"), expand=True, data_type=str),
                Column("receiving_order.invoice_number", title=_("Invoice"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column("quantity", title=_("Quantity"),
                       data_type=Decimal,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("unit_description", title=_("Unit"), data_type=str)]

    def _get_sale_columns(self):
        return [Column("sale.id", title=_("#"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       sorted=True),
                Column("sale.open_date",
                       title=_("Date Started"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("sale.client_name",
                       title=_("Client"), expand=True, data_type=str),
                Column("quantity", title=_("Sold"),
                       data_type=int),
                Column("sellable.unit_description",
                       title=_("Unit"), data_type=str)]

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

    def _get_retention_columns(self):
        return [Column("id", title=_("#"), data_type=int,
                        justify=gtk.JUSTIFY_RIGHT, sorted=True),
                Column("reason", title=_(u"Reason"), data_type=str,
                        expand=True),
                Column("quantity", title=_(u"Quantity Retended"),
                        data_type=Decimal)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, ['description'])

        storable = IStorable(self.model)
        self.add_proxy(storable, ['full_balance'])
