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
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ColoredColumn
from kiwi.ui.gadgets import render_pixbuf
from kiwi.ui.widgets.list import SummaryLabel

from stoqlib.api import api
from stoqlib.domain.person import Client
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.utils.workorderutils import get_workorder_state_icon


_ = stoqlib_gettext


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
    model_type = Client
    gladefile = "ClientDetailsDialog"
    proxy_widgets = ('client',
                     'last_purchase_date',
                     'status')

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.sales_list.set_columns(self._get_sale_columns())
        self.returned_sales_list.set_columns(self._get_returned_sale_columns())
        self.product_list.set_columns(self._get_product_columns())
        self.services_list.set_columns(self._get_services_columns())
        self.work_order_list.set_columns(self._get_work_order_columns())
        self.payments_list.set_columns(self._get_payments_columns())
        self.calls_list.set_columns(self._get_calls_columns())
        self.account_list.set_columns(self._get_account_columns())
        self.sales_list.add_list(self.model.get_client_sales())
        self.returned_sales_list.add_list(self.model.get_client_returned_sales())
        self.product_list.add_list(self.model.get_client_products())
        self.services_list.add_list(self.model.get_client_services())
        self.work_order_list.add_list(self.model.get_client_work_orders())
        self.payments_list.add_list(self.model.get_client_payments())
        self.calls_list.add_list(self.model.person.calls)
        self.account_list.add_list(self.model.get_credit_transactions())
        value_format = '<b>%s</b>'
        total_label = "<b>%s</b>" % api.escape(_("Total:"))
        saldo_label = "<b>%s</b>" % api.escape(_("Balance:"))

        sales_summary_label = SummaryLabel(klist=self.sales_list,
                                           column='total',
                                           label=total_label,
                                           value_format=value_format)
        account_summary_label = SummaryLabel(klist=self.account_list,
                                             column='paid_value',
                                             label=saldo_label,
                                             value_format=value_format,
                                             data_func=lambda p: p.is_outpayment())

        sales_summary_label.show()
        account_summary_label.show()
        self.sales_vbox.pack_start(sales_summary_label, False)
        self.account_vbox.pack_start(account_summary_label, False)

    def _get_sale_columns(self):
        return [IdentifierColumn('identifier', sorted=True),
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

    def _get_returned_sale_columns(self):
        return [IdentifierColumn('identifier', sorted=True),
                Column("invoice_number", title=_("Invoice #"),
                       data_type=int, width=90),
                Column("return_date", title=_("Return Date"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT, width=80),
                Column("product_name", title=_("Product"),
                       searchable=True, data_type=str),
                Column("salesperson_name", title=_("Salesperson"),
                       searchable=True, visible=False, data_type=str),
                Column("responsible_name", title=_("Responsible"),
                       searchable=True, data_type=str),
                Column("reason", title=_("Reason"), searchable=False, expand=True, data_type=str),
                Column("total", title=_("Total"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100)]

    def _get_product_columns(self):
        return [Column("code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=120, sorted=True),
                Column("description", title=_("Description"), data_type=str,
                       expand=True, searchable=True),
                Column("quantity", title=_("Total quantity"),
                       data_type=str, width=120, justify=gtk.JUSTIFY_RIGHT),
                Column("last_date", title=_("Lastest purchase"),
                       data_type=datetime.date, width=150),
                Column("avg_value", title=_("Avg. value"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT),
                Column("total_value", title=_("Total value"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT, )]

    def _get_services_columns(self):
        return [Column("code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=120, sorted=True),
                Column("description",
                       title=_("Description"), data_type=str, expand=True,
                       searchable=True),
                Column("estimated_fix_date", title=_("Estimated fix date"),
                       width=150, data_type=datetime.date)]

    def _get_payments_columns(self):
        return [IdentifierColumn('identifier'),
                Column("method_name", title=_("Type"),
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
                ColoredColumn("value", title=_("Value"),
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

    def _get_account_columns(self):
        return [IdentifierColumn('identifier', sorted=True),
                Column('paid_date', title=_(u'Date'), data_type=datetime.date,
                       width=150),
                Column('description', title=_(u'Description'),
                       data_type=str, width=150, expand=True),
                ColoredColumn('paid_value', title=_(u'Value'), color='red',
                              data_type=currency, width=100,
                              use_data_model=True,
                              data_func=lambda p: not p.is_outpayment())]

    def _get_work_order_columns(self):
        return [IdentifierColumn("identifier", sorted=True),
                Column("equipment", title=_("Equipment"),
                       data_type=str, expand=True, pack_end=True),
                Column('category_color', title=_(u'Equipment'),
                       column='equipment', data_type=gtk.gdk.Pixbuf,
                       format_func=render_pixbuf),
                Column('flag_icon', title=_(u'Equipment'), column='equipment',
                       data_type=gtk.gdk.Pixbuf, format_func_data=True,
                       format_func=self._format_state_icon),
                Column("open_date", title=_("Open date"),
                       data_type=datetime.date, width=120),
                Column("approve_date", title=_("Approve date"),
                       data_type=datetime.date, width=120),
                Column("finish_date", title=_("Finish date"),
                       data_type=datetime.date, width=120),
                Column("total", title=_("Total"),
                       data_type=currency, width=100)]

    def _format_state_icon(self, item, data):
        stock_id, tooltip = get_workorder_state_icon(item.work_order)
        if stock_id is not None:
            # We are using self.sales_vbox because render_icon is a
            # gtk.Widget's # method. It has nothing to do with results tough.
            return self.sales_vbox.render_icon(stock_id, gtk.ICON_SIZE_MENU)

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)

    #
    # Callbacks
    #

    def on_further_details_button__clicked(self, *args):
        store = api.new_store()
        model = store.fetch(self.model)
        run_person_role_dialog(ClientEditor, self, store,
                               model, visual_mode=True)
        store.confirm(False)
        store.close()
