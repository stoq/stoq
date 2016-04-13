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

import gtk
import mock

from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.domain.views import PendingReturnedSalesView, ReturnedSalesView
from stoqlib.gui.dialogs.returnedsaledialog import (ReturnedSaleDialog,
                                                    ReturnedSaleUndoDialog)
from stoqlib.gui.test.uitestutils import GUITest


class TestReturnedSaleDialog(GUITest):
    def test_show_pending(self):
        pending_return = self.create_pending_returned_sale()
        pending_return.sale.identifier = 336
        pending_return.identifier = 60
        pending_return.reason = u'Teste'
        model = self.store.find(PendingReturnedSalesView).one()
        dialog = ReturnedSaleDialog(self.store, model)
        self.check_dialog(dialog, 'dialog-receive-pending-returned-sale')

    def test_show_with_package_product(self):
        sale = self.create_sale()
        sale.identifier = 666
        package = self.create_product(description=u'Package', is_package=True)
        comp = self.create_product(description=u'Component 1', stock=5,
                                   storable=True)
        comp2 = self.create_product(description=u'Component 2', stock=5,
                                    storable=True)
        p_comp = self.create_product_component(product=package,
                                               component=comp,
                                               component_quantity=2,
                                               price=2)
        p_comp2 = self.create_product_component(product=package,
                                                component=comp2,
                                                component_quantity=2,
                                                price=5)
        item = sale.add_sellable(package.sellable, quantity=1, price=0)
        sale.add_sellable(comp.sellable,
                          quantity=item.quantity * p_comp.quantity,
                          price=p_comp.price,
                          parent=item)
        sale.add_sellable(comp2.sellable,
                          quantity=item.quantity * p_comp2.quantity,
                          price=p_comp2.price,
                          parent=item)

        self.add_payments(sale)
        sale.order()
        sale.confirm()
        r_sale = self.create_returned_sale(sale)
        r_sale.identifier = 666

        model = self.store.find(ReturnedSalesView).one()
        dialog = ReturnedSaleDialog(self.store, model)
        self.check_dialog(dialog, 'dialog-returned-sale-with-package')

    def test_show_undone(self):
        rsale = self.create_returned_sale()
        rsale.sale.identifier = 336
        rsale.identifier = 60
        rsale.reason = u'Teste'
        rsale.undo_reason = u'Foo bar'
        rsale.status = ReturnedSale.STATUS_CANCELLED
        rsale.confirm_responsible = rsale.responsible
        rsale.confirm_date = rsale.return_date

        model = self.store.find(ReturnedSalesView).one()
        dialog = ReturnedSaleDialog(self.store, model)
        self.check_dialog(dialog, 'dialog-returned-sale-undone')

    @mock.patch('stoqlib.gui.dialogs.returnedsaledialog.yesno')
    def test_receive_pending_returned_sale(self, yesno):
        self.create_pending_returned_sale()
        model = self.store.find(PendingReturnedSalesView).one()
        dialog = ReturnedSaleDialog(self.store, model)
        self.assertEquals(dialog.receive_button.get_property('visible'), True)
        self.assertEquals(model.returned_sale.status, ReturnedSale.STATUS_PENDING)
        with mock.patch.object(self.store, 'commit'):
            self.click(dialog.receive_button)
            yesno.assert_called_once_with(u'Receive pending returned sale?',
                                          gtk.RESPONSE_NO,
                                          u'Receive', u"Don't receive")
            self.assertEquals(model.returned_sale.status, ReturnedSale.STATUS_CONFIRMED)

    @mock.patch('stoqlib.gui.dialogs.returnedsaledialog.print_report')
    def test_print_button(self, print_report):
        self.create_pending_returned_sale()
        model = self.store.find(PendingReturnedSalesView).one()
        dialog = ReturnedSaleDialog(self.store, model)

        self.click(dialog.print_button)
        print_report.assert_called_once_with(dialog.report_class, dialog.model)

    @mock.patch('stoqlib.gui.dialogs.returnedsaledialog.run_dialog')
    @mock.patch('stoqlib.gui.dialogs.saledetails.api.new_store')
    def test_undo(self, new_store, run_dialog):
        new_store.return_value = self.store

        rsale = self.create_returned_sale()
        rsale.status = ReturnedSale.STATUS_CONFIRMED
        rsale.confirm_responsible = rsale.responsible
        rsale.confirm_date = rsale.return_date

        model = self.store.find(ReturnedSalesView).one()
        dialog = ReturnedSaleDialog(self.store, model)

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(dialog.undo_button)

        run_dialog.assert_called_once_with(ReturnedSaleUndoDialog, dialog,
                                           self.store, model.returned_sale)


class TestReturnedSaleUndoDialog(GUITest):
    def test_show(self):
        rsale = self.create_pending_returned_sale()
        rsale.sale.identifier = 336
        rsale.identifier = 60
        rsale.status = ReturnedSale.STATUS_CONFIRMED
        rsale.reason = u'Teste'

        dialog = ReturnedSaleUndoDialog(self.store, rsale)
        self.check_dialog(dialog, 'dialog-returned-sale-undo')

    def test_cancel(self):
        rsale = self.create_pending_returned_sale()
        rsale.status = ReturnedSale.STATUS_CONFIRMED
        dialog = ReturnedSaleUndoDialog(self.store, rsale)

        self.assertFalse(rsale.is_undone())
        self.click(dialog.main_dialog.cancel_button)
        self.assertFalse(rsale.is_undone())

    def test_undo(self):
        rsale = self.create_pending_returned_sale()
        rsale.status = ReturnedSale.STATUS_CONFIRMED
        dialog = ReturnedSaleUndoDialog(self.store, rsale)

        self.assertNotSensitive(dialog.main_dialog, ['ok_button'])
        dialog.undo_reason.update('foo')
        self.assertSensitive(dialog.main_dialog, ['ok_button'])

        self.assertFalse(rsale.is_undone())
        self.click(dialog.main_dialog.ok_button)
        self.assertTrue(rsale.is_undone())

    @mock.patch('stoqlib.gui.dialogs.returnedsaledialog.warning')
    def test_undo_without_stock(self, warning):
        product = self.create_product(storable=True)

        rsale = self.create_pending_returned_sale(product=product)
        rsale.status = ReturnedSale.STATUS_CONFIRMED

        dialog = ReturnedSaleUndoDialog(self.store, rsale)

        self.assertNotSensitive(dialog.main_dialog, ['ok_button'])
        dialog.undo_reason.update('foo')
        self.assertSensitive(dialog.main_dialog, ['ok_button'])

        self.assertFalse(rsale.is_undone())
        self.click(dialog.main_dialog.ok_button)
        self.assertFalse(rsale.is_undone())

        warning.assert_called_once_with(
            'It was not possible to undo this returned sale. Some of the '
            'returned products are out of stock.')
