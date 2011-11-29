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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Classes for client details """

import datetime

import gtk
from kiwi.ui.objectlist import Column, ColoredColumn
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import SummaryLabel

from stoqlib.api import api
from stoqlib.domain.interfaces import IClient
from stoqlib.domain.sale import Sale
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize


_ = stoqlib_gettext

class _TemporaryProduct(object):
    """A class to hold information about client's bought products."""

    def __init__(self, product):
        """Initialize the object.

        Note: When creating an instance of this class, you'll have
              to call update_values even for the same product that
              were used to create the instance itself. This is
              done this way so we don't need to wast cpu/ram for
              finding if the product's values weren't updated on
              __init__ themselves.
        """
        self._unit = product.sellable.get_unit_description()
        self.description = product.sellable.get_description()
        self.code = product.sellable.code

        self._quantity = 0
        self.avg_value = 0
        self.total_value = 0

    #
    # Properties
    #

    @property
    def qty_str(self):
        """The string representation of the quantities."""
        return "%s %s" % (self._quantity, self._unit)

    #
    # Public API
    #

    def update_values(self, product):
        self.last_date = product.sale.confirm_date or product.sale.open_date
        self._quantity += product.quantity
        self.total_value += product.price * product.quantity
        self.avg_value = self.total_value / self._quantity


class ClientDetailsDialog(BaseEditor):
    """This dialog shows some important details about clients like:
        - history of sales
        - all products tied with sales
        - all services tied with sales
        - all payments already created
    """
    title = _(u"Client Details")
    hide_footer = True
    size = (780, 400)
    model_iface = IClient
    gladefile = "ClientDetailsDialog"
    proxy_widgets = ('client',
                     'last_purchase_date',
                     'status')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _build_data(self, sales):
        self.services = []
        self.payments = []
        product_dict = {}
        for sale_view in sales:
            sale = Sale.get(sale_view.id, connection=self.conn)
            self.services.extend(sale.services)
            self.payments.extend(sale.payments)
            for product in sale.products:
                p = product_dict.setdefault(product.sellable,
                                            _TemporaryProduct(product))
                p.update_values(product)

        self.products = product_dict.values()

    def _setup_widgets(self):
        self.sales_list.set_columns(self._get_sale_columns())
        self.product_list.set_columns(self._get_product_columns())
        self.services_list.set_columns(self._get_services_columns())
        self.payments_list.set_columns(self._get_payments_columns())
        self.calls_list.set_columns(self._get_calls_columns())

        sales = self.model.get_client_sales()
        self.sales_list.add_list(sales)

        self._build_data(sales)
        self.product_list.add_list(self.products)
        self.services_list.add_list(self.services)
        self.payments_list.add_list(self.payments)
        self.calls_list.add_list(self.model.person.calls)

        value_format = '<b>%s</b>'
        total_label = "<b>%s</b>" % _("Total:")
        sales_summary_label = SummaryLabel(klist=self.sales_list,
                                              column='total',
                                              label=total_label,
                                              value_format=value_format)

        sales_summary_label.show()
        self.sales_vbox.pack_start(sales_summary_label, False)

    def _get_sale_columns(self):
        return [Column("id", title=_("#"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       format='%04d', width=90, sorted=True),
                Column("invoice_number", title=_("Invoice #"),
                       data_type=int, width=90),
                Column("open_date", title=_("Date"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT, width=80),
                Column("salesperson_name", title=_("Salesperson"),
                       searchable=True, expand=True, data_type=str),
                Column("status_name", title=_("Status"), width=80,
                      data_type=str),
                Column("total", title=_("Total"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100)]

    def _get_product_columns(self):
        return [Column("code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=120, sorted=True),
                Column("description", title=_("Description"), data_type=str,
                       expand=True, searchable=True),
                Column("qty_str", title=_("Total quantity"),
                       data_type=str, width=120, justify=gtk.JUSTIFY_RIGHT),
                Column("last_date", title=_("Lastest purchase"),
                       data_type=datetime.date, width=150),
                Column("avg_value", title=_("Avg. value"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT),
                Column("total_value", title=_("Total value"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT, )]

    def _get_services_columns(self):
        return [Column("sellable.code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=120, sorted=True),
                Column("sellable.base_sellable_info.description",
                       title=_("Description"), data_type=str, expand=True,
                       searchable=True),
                Column("estimated_fix_date", title=_("Estimated fix date"),
                       width=150, data_type=datetime.date)]

    def _get_payments_columns(self):
        return [Column("id", title=_("#"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT,
                       format='%04d', width=50),
                Column("method.description", title=_("Type"),
                       data_type=str, width=90),
                Column("description", title=_("Description"),
                       data_type=str, searchable=True, width=190,
                       expand=True),
                Column("due_date", title=_("Due date"), width=110,
                       data_type=datetime.date, sorted=True),
                Column("paid_date", title=_("Paid date"), width=110,
                       data_type=datetime.date),
                Column("status_str", title=_("Status"), width=80,
                       data_type=str),
                ColoredColumn("base_value", title=_("Value"),
                              justify=gtk.JUSTIFY_RIGHT, data_type=currency,
                              color='red', width=100,
                              data_func=payment_value_colorize),
                Column("days_late", title=_("Days Late"), width=110,
                       format_func=(lambda days_late: days_late and
                                    str(days_late) or u""),
                       justify=gtk.JUSTIFY_RIGHT, data_type=str)]

    def _get_calls_columns(self):
        return [Column("date", title=_("Date"),
                       data_type=datetime.date, width=150, sorted=True),
                Column("description", title=_("Description"),
                       data_type=str, width=150, expand=True),
                Column("attendant.person.name", title=_("Attendant"),
                       data_type=str, width=100, expand=True)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)

    #
    # Callbacks
    #

    def on_further_details_button__clicked(self, *args):
        trans = api.new_transaction()
        run_person_role_dialog(ClientEditor, self, trans,
                               self.model, visual_mode=True)
        api.finish_transaction(trans, False)
