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
import gtk

from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.gui.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestSaleQuoteWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.salequotewizard.yesno')
    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_dialog')
    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_person_role_dialog')
    def test_confirm(self, run_person_role_dialog, run_dialog, yesno):
        client = self.create_client()
        self.create_address(person=client.person)

        run_person_role_dialog.return_value = client
        yesno.return_value = False

        sellable = self.create_sellable()
        sellable.barcode = '12345678'

        wizard = SaleQuoteWizard(self.trans)

        step = wizard.get_current_step()

        self.click(step.create_client)
        self.assertEquals(run_person_role_dialog.call_count, 1)
        args, kwargs = run_person_role_dialog.call_args
        editor, parent, trans, model = args
        self.assertEquals(editor, ClientEditor)
        self.assertEquals(parent, wizard)
        self.assertTrue(trans is not None)
        self.assertTrue(model is None)

        self.click(step.client_details)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, parent, trans, model = args
        self.assertEquals(dialog, ClientDetailsDialog)
        self.assertEquals(parent, wizard)
        self.assertTrue(trans is not None)
        self.assertEquals(model, client)

        self.click(step.notes_button)
        self.assertEquals(run_dialog.call_count, 2)
        args, kwargs = run_dialog.call_args
        editor, parent, trans, model, notes = args
        self.assertEquals(editor, NoteEditor)
        self.assertEquals(parent, wizard)
        self.assertTrue(trans is not None)
        self.assertEquals(model, wizard.model)
        self.assertEquals(notes, 'notes')
        self.assertEquals(kwargs['title'], _("Additional Information"))

        self.check_wizard(wizard, 'wizard-sale-quote-start-sale-quote-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)
        step.quantity.update(2)
        self.click(step.add_sellable_button)
        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        sale = wizard.retval
        self.check_wizard(wizard, 'wizard-sale-quote-sale-quote-item-step',
                          [sale, client] + list(sale.get_items()) + [sellable])

        yesno.assert_called_once_with(_('Would you like to print the quote '
                                        'details now?'), gtk.RESPONSE_YES,
                                      _("Print quote details"), _("Don't print"))
