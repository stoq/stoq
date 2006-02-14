# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Bruno Rafael Garcia             <brg@async.com.br>
##
##
""" Classes for sale details """


import datetime
import gettext

from kiwi.datatypes import currency
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.list import Column, SummaryLabel

from stoqlib.gui.base.dialogs import BasicWrappingDialog
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.lib.validators import get_formatted_price

_ = lambda msg: gettext.dgettext('stoqlib', msg)


class SaleDetailsDialog(SlaveDelegate):
    gladefile = "SaleDetailsDialog"
    title = _("Sale Details")
    size = (650, 460)

    def __init__(self, conn, sale):
        SlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.main_dialog = BasicWrappingDialog(self, self.title,
                                               size=self.size,
                                               hide_footer=True)
        self.sale = sale
        self.conn = conn
        self._setup_widgets()

    def _setup_widgets(self):
        self.details_button.set_sensitive(False)

        #
        # FIXME: These labels must be defined through Kiwi's proxy.
        # Waiting for bug #2366
        #
        salesperson = self.sale.salesperson
        if not salesperson:
            raise DatabaseInconsistency("A sale must have a salesperson.")
        salesperson_name = salesperson.get_adapted().name
        self.salesperson_lbl.set_text(salesperson_name)
        client = self.sale.client
        client_name = (client and client.get_name()
                       or _("<i>Anonymous</i>"))
        self.client_lbl.set_text(client_name)
        
        open_date_str = self.sale.open_date.strftime("%x")
        status_str = self.sale.get_status_name()
        subtotal_str = get_formatted_price(self.sale.get_sale_subtotal())
        discount_value_str = get_formatted_price(self.sale.discount_value)
        surcharge_value_str = get_formatted_price(self.sale.charge_value)
        total_str = get_formatted_price(self.sale.get_total_sale_amount())
        self.open_date_lbl.set_text(open_date_str)
        self.status_lbl.set_text(status_str)
        self.subtotal_lbl.set_text(subtotal_str)
        self.discount_lbl.set_text(discount_value_str)
        self.surcharge_lbl.set_text(surcharge_value_str)
        self.total_lbl.set_text(total_str)
        
        self.items_list.set_columns(self._get_items_columns())
        self.payments_list.set_columns(self._get_payments_columns())
        
        self.items_list.add_list(self.sale.get_items())
        group = IPaymentGroup(self.sale, connection=self.conn)
        self.payments_list.add_list(group.get_items())

        value_format = '<b>%s</b>'
        payments_summary_label = SummaryLabel(klist=self.payments_list,
                                              column='value',
                                              label='<b>Total:</b>',
                                              value_format=value_format)
        payments_summary_label.show()
        self.payments_vbox.pack_start(payments_summary_label, False)

    def _get_payments_columns(self):
        return [Column('payment_number', "#", data_type=int, width=50),
                Column('method.description', _("Method of Payment"),
                       expand=True, data_type=str, width=200),
                Column('due_date', _("Due Date"), sorted=True,
                       data_type=datetime.date, width=120),
                Column('status_str', _("Status"), data_type=str, width=100),
                Column('value', _("Value"), data_type=currency, width=100)]
    
    def _get_items_columns(self):
        return [Column('sellable.code', _("Code"), sorted=True, 
                       data_type=str, width=80),
                Column('sellable.base_sellable_info.description', 
                       _("Description"), data_type=str, expand=True, 
                       width=200),
                Column('quantity', _("Quantity"), data_type=int, width=100), 
                Column('price', _("Price"), data_type=currency, width=100),
                Column('total', _("Total"), data_type=currency, width=100)]

    #
    # BasicDialog Hooks
    #
    
    def on_cancel(self):
        self.main_dialog.close()

    #
    # Kiwi handlers
    #

    def on_details_button__clicked(self, *args):
        # This button will be implemeted after bug 2360 fix.
        pass
