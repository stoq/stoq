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

from stoqlib.domain.person import CreditProvider
from stoqlib.domain.sale import SaleView
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.editors.paymenteditor import LonelyPaymentDetailsDialog
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.search.paymentsearch import CardPaymentSearch
from stoqlib.reporting.payment import CardPaymentReport


class TestPaymentSearch(GUITest):
    def _show_search(self):
        search = CardPaymentSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        pay = self.create_card_payment(date=datetime.datetime(2012, 1, 1),
                                         provider_id='VISANET')
        client = self.create_client(name='Dane Cook')
        sale = self.create_sale(client=client)
        self.create_sale_item(sale=sale)
        pay.group = sale.group
        pay.identifier = 55555

        pay = self.create_card_payment(date=datetime.datetime(2012, 2, 2),
                                         provider_id='AMEX')
        client = self.create_client(name='Carmen Sandiego')
        sale = self.create_sale(client=client)
        pay.group = sale.group
        sale.group.sale = sale
        pay.identifier = 66666

        pay = self.create_card_payment(date=datetime.datetime(2012, 3, 3),
                                         provider_id='VISANET')
        self.create_payment_renegotiation(group=pay.group)
        pay.identifier = 77777

        pay = self.create_card_payment(date=datetime.datetime(2012, 4, 4),
                                         provider_id='VISANET')
        pay.identifier = 88888

    def testCardPaymentSearch(self):
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
        provider = CreditProvider.selectOneBy(provider_id='AMEX',
                                              connection=self.trans)
        search.provider_filter.set_state(provider)
        search.search.refresh()
        self.check_search(search, 'card-payment-provider-filter')

    @mock.patch('stoqlib.gui.search.paymentsearch.print_report')
    @mock.patch('stoqlib.gui.search.paymentsearch.run_dialog')
    def testButtons(self, run_dialog, print_report):
        self._create_domain()
        search = self._show_search()

        search.search.refresh()
        self.assertNotSensitive(search._details_slave, ['details_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])

        self.click(search._details_slave.details_button)
        sale_view = SaleView.select(SaleView.q.id == search.results[0].sale_id,
                                    connection=self.trans)[0]
        run_dialog.assert_called_once_with(SaleDetailsDialog, search,
                                           self.trans, sale_view)

        run_dialog.reset_mock()
        search.results.select(search.results[2])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(RenegotiationDetailsDialog, search,
                                           self.trans,
                                           search.results[2].renegotiation)

        run_dialog.reset_mock()
        search.results.select(search.results[3])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(LonelyPaymentDetailsDialog, search,
                                           self.trans,
                                           search.results[3].payment)

        self.assertSensitive(search._details_slave, ['print_button'])
        self.click(search._details_slave.print_button)
        print_report.assert_called_once_with(CardPaymentReport, search.results,
                                    list(search.results),
                                    filters=search.search.get_search_filters())
