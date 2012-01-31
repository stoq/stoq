# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2010 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for payment objects """

import datetime
from decimal import Decimal

import gtk

from kiwi.datatypes import currency
from kiwi.ui.objectlist import SearchColumn

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import SaleView
from stoqlib.domain.payment.views import (InCheckPaymentView,
                                          OutCheckPaymentView,
                                          CardPaymentView)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.editors.paymenteditor import LonelyPaymentDetailsDialog
from stoqlib.gui.printing import print_report
from stoqlib.reporting.payment import (BillCheckPaymentReport,
                                       CardPaymentReport)

_ = stoqlib_gettext


class _BaseBillCheckSearch(SearchDialog):

    title = _(u"Bill & Check Payments Search")
    size = (750, 500)
    searching_by_date = True
    selection_mode = gtk.SELECTION_MULTIPLE

    def _get_status_values(self):
        items = [(value, key) for key, value in
                 Payment.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['payment_number', 'account'])

        self.set_searchbar_labels(_(u'Bill or check number:'))

    def get_columns(self):
        return [SearchColumn('id', title=_('#'), data_type=int, sorted=True,
                             format='%04d', long_title=_('Id'), width=55),
                SearchColumn('method_description', title=_(u'Method'),
                             data_type=str, width=90),
                SearchColumn('payment_number', title=_(u'Number'),
                             data_type=str, width=100),
                SearchColumn('due_date', title=_('Due date'),
                             data_type=datetime.date,
                             width=120),
                SearchColumn('paid_date', title=_('Paid date'),
                             data_type=datetime.date,
                             width=120),
                SearchColumn('status_str', title=_('Status'), data_type=str,
                             valid_values=self._get_status_values(),
                             search_attribute='status'),
                SearchColumn('value', title=_('Value'), data_type=currency)]

    def _print_report(self):
        payments = self.results.get_selected_rows() or list(self.results)
        print_report(BillCheckPaymentReport, self.results, payments,
                     filters=self.search.get_search_filters())

    #
    # Callbacks
    #

    def on_print_button_clicked(self, widget):
        self._print_report()


class InPaymentBillCheckSearch(_BaseBillCheckSearch):
    table = InCheckPaymentView


class OutPaymentBillCheckSearch(_BaseBillCheckSearch):
    table = OutCheckPaymentView


class CardPaymentSearch(SearchDialog):

    title = _(u"Card Payment Search")
    size = (750, 500)
    searching_by_date = True
    search_table = CardPaymentView
    selection_mode = gtk.SELECTION_BROWSE

    def __init__(self, conn):
        SearchDialog.__init__(self, conn, self.search_table,
                              title=self.title)
        self.set_details_button_sensitive(False)
        self.results.connect('selection-changed', self.on_selection_changed)

    #
    #SearchDialogs Hooks
    #

    def _get_status_values(self):
        values = [(v, k) for k, v in Payment.statuses.items()]
        values.insert(0, (_("Any"), None))
        return values

    def create_filters(self):
        self.set_text_field_columns(['drawee_name'])
        self.set_searchbar_labels(_(u'Client:'))
        self.executer.set_query(self.executer_query)

        #Provider
        provider_filter = self.create_provider_filter(_('Provider:'))
        self.add_filter(provider_filter, columns=[])
        self.provider_filter = provider_filter

    def get_columns(self):
        return [SearchColumn('id', title=_('#'), data_type=int,
                             sorted=True, format='%04d', long_title=_('Id')),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, expand=True),
                SearchColumn('drawee_name', title=_(u'Drawee'), data_type=str,
                             expand=True),
                SearchColumn('provider_name', title=_(u'Credit provider'),
                             data_type=str, expand=True),
                SearchColumn('due_date', title=_(u'Due date'),
                             data_type=datetime.date),
                SearchColumn('paid_date', title=_(u'Paid date'), visible=False,
                             data_type=datetime.date),
                SearchColumn('status_str', title=_(u'Status'), data_type=str,
                             expand=True, search_attribute='status',
                             valid_values=self._get_status_values()),
                SearchColumn('value', title=_(u'Value'), data_type=currency),
                SearchColumn('fee', title=_(u'% Fee'),
                             data_type=Decimal),
                SearchColumn('fee_calc', title=_(u'Fee'),
                             data_type=currency)]

    def executer_query(self, query, having, conn):
        provider = self.provider_filter.get_state().value
        return self.search_table.select_by_provider(query, provider,
                                                    connection=conn)

    def _print_report(self):
        print_report(CardPaymentReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())

    def on_selection_changed(self, results, selected):
        can_details = bool(selected)
        self.set_details_button_sensitive(can_details)

    #
    #Private
    #

    def _show_details(self, receivable_view):
        if receivable_view.sale_id is not None:
            sale_view = SaleView.select(
                    SaleView.q.id == receivable_view.sale_id)[0]
            run_dialog(SaleDetailsDialog, self, self.conn, sale_view)
        elif receivable_view.renegotiation_id is not None:
            run_dialog(RenegotiationDetailsDialog, self, self.conn,
                       receivable_view.renegotiation)
        else:
            payment = receivable_view.payment
            run_dialog(LonelyPaymentDetailsDialog, self, self.conn, payment)

    #
    #Callbacks
    #

    def on_print_button_clicked(self, widget):
        self._print_report()

    def on_details_button_clicked(self, button):
        selected = self.results.get_selected()
        self._show_details(selected)
