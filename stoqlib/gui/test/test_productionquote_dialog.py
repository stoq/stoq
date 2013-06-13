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

from stoqlib.domain.production import ProductionMaterial, ProductionOrder
from stoqlib.gui.dialogs.productionquotedialog import ProductionQuoteDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestProductionQuoteDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.productionquotedialog.info')
    @mock.patch('stoqlib.gui.dialogs.productionquotedialog.api.get_current_user')
    @mock.patch('stoqlib.gui.dialogs.productionquotedialog.api.new_store')
    def test_confirm(self, new_store, get_current_user, info):
        new_store.return_value = self.store

        user = self.create_user()
        get_current_user.return_value = user

        production_order = self.create_production_order()
        self.create_production_item(order=production_order)
        material = self.store.find(ProductionMaterial,
                                   order=production_order).one()

        production_order.status = ProductionOrder.ORDER_WAITING
        production_order.open_date = datetime.date.today()
        production_order.identifier = 333
        material.to_purchase = 1

        dialog = ProductionQuoteDialog(self.store)
        self.check_dialog(dialog, 'production-quote-dialog-show')

        self.assertNotSensitive(dialog, ['select_all'])
        self.assertSensitive(dialog, ['unselect_all'])

        self.click(dialog.unselect_all)
        self.assertSensitive(dialog, ['select_all'])
        self.assertNotSensitive(dialog, ['unselect_all'])

        self.click(dialog.select_all)

        # Dont commit the transaction
        with mock.patch.object(self.store, 'commit'):
            # Also dont close it, since tearDown will do it.
            with mock.patch.object(self.store, 'close'):
                self.click(dialog.main_dialog.ok_button)

        info.assert_called_once_with(_(u'The quote group was succesfully '
                                       'created and it is available '
                                       'in the Purchase application.'))

        quotation = dialog.retval.get_items()[0]
        order = quotation.purchase
        item = order.get_items()[0]

        self.check_dialog(dialog, 'production-quote-dialog-confirm',
                          [dialog.retval, quotation, order, item])
