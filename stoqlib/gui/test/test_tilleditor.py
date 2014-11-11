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

from kiwi.currency import currency
from kiwi.python import Settable

from stoqlib.exceptions import TillError
from stoqlib.domain.events import (TillOpenEvent, TillAddCashEvent,
                                   TillRemoveCashEvent)
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.till import Till
from stoqlib.gui.editors.tilleditor import (TillClosingEditor,
                                            TillOpeningEditor,
                                            CashAdvanceEditor,
                                            CashInEditor, CashOutEditor)
from stoqlib.gui.test.uitestutils import GUITest


def _till_event(*args, **kwargs):
    raise TillError("ERROR")


class _BaseTestTillEditor(GUITest):
    need_open_till = False

    def setUp(self):
        super(_BaseTestTillEditor, self).setUp()
        if self.need_open_till:
            self.till = self.create_till()
            self.till.open_till()


class TestTillOpeningEditor(_BaseTestTillEditor):
    need_open_till = False

    def test_create(self):
        editor = TillOpeningEditor(self.store)
        self.check_editor(editor, 'editor-tillopening-create')

    @mock.patch('stoqlib.gui.editors.tilleditor.warning')
    def test_confirm(self, warning):
        editor = TillOpeningEditor(self.store)

        TillOpenEvent.connect(_till_event)
        editor.confirm()
        warning.assert_called_once_with("ERROR")
        self.assertEqual(editor.retval, False)

        TillOpenEvent.disconnect(_till_event)
        editor.confirm()
        self.assertEqual(editor.retval, editor.model)

    @mock.patch('stoqlib.gui.editors.tilleditor.warning')
    def test_confirm_multiple(self, warning):
        # FIXME: We cannot do this test using 2 editors because:
        # 1- They should live in different transactions
        # 2- One of them should be committed for it to work
        editor = TillOpeningEditor(self.store)

        with mock.patch.object(Till, 'get_last_opened') as glo:
            glo.return_value = Settable(
                opening_date=editor.model.till.opening_date)
            self.click(editor.main_dialog.ok_button)
            self.assertEqual(editor.retval, False)
            warning.assert_called_once_with(
                "A till was opened earlier this day.")


class TestTillClosingEditor(_BaseTestTillEditor):
    need_open_till = True

    def test_create(self):
        editor = TillClosingEditor(self.store)
        self.check_editor(editor, 'editor-tillclosing-create')

    @mock.patch('stoqlib.gui.editors.tilleditor.warning')
    def test_confirm(self, warning):
        editor = TillClosingEditor(self.store)

        editor.model.value = editor.model.till.get_balance() + 1
        self.assertFalse(editor.confirm())
        warning.assert_called_once_with(
            "The amount that you want to remove is "
            "greater than the current balance.")
        editor.model.value = editor.model.till.get_balance()
        self.assertTrue(editor.confirm())


class TestCashInEditor(_BaseTestTillEditor):
    need_open_till = True

    def test_create(self):
        editor = CashInEditor(self.store)
        self.check_editor(editor, 'editor-cashin-create')

    @mock.patch('stoqlib.gui.editors.tilleditor.warning')
    def test_confirm(self, warning):
        editor = CashInEditor(self.store)
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        editor.cash_slave.proxy.update('value', currency(10))
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        editor.reason.update(u'Cash in test')
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        TillAddCashEvent.connect(_till_event)
        editor.confirm()
        self.assertEqual(editor.retval, False)
        warning.assert_called_once_with("ERROR")

        TillAddCashEvent.disconnect(_till_event)
        editor.confirm()
        self.assertEqual(editor.retval, editor.model)


class TestCashOutEditor(_BaseTestTillEditor):
    need_open_till = True

    def test_create(self):
        editor = CashOutEditor(self.store)
        self.check_editor(editor, 'editor-cashout-create')

    @mock.patch('stoqlib.gui.editors.tilleditor.warning')
    def test_confirm(self, warning):
        # Add some amount to till so it can be removed above
        p = self.create_payment(payment_type=Payment.TYPE_IN,
                                value=currency(50))
        self.till.add_entry(p)

        editor = CashOutEditor(self.store)
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        editor.cash_slave.proxy.update('value', currency(10))
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        editor.reason.update(u'Cash out test')
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        TillRemoveCashEvent.connect(_till_event)
        editor.confirm()
        self.assertEqual(editor.retval, False)
        warning.assert_called_once_with("ERROR")

        TillRemoveCashEvent.disconnect(_till_event)
        editor.confirm()
        self.assertEqual(editor.retval, editor.model)


class TestCashAdvanceEditor(_BaseTestTillEditor):
    need_open_till = True

    def test_create(self):
        editor = CashAdvanceEditor(self.store)
        self.check_editor(editor, 'editor-cashadvance-create')

    @mock.patch('stoqlib.gui.editors.tilleditor.warning')
    def test_confirm(self, warning):
        # Add some amount to till so it can be removed
        payment = self.create_payment(payment_type=Payment.TYPE_IN,
                                      value=currency(50))
        self.till.add_entry(payment)

        editor = CashAdvanceEditor(self.store)
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        editor.cash_slave.proxy.update('value', currency(10))
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        TillRemoveCashEvent.connect(_till_event)
        editor.confirm()
        self.assertEqual(editor.retval, False)
        warning.assert_called_once_with("ERROR")

        TillRemoveCashEvent.disconnect(_till_event)
        editor.confirm()
        self.assertEqual(editor.retval, editor.model)
