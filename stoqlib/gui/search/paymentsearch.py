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

from kiwi.currency import currency
from kiwi.ui.objectlist import Column

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import SaleView
from stoqlib.domain.payment.card import CardPaymentDevice, CreditCardData
from stoqlib.domain.payment.views import (InCheckPaymentView,
                                          OutCheckPaymentView,
                                          CardPaymentView)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.editors.paymenteditor import LonelyPaymentDetailsDialog
from stoqlib.gui.editors.paymentmethodeditor import CardPaymentDetailsEditor
from stoqlib.gui.utils.printing import print_report
from stoqlib.reporting.payment import (BillCheckPaymentReport,
                                       CardPaymentReport)

_ = stoqlib_gettext


class _BaseBillCheckSearch(SearchDialog):

    title = _(u"Bill & Check Payments Search")
    size = (-1, 500)
    selection_mode = gtk.SELECTION_MULTIPLE
    report_class = BillCheckPaymentReport
    search_label = _(u'Bill or check number:')
    branch_filter_column = Payment.branch_id

    def _get_status_values(self):
        items = [(value, key) for key, value in
                 Payment.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
                Column('method_description', title=_(u'Method'),
                       data_type=str, expand=True),
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

    def print_report(self):
        payments = self.results.get_selected_rows() or list(self.results)
        print_report(self.report_class, self.results, payments,
                     filters=self.search.get_search_filters())


class InPaymentBillCheckSearch(_BaseBillCheckSearch):
    search_spec = InCheckPaymentView
    text_field_columns = [InCheckPaymentView.payment_number,
                          InCheckPaymentView.bank_account]


class OutPaymentBillCheckSearch(_BaseBillCheckSearch):
    search_spec = OutCheckPaymentView
    text_field_columns = [OutCheckPaymentView.payment_number,
                          OutCheckPaymentView.bank_account]

    def get_columns(self):
        columns = _BaseBillCheckSearch.get_columns(self)
        columns.append(
            SearchColumn('bill_received', title=_('Bill received'),
                         data_type=bool, visible=False)
        )
        return columns


class CardPaymentSearch(SearchEditor):
    title = _(u"Card Payment Search")
    size = (850, 500)
    search_spec = CardPaymentView
    editor_class = CardPaymentDetailsEditor
    report_class = CardPaymentReport
    search_label = (u'Client:')
    selection_mode = gtk.SELECTION_BROWSE
    text_field_columns = [CardPaymentView.drawee_name,
                          CardPaymentView.identifier_str]
    branch_filter_column = Payment.branch_id

    def __init__(self, store):
        SearchEditor.__init__(self, store)
        self.set_details_button_sensitive(False)
        self.hide_new_button()

    def _get_status_values(self):
        values = [(v, k) for k, v in Payment.statuses.items()]
        values.insert(0, (_("Any"), None))
        return values

    def _get_device_values(self):
        devices = CardPaymentDevice.get_devices(self.store)
        # This is used in a int filter, so we must use the id
        values = [(d.description, d.id) for d in devices]
        values.insert(0, (_("Any"), None))
        return values

    #
    # SearchDialogs Hooks
    #

    def create_filters(self):
        provider_filter = self.create_provider_filter(_('Provider:'))
        self.add_filter(provider_filter, columns=[CreditCardData.provider])
        self.provider_filter = provider_filter

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, payment_card_view):
        return payment_card_view.credit_card_data

    def get_columns(self):
        # TODO: Adicionar filtro por card_type
        return [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, expand=True),
                SearchColumn('drawee_name', title=_(u'Drawee'), data_type=str,
                             expand=True),
                SearchColumn('device_name', title=_(u'Card Device'),
                             data_type=str, visible=False,
                             search_attribute='device_id',
                             valid_values=self._get_device_values()),
                SearchColumn('provider_name', title=_(u'Provider'),
                             data_type=str),
                SearchColumn('due_date', title=_(u'Due date'),
                             data_type=datetime.date),
                SearchColumn('paid_date', title=_(u'Paid date'), visible=False,
                             data_type=datetime.date),
                SearchColumn('status_str', title=_(u'Status'), data_type=str,
                             expand=True, search_attribute='status',
                             valid_values=self._get_status_values()),
                SearchColumn('value', title=_(u'Value'), data_type=currency),
                SearchColumn('fare', title=_(u'Fare'), data_type=currency),
                SearchColumn('fee', title=_(u'% Fee'), data_type=Decimal,
                             visible=False),
                SearchColumn('fee_calc', title=_(u'Fee'), data_type=currency),
                SearchColumn('auth', title=_(u'Authorization'), data_type=int,
                             visible=False)]

    def row_activate(self, obj):
        selected = self.results.get_selected()
        self._show_details(selected)

    def on_results__selection_changed(self, results, selected):
        can_details = bool(selected)
        self.set_details_button_sensitive(can_details)

    #
    # Private
    #

    def _show_details(self, receivable_view):
        if receivable_view.sale_id is not None:
            sale_view = self.store.find(SaleView, id=receivable_view.sale_id).one()
            run_dialog(SaleDetailsDialog, self, self.store, sale_view)
        elif receivable_view.renegotiation_id is not None:
            run_dialog(RenegotiationDetailsDialog, self, self.store,
                       receivable_view.renegotiation)
        else:
            payment = receivable_view.payment
            run_dialog(LonelyPaymentDetailsDialog, self, self.store, payment)

    #
    # Callbacks
    #

    def on_details_button_clicked(self, button):
        selected = self.results.get_selected()
        self._show_details(selected)
