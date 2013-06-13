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

import mock

from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.search.paymentreceivingsearch import PaymentReceivingSearch
from stoqlib.gui.slaves.paymentconfirmslave import SalePaymentConfirmSlave
from stoqlib.gui.test.uitestutils import GUITest


class TestPaymentReceivingSearch(GUITest):
    def test_show(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN,
                                      method=self.get_payment_method(name=u'store_credit'))
        payment.status = Payment.STATUS_PENDING
        payment.identifier = 123456

        dialog = PaymentReceivingSearch(self.store)
        self.click(dialog.search.search_button)
        self.check_dialog(dialog, 'search-payment-receiving-show')

    @mock.patch('stoqlib.gui.search.paymentreceivingsearch.run_dialog')
    @mock.patch('stoqlib.api.new_store')
    def test_receive(self, new_store, run_dialog):
        new_store.return_value = self.store
        run_dialog.return_value = True

        till = self.create_till()
        till.open_till()

        payment = self.create_payment(payment_type=Payment.TYPE_IN,
                                      method=self.get_payment_method(name=u'store_credit'))
        payment.status = Payment.STATUS_PENDING
        payment.identifier = 123456

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                dialog = PaymentReceivingSearch(self.store)
                self.click(dialog.search.search_button)
                dialog.results.select(dialog.results[0])
                dialog._receive()

                run_dialog.assert_called_once_with(
                    SalePaymentConfirmSlave, dialog,
                    self.store, payments=[payment], show_till_info=False)
