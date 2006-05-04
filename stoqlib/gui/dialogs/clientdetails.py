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
""" Classes for client details """

from datetime import date
from decimal import Decimal

import gtk
from kiwi.python import Settable
from kiwi.ui.objectlist import Column
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import SummaryLabel

from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.sale import Sale
from stoqlib.domain.person import PersonAdaptToClient
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext

class ClientDetailsDialog(BaseEditor):
    """This dialog shows some important details about clients like:
        - history of sales
        - all products tied with sales
        - all services tied with sales
        - all payments already created
    """
    title = _("Client Details")
    hide_footer = True
    size = (700, 400)
    model_type = PersonAdaptToClient
    gladefile = "ClientDetailsDialog"
    proxy_widgets = ('client',
                     'last_purchase_date',
                     'status')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()
        # Waiting for bug 2360
        self.further_details_button.set_sensitive(False)

    def _build_data(self, sales):
        self.services = []
        self.payments = []
        product_dict = {}
        for sale_view in sales:
            sale = Sale.get(sale_view.id, connection=self.conn)
            self.services.extend(sale.get_services())
            group = IPaymentGroup(sale, connection=self.conn)
            self.payments.extend(group.get_items())
            for product in sale.get_products():
                qty = product.quantity
                price = product.price
                product_codes = [item.code for item in product_dict.values()]
                sellable = product.sellable
                if not sellable.code in product_codes:
                    desc = sellable.base_sellable_info.description
                    obj = Settable(code=sellable.code, description=desc,
                                   total_qty=qty, total_value=price)
                    product_dict[sellable] = obj
                else:
                    product_dict[sellable].total_qty += qty
        self.products = product_dict.values()

    def _setup_widgets(self):
        self.sales_list.set_columns(self._get_sale_columns())
        self.product_list.set_columns(self._get_product_columns())
        self.services_list.set_columns(self._get_services_columns())
        self.payments_list.set_columns(self._get_payments_columns())

        sales = self.model.get_client_sales()
        self.sales_list.add_list(sales)

        self._build_data(sales)
        self.product_list.add_list(self.products)
        self.services_list.add_list(self.services)
        self.payments_list.add_list(self.payments)

        value_format = '<b>%s</b>'
        total_label = "<b>%s</b>" % _("Total:")
        sales_summary_label = SummaryLabel(klist=self.sales_list,
                                              column='total',
                                              label=total_label,
                                              value_format=value_format)

        sales_summary_label.show()
        self.sales_vbox.pack_start(sales_summary_label, False)

    def _get_sale_columns(self):
        return [Column("order_number", title=_("Order Number"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       width=145, sorted=True),
                Column("open_date", title=_("Date"), data_type=date,
                       justify=gtk.JUSTIFY_RIGHT, width=80),
                Column("salesperson_name", title=_("Salesperson"),
                       searchable=True, expand=True, data_type=str),
                Column("status_name", title=_("Status"), width=80,
                      data_type=str),
                Column("total", title=_("Total"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100)]

    def _get_product_columns(self):
        return [Column("code", title=_("Code"), data_type=int,
                       justify=gtk.JUSTIFY_RIGHT, width=120, sorted=True),
                Column("description", title=_("Description"), data_type=str,
                       expand=True, searchable=True),
                Column("total_qty", title=_("Total Quantity"),
                       data_type=Decimal, width=120),
                Column("total_value", title=_("Total Value"), width=80,
                       data_type=currency)]

    def _get_services_columns(self):
       return [Column("sellable.code", title=_("Code"), data_type=int,
                      justify=gtk.JUSTIFY_RIGHT, width=120, sorted=True),
               Column("sellable.base_sellable_info.description",
                      title=_("Description"), data_type=str, expand=True,
                      searchable=True),
               Column("estimated_fix_date", title=_("Estimated Fix Date"),
                      width=130,data_type=date)]

    def _get_payments_columns(self):
        return [Column("identifier", title=_("Number"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       width=80, sorted=True),
                Column("method.description", title=_("Payment Method"),
                       data_type=str, searchable=True, expand=True),
                Column("due_date", title=_("Due Date"), width=90,
                       data_type=date),
                Column("status_str", title=_("Status"), width=80,
                       data_type=str),
                Column("value", title=_("Value"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100),
                Column("days_late", title=_("Days Late"), width=105,
                       format_func=(lambda days_late: days_late and
                                    str(days_late) or u""),
                       justify=gtk.JUSTIFY_RIGHT, data_type=str)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)
