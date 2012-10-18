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

from stoqlib.domain.person import CreditProvider
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.search.paymentsearch import CardPaymentSearch


class TestPaymentSearch(GUITest):
    def testCardPaymentSearch(self):
        pay_a = self.create_card_payment(date=datetime.datetime(2012, 1, 1),
                                         provider_id='VISANET')
        pay_b = self.create_card_payment(date=datetime.datetime(2012, 2, 2),
                                         provider_id='AMEX')

        client = self.create_client(name='Dane Cook')
        sale = self.create_sale(client=client)
        pay_a.group = sale.group

        client = self.create_client(name='Carmen Sandiego')
        sale = self.create_sale(client=client)
        pay_b.group = sale.group

        pay_a.identifier = 75946
        pay_b.identifier = 74582

        search = CardPaymentSearch(self.trans)

        # Empty filters.
        search.search.refresh()
        self.check_search(search, 'card-payment-no-filter')

        # Filtering by client.
        search.search.search._primary_filter.entry.set_text('dan')
        search.search.refresh()
        self.check_search(search, 'card-payment-string-filter')

        # Filtering by credit provider.
        search.search.search._primary_filter.entry.set_text('')
        provider = CreditProvider.selectOneBy(provider_id='AMEX',
                                              connection=self.trans)
        search.provider_filter.set_state(provider)
        search.search.refresh()
        self.check_search(search, 'card-payment-provider-filter')
