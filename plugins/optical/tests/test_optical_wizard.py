import mock
import gtk

from stoqlib.domain.sale import Sale
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.test.uitestutils import GUITest
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
