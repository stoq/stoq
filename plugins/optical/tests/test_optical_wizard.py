# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'plugins/optical/opticalwizard.py'

import mock
import gtk

from stoqlib.domain.sale import Sale
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

from ...optical.opticalwizard import OpticalSaleQuoteWizard

_ = stoqlib_gettext


class TestSaleQuoteWizard(GUITest):
    @mock.patch('plugins.optical.opticalwizard.yesno')
    @mock.patch('plugins.optical.opticalwizard.run_dialog')
    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
    def test_confirm(self, run_person_role_dialog, run_dialog, yesno):
        client = self.create_client()
        self.create_address(person=client.person)

        run_person_role_dialog.return_value = client
        yesno.return_value = False

        sellable = self.create_sellable()
        sellable.barcode = u'12345678'

        wizard = OpticalSaleQuoteWizard(self.store)

        step = wizard.get_current_step()

        self.click(step.create_client)
        self.assertEquals(run_person_role_dialog.call_count, 1)
        args, kwargs = run_person_role_dialog.call_args
        editor, parent, store, model = args
        self.assertEquals(editor, ClientEditor)
        self.assertEquals(parent, wizard)
        self.assertTrue(store is not None)
        self.assertTrue(model is None)

        self.click(step.client_details)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, parent, store, model = args
        self.assertEquals(dialog, ClientDetailsDialog)
        self.assertEquals(parent, wizard)
        self.assertTrue(store is not None)
        self.assertEquals(model, client)

        self.click(step.observations_button)
        self.assertEquals(run_dialog.call_count, 2)
        args, kwargs = run_dialog.call_args
        editor, parent, store, model, notes = args
        self.assertEquals(editor, NoteEditor)
        self.assertEquals(parent, wizard)
        self.assertTrue(store is not None)
        self.assertEquals(model, wizard.model)
        self.assertEquals(notes, 'notes')
        self.assertEquals(kwargs['title'], _("Additional Information"))

        self.check_wizard(wizard, 'wizard-optical-start-sale-quote-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        slave = step.slaves['WO 1']
        slave.patient.update('Patient')

        sale = wizard.model
        self.check_wizard(wizard, 'wizard-optical-work-order-step')

        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-optical-item-step',
                          [sale, client] + list(sale.get_items()) + [sellable])

        module = 'stoqlib.gui.events.SaleQuoteWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], Sale))

        self.assertEqual(wizard.model.payments.count(), 0)
        yesno.assert_called_once_with(_('Would you like to print the quote '
                                        'details now?'), gtk.RESPONSE_YES,
                                      _("Print quote details"), _("Don't print"))

    def test_param_accept_change_salesperson(self):
        sysparam(self.store).update_parameter(
            u'ACCEPT_CHANGE_SALESPERSON',
            u'True')
        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        self.assertTrue(step.salesperson.get_sensitive())

        sysparam(self.store).update_parameter(
            u'ACCEPT_CHANGE_SALESPERSON',
            u'False')

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        self.assertFalse(step.salesperson.get_sensitive())

    @mock.patch('plugins.optical.opticalwizard.localtoday')
    def test_expire_date_validate(self, localtoday_):
        localtoday_.return_value = localdate(2014, 1, 1)

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()

        res = step.expire_date.emit('validate', localdate(2013, 1, 1).date())
        self.assertEquals(
            unicode(res),
            u"The expire date must be set to today or a future date.")

    @mock.patch('plugins.optical.opticalwizard.warning')
    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
    def test_multiple_work_orders(self, run_person_role_dialog, warning):
        client = self.create_client()

        run_person_role_dialog.return_value = client

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        for i in range(3):
            wo = self.create_workorder()
            wo.sale = step.model

        wo.add_sellable(self.create_sellable())

        self.click(step.create_client)
        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-optical-work-order-step-multiple-wo')

        step = wizard.get_current_step()
        assert step.work_orders_nb.get_n_pages() == 3

        # Test removing the first, with no items
        self.click(step.slaves['WO 1'].close_button)

        # Test removing the third, which has items
        self.click(step.slaves['WO 3'].close_button)
        warning.assert_called_once_with(
            'This workorder already has items and cannot be removed')

        # Test removing the second, which has no items
        self.click(step.slaves['WO 2'].close_button)

        # Test removing the third, which is not possible any more since
        # it's the last
        self.click(step.slaves['WO 3'].close_button)

        # Add a new
        self.click(step.new_tab_button)

    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
    def test_item_step(self, run_person_role_dialog):
        client = self.create_client()
        run_person_role_dialog.return_value = client
        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        wo = self.create_workorder()
        wo.sale = step.model

        self.click(step.create_client)
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        slave = step.slaves['WO 1']
        slave.patient.update('Patient')
        self.click(wizard.next_button)

        # FIXME: WIP
