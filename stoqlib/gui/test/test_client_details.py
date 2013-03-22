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

import unittest

import mock
from stoqlib.database.runtime import StoqlibStore
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.lib.dateutils import localtoday
from stoqlib.gui.uitestutils import GUITest


class TestClientDetails(GUITest):

    def testShow(self):
        today = localtoday().date()
        client = self.create_client()
        # Nova venda
        sale = self.create_sale()
        sale.identifier = 123
        sale.client = client
        sale.open_date = today

        # Product
        self.create_sale_item(sale, product=True)
        # Service
        item = self.create_sale_item(sale, product=False)
        item.estimated_fix_date = today
        # Payments
        payment = self.add_payments(sale, date=today)[0]
        payment.identifier = 999
        payment.group.payer = client.person
        # Call
        self.create_call(client.person)

        dialog = ClientDetailsDialog(self.store, client)
        self.check_editor(dialog, 'dialog-client-details')

    @mock.patch('stoqlib.gui.dialogs.clientdetails.run_person_role_dialog')
    def testFurtherDetails(self, run_dialog):
        client = self.create_client()

        dialog = ClientDetailsDialog(self.store, client)
        new_store = 'stoqlib.gui.dialogs.clientdetails.api.new_store'
        with mock.patch(new_store) as new_store:
            with mock.patch.object(self.store, 'close'):
                new_store.return_value = self.store
                self.click(dialog.further_details_button)

        args, kwargs = run_dialog.call_args
        editor, d, store, model = args
        self.assertEquals(editor, ClientEditor)
        self.assertEquals(d, dialog)
        self.assertEquals(model, dialog.model)
        self.assertTrue(isinstance(store, StoqlibStore))
        self.assertEquals(kwargs.pop('visual_mode'), True)
        self.assertEquals(kwargs, {})


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
