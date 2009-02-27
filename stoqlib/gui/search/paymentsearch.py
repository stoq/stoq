# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
##  Author(s): George Kussumoto   <george@async.com.br>
##
##
""" Search dialogs for payment objects """

import datetime

import gtk

from kiwi.datatypes import currency
from kiwi.ui.search import DateSearchFilter
from kiwi.ui.objectlist import SearchColumn

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InCheckPaymentView, OutCheckPaymentView
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.printing import print_report
from stoqlib.reporting.payment import BillCheckPaymentReport

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
        return [SearchColumn('id', title=_('#'), data_type=int,
                             sorted=True, format='%04d', long_title='Id'),
                SearchColumn('bank_id', title=_(u'Bank'), data_type=int,
                             format='%03d'),
                SearchColumn('branch', title=_(u'Branch Number'), data_type=str,
                             expand=True),
                SearchColumn('account', title=_(u'Account'), data_type=str,
                             expand=True),
                SearchColumn('payment_number', title=_(u'Number'), data_type=str,
                             expand=True),
                SearchColumn('due_date', title=_('Due Date'),
                             data_type=datetime.date),
                SearchColumn('paid_date', title=_('Paid Date'),
                             data_type=datetime.date),
                SearchColumn('status_str', title=_('Status'), data_type=str,
                             valid_values=self._get_status_values(),
                             search_attribute='status'),
                SearchColumn('value', title=_('Value'), data_type=currency)]

    def _print_report(self):
        print_report(BillCheckPaymentReport, self.results,
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
