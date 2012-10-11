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
from decimal import Decimal

from kiwi.python import Settable

from stoqlib.domain.sale import Sale
from stoqlib.gui.dialogs.quotedialog import (ConfirmSaleMissingDialog,
                                             QuoteFillingDialog)
from stoqlib.gui.uitestutils import GUITest


class TestConfirmSaleMissingDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.quotedialog.api.new_transaction')
    def test_confirm(self, new_transaction):
        # We need to use the current transaction in the test, since the test
        # object is only in this transaction
        new_transaction.return_value = self.trans

        sale = self.create_sale()
        sale_item = self.create_sale_item(sale=sale)
        product = sale_item.sellable.product
        self.create_storable(product=product)
        missing_item = Settable(description='desc',
                                ordered=Decimal('1'),
                                stock=Decimal('0'),
                                storable=sale_item.sellable.product.storable)

        sale.status = Sale.STATUS_QUOTE
        dialog = ConfirmSaleMissingDialog(sale, [missing_item])

        # Dont commit the transaction
        with mock.patch.object(self.trans, 'commit'):
            # Also dont close it, since tearDown will do it.
            with mock.patch.object(self.trans, 'close'):
                self.click(dialog.ok_button)

        storable = dialog.retval[0].storable
        self.check_dialog(dialog, 'test-confirm-sale-missing-dialog-confirm',
                          [storable, sale, sale_item, product])


class TestQuoteFillingDialog(GUITest):
    def test_show(self):
        order = self.create_purchase_order()
        order.add_item(self.create_sellable())
        dialog = QuoteFillingDialog(order, self.trans)
        self.check_dialog(dialog, 'test-quote-filling-dialog-show')
