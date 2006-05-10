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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Search dialogs for purchase receiving"""

import datetime

import gtk
from kiwi.datatypes import currency

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.columns import Column
from stoqlib.gui.base.search import SearchDialog
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.reporting.purchase_receival import PurchaseReceivalReport

_ = stoqlib_gettext


class PurchaseReceivingSearch(SearchDialog):
    title = _('Purchase Receiving Search')
    size = (750, 500)
    table = ReceivingOrder
    selection_mode = gtk.SELECTION_MULTIPLE
    searching_by_date = True
    searchbar_labels = _('Receiving Orders Matching:'), None
    searchbar_result_strings = _('receiving order'), _('receiving orders')

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [Column('receiving_number_str', _('#'), data_type=unicode,
                       width=80,),
                Column('receival_date', _('Receival Date'),
                       data_type=datetime.date, sorted=True, width=130),
                Column('order_number', _('Purchase Order #'), data_type=unicode,
                       width=130),
                Column('supplier_name', _('Supplier'), data_type=unicode,
                       expand=True),
                Column('branch_name', _('Branch'), data_type=unicode,
                       width=90, visible=False),
                Column('invoice_number', _('Invoice #'), data_type=int,
                       width=80),
                Column('invoice_total', _('Invoice Total'),
                       data_type=currency, width=120)]

    #
    # Callbacks
    #

    def on_print_button_clicked(self, *args):
        self.search_bar.print_report(PurchaseReceivalReport, list(self.klist))
