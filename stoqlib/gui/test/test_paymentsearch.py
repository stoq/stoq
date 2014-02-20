# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime

import mock

from stoqlib.domain.payment.card import CreditProvider
from stoqlib.domain.sale import SaleView
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.paymenteditor import LonelyPaymentDetailsDialog
from stoqlib.gui.search.paymentsearch import CardPaymentSearch
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.reporting.payment import CardPaymentReport


class TestPaymentSearch(GUITest):
    def _show_search(self):
        search = CardPaymentSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        pay = self.create_card_payment(date=datetime.datetime(2012, 1, 1),
                                       provider_id=u'VISANET')
        client = self.create_client(name=u'Dane Cook')
        sale = self.create_sale(client=client)
        self.create_sale_item(sale=sale)
        pay.group = sale.group
        pay.identifier = 55555

        pay = self.create_card_payment(date=datetime.datetime(2012, 2, 2),
                                       provider_id=u'AMEX')
        client = self.create_client(name=u'Carmen Sandiego')
        sale = self.create_sale(client=client)
        pay.group = sale.group
        sale.group.sale = sale
        pay.identifier = 66666

        pay = self.create_card_payment(date=datetime.datetime(2012, 3, 3),
                                       provider_id=u'VISANET')
        self.create_payment_renegotiation(group=pay.group)
        pay.identifier = 77777

        pay = self.create_card_payment(date=datetime.datetime(2012, 4, 4),
                                       provider_id=u'VISANET')
        pay.identifier = 88888

    def test_card_payment_search(self):
        self._create_domain()
        search = self._show_search()

        # Empty filters.
        self.check_search(search, 'card-payment-no-filter')

        # Filtering by client.
        search.set_searchbar_search_string('dan')
        search.search.refresh()
        self.check_search(search, 'card-payment-string-filter')

        # Filtering by credit provider.
        search.set_searchbar_search_string('')
        provider = self.store.find(CreditProvider, provider_id=u'AMEX').one()
        search.provider_filter.set_state(provider)
        search.search.refresh()
        self.check_search(search, 'card-payment-provider-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    @mock.patch('stoqlib.gui.search.paymentsearch.run_dialog')
    def test_buttons(self, run_dialog, print_report):
        self._create_domain()
        search = self._show_search()

        search.search.refresh()
        self.assertNotSensitive(search._details_slave, ['details_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])

        self.click(search._details_slave.details_button)
        sale_view = self.store.find(SaleView, id=search.results[0].sale_id).one()
        run_dialog.assert_called_once_with(SaleDetailsDialog, search,
                                           self.store, sale_view)

        run_dialog.reset_mock()
        search.results.select(search.results[2])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(RenegotiationDetailsDialog, search,
                                           self.store,
                                           search.results[2].renegotiation)

        run_dialog.reset_mock()
        search.results.select(search.results[3])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(LonelyPaymentDetailsDialog, search,
                                           self.store,
                                           search.results[3].payment)

        self.assertSensitive(search._details_slave, ['print_button'])
        self.click(search._details_slave.print_button)
        print_report.assert_called_once_with(CardPaymentReport, search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())
