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
from stoqlib.api import api
from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.domain.events import TillOpenEvent
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.till import Till
from stoqlib.gui.editors.tilleditor import TillOpeningEditor

from stoq.gui.pos import PosApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestPos(BaseGUITest):
    def testInitial(self):
        app = self.create_app(PosApp, 'pos')
        self.check_app(app, 'pos')

    def _open_till(self, trans):
        till = Till(connection=trans,
                    station=api.get_current_station(trans))
        till.open_till()

        TillOpenEvent.emit(till=till)
        self.assertEquals(till, Till.get_current(trans))
        return till

    def _pos_open_till(self, pos):
        with mock.patch('stoqlib.gui.fiscalprinter.run_dialog') as run_dialog:
            self.activate(pos.TillOpen)
            self._called_once_with_trans(run_dialog, TillOpeningEditor, pos)

    def _auto_confirm_sale_wizard(self, wizard, app, trans, sale):
        # This is in another transaction and as we want to avoid committing
        # we need to open the till again
        self._open_till(trans)

        sale.order()
        money_method = PaymentMethod.get_by_name(trans, 'money')
        total = sale.get_total_sale_amount()
        money_method.create_inpayment(sale.group,
                                      sale.branch, total)
        self.sale = sale
        return sale

    def _called_once_with_trans(self, func, *expected_args):
        args = func.call_args[0]
        for arg, expected in zip(args, expected_args):
            self.assertEquals(arg, expected)

    @mock.patch.object(api, 'finish_transaction')
    def testTillOpen(self, finish_transaction):
        app = self.create_app(PosApp, 'pos')
        pos = app.main_window

        self._pos_open_till(pos)

        self.check_app(app, 'pos-till-open')

    @mock.patch.object(api, 'finish_transaction')
    def testCheckout(self, finish_transaction):
        app = self.create_app(PosApp, 'pos')
        pos = app.main_window

        self._pos_open_till(pos)
        pos.barcode.set_text('1598756984265')
        self.activate(pos.barcode)

        self.check_app(app, 'pos-checkout-pre')

        # Delay the close calls until after the test is done
        close_calls = []

        def close(trans):
            if not trans in close_calls:
                close_calls.insert(0, trans)

        with mock.patch.object(StoqlibTransaction, 'close', new=close):

            with mock.patch('stoqlib.gui.fiscalprinter.run_dialog',
                            self._auto_confirm_sale_wizard):
                self.activate(pos.ConfirmOrder)

            models = self.collect_sale_models(self.sale)
            self.check_app(app, 'pos-checkout-post',
                           models=models)

        for trans in close_calls:
            trans.close()
