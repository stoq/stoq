# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""A details dialog for a |costcenter| object"""

import datetime
from decimal import Decimal
import gtk

from kiwi.currency import currency
from kiwi.ui.objectlist import Column, SummaryLabel

from stoqlib.api import api
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.domain.costcenter import CostCenter
from stoqlib.domain.sale import SaleView
from stoqlib.domain.stockdecrease import StockDecrease
from stoqlib.domain.views import CostCenterEntryStockView, StockDecreaseView

_ = stoqlib_gettext


class CostCenterDialog(BaseEditor):
    gladefile = "CostCenterDialog"
    model_name = _(u'Cost Center')
    size = (750, 450)
    model_type = CostCenter
    proxy_widgets = ('name_lbl',
                     'budget_lbl',
                     'description_lbl')

    def _get_stock_transactions_columns(self):
        return [Column('date', _('Date'), data_type=datetime.date,
                       sorted=True),
                Column('responsible_name', _('Responsible'),
                       visible=False, data_type=str),
                Column('product_description', _('Product'), data_type=str,
                       expand=True),
                Column('stock_transaction.description', _('Description'), data_type=str,
                       width=140),
                Column('stock_cost', _('Stock cost'), data_type=currency),
                Column('quantity', _('Qty'), data_type=Decimal, format_func=abs),
                Column('total', _('Total'), data_type=currency)]

    def _get_payments_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
                Column('method.description', _("Method"),
                       data_type=str, width=60),
                Column('description', _("Description"), data_type=str,
                       expand=True),
                Column('due_date', _("Due date"), visible=False,
                       data_type=datetime.date, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('paid_date', _("Paid date"),
                       data_type=datetime.date, width=90),
                Column('status_str', _("Status"), data_type=str, width=80),
                Column('value', _("Value"), data_type=currency,
                       justify=gtk.JUSTIFY_RIGHT, visible=False),
                Column('paid_value', _("Paid value"), data_type=currency,
                       justify=gtk.JUSTIFY_RIGHT)]

    def _get_sales_columns(self):
        return [IdentifierColumn('identifier', title=_('Sale #'), sorted=True),
                Column('client_name', title=_('Client'),
                       data_type=unicode, expand=True),
                Column('branch_name', title=_('Branch'),
                       data_type=unicode, visible=False),
                Column('open_date', title=_('Open date'), width=120,
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT,
                       visible=False),
                Column('confirm_date', title=_('Confirm date'),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT,
                       width=120),
                Column('total', title=_('Total'), data_type=currency,
                       width=120)]

    def _get_stock_decrease_columns(self):
        return [IdentifierColumn('identifier', title=('Decrease #'), sorted=True),
                Column('confirm_date', _('Date'),
                       data_type=datetime.date, width=100),
                Column('branch_name', _('Branch'),
                       data_type=unicode, expand=True),
                Column('removed_by_name', _('Removed By'),
                       data_type=unicode, width=120)]

    def _setup_columns(self):
        self.payments_list.set_columns(self._get_payments_columns())
        self.stock_transactions_list.set_columns(
            self._get_stock_transactions_columns())
        self.sales_list.set_columns(self._get_sales_columns())
        self.stock_decreases_list.set_columns(self._get_stock_decrease_columns())

    def _setup_summary_labels(self):
        value_format = "<b>%s</b>"
        total_label = "<b>%s</b>" % api.escape(_("Total:"))
        total_summary_label = SummaryLabel(klist=self.payments_list,
                                           column='value',
                                           label=total_label,
                                           value_format=value_format)
        total_summary_label.show()
        self.payments_vbox.pack_start(total_summary_label, False)

        total_label = "<b>%s</b>" % api.escape(_("Total paid:"))
        total_paid_summary_label = SummaryLabel(klist=self.payments_list,
                                                column='paid_value',
                                                label=total_label,
                                                value_format=value_format)
        total_paid_summary_label.show()
        self.payments_vbox.pack_start(total_paid_summary_label, False)

        total_label = "<b>%s</b>" % api.escape(_("Total:"))
        transaction_summary_label = SummaryLabel(
            klist=self.stock_transactions_list,
            column='total',
            label=total_label,
            value_format=value_format)
        transaction_summary_label.show()
        self.stock_transactions_vbox.pack_start(transaction_summary_label, False)

        total_label = "<b>%s</b>" % api.escape(_("Total:"))
        sale_summary_label = SummaryLabel(klist=self.sales_list,
                                          column='total',
                                          label=total_label,
                                          value_format=value_format)
        sale_summary_label.show()
        self.sales_vbox.pack_start(sale_summary_label, False)

    def _setup_widgets(self):
        self._setup_columns()

        # stock transactions
        items = self.store.find(CostCenterEntryStockView,
                                CostCenterEntryStockView.cost_center_id == self.model.id)
        self.stock_transactions_list.add_list(list(items))

        # payments
        self.payments_list.add_list(list(self.model.get_payments()))

        # sales
        sales = self.store.find(SaleView, SaleView.sale.cost_center == self.model)
        self.sales_list.add_list(list(sales))

        # stock decreases
        items = self.store.find(StockDecreaseView,
                                StockDecrease.cost_center == self.model)
        self.stock_decreases_list.add_list(list(items))

        self._setup_summary_labels()

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, self.proxy_widgets)


def test():  # pragma: no cover
    from stoqlib.gui.base.dialogs import run_dialog

    ec = api.prepare_test()
    model = ec.store.find(CostCenter).any()
    run_dialog(CostCenterDialog, None, ec.store, model)


if __name__ == '__main__':
    test()
