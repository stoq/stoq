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
import unittest

import mock
from stoqlib.database.runtime import StoqlibStore
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.dialogs.supplierdetails import SupplierDetailsDialog
from stoqlib.gui.editors.personeditor import SupplierEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestSupplierDetails(GUITest):

    def test_show(self):
        date = datetime.date(2012, 1, 1)
        supplier = self.create_supplier()

        # Nova venda
        order = self.create_purchase_order()
        order.identifier = 123
        order.supplier = supplier
        order.open_date = date

        # Product
        self.create_purchase_order_item(order)

        # Payments
        payment = self.add_payments(order, date=date)[0]
        payment.identifier = 999
        payment.group.payer = supplier.person
        payment.status = Payment.STATUS_PAID

        dialog = SupplierDetailsDialog(self.store, supplier)
        self.check_editor(dialog, 'dialog-supplier-details')

    @mock.patch('stoqlib.gui.dialogs.supplierdetails.run_person_role_dialog')
    def test_further_details(self, run_dialog):
        supplier = self.create_supplier()

        dialog = SupplierDetailsDialog(self.store, supplier)
        self.click(dialog.further_details_button)

        args, kwargs = run_dialog.call_args
        editor, d, store, model = args
        self.assertEquals(editor, SupplierEditor)
        self.assertEquals(d, dialog)
        self.assertEquals(model, dialog.model)
        self.assertTrue(isinstance(store, StoqlibStore))
        self.assertEquals(kwargs.pop('visual_mode'), True)
        self.assertEquals(kwargs, {})


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
