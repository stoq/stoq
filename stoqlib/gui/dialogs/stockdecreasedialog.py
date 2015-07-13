# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010-2014 Async Open Source <http://www.async.com.br>
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
""" Classes for Stock Decrease Details Dialog """

import datetime

import gtk
from kiwi.ui.objectlist import Column, SummaryLabel
from kiwi.currency import currency
import pango

from stoqlib.api import api
from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.stockdecrease import StockDecreaseReceipt

_ = stoqlib_gettext


class StockDecreaseDetailsDialog(BaseEditor):
    title = _(u"Manual Stock Decrease Details")
    hide_footer = True
    size = (700, 400)
    model_type = StockDecrease
    report_class = StockDecreaseReceipt
    gladefile = "StockDecreaseDetails"
    proxy_widgets = ('identifier',
                     'confirm_date',
                     'branch_name',
                     'responsible_name',
                     'removed_by_name',
                     'cfop_description',
                     'reason',
                     'invoice_number')

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_list.set_columns(self._get_product_columns())
        # if the parameter is on we have to build the summary
        if api.sysparam.get_bool("CREATE_PAYMENTS_ON_STOCK_DECREASE"):
            value_format = '<b>%s</b>'
            total_cost_label = value_format % api.escape(_("Total cost:"))
            products_cost_summary_label = SummaryLabel(klist=self.product_list,
                                                       column='total_cost',
                                                       label=total_cost_label,
                                                       value_format=value_format)
            products_cost_summary_label.show()
            self.products_vbox.pack_start(products_cost_summary_label, False)
        products = self.store.find(StockDecreaseItem, stock_decrease=self.model)
        self.product_list.add_list(list(products))

        if self.model.group:
            self.payment_list.set_columns(self._get_payment_columns())
            self.payment_list.add_list(list(self.model.group.payments))
        else:
            self.notebook.remove_page(2)

    def _get_payment_columns(self):
        return [IdentifierColumn("identifier", title=_('Payment #')),
                Column("method.description", title=_("Type"),
                       data_type=str),
                Column("description", title=_("Description"),
                       data_type=str),
                Column("due_date", title=_("Due date"),
                       data_type=datetime.date),
                Column("paid_date", title=_("Paid date"),
                       data_type=datetime.date),
                Column("value", title=_("Value"),
                       data_type=currency),
                Column("paid_value", title=_("Paid value"),
                       data_type=currency),
                ]

    def _get_product_columns(self):
        columns = [Column("sellable.code", title=_("Code"), data_type=str,
                          justify=gtk.JUSTIFY_RIGHT, ellipsize=pango.ELLIPSIZE_END),
                   Column("sellable.description", title=_("Description"),
                          data_type=str, expand=True),
                   Column('batch.batch_number', title=_("Batch"),
                          data_type=str),
                   Column("quantity", title=_("Qty"),
                          data_type=int, justify=gtk.JUSTIFY_RIGHT),
                   ]
        if api.sysparam.get_bool("CREATE_PAYMENTS_ON_STOCK_DECREASE"):
            columns.append(Column('total_cost', title=_("Cost"),
                                  data_type=currency))
        return columns

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    # Callbacks
    #

    def on_print_button__clicked(self, button):
        print_report(self.report_class, self.model)
