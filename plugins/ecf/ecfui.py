# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
import logging
import os
import time

import gtk
from serial import SerialException

from kiwi.python import Settable
from stoqdrivers.exceptions import CouponOpenError, DriverError

from stoqlib.api import api
from stoqlib.database.runtime import (get_current_station,
                                      get_default_store,
                                      new_store)
from stoqlib.domain.events import (SaleStatusChangedEvent, TillAddCashEvent,
                                   TillRemoveCashEvent, TillOpenEvent,
                                   TillCloseEvent, TillAddTillEntryEvent,
                                   GerencialReportPrintEvent,
                                   GerencialReportCancelEvent,
                                   CheckECFStateEvent,
                                   HasPendingReduceZ, SaleAvoidCancelEvent,
                                   HasOpenCouponEvent)
from stoqlib.domain.person import Individual, Company
from stoqlib.domain.sale import Sale, SaleComment
from stoqlib.domain.till import Till
from stoqlib.exceptions import DeviceError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.events import (StartApplicationEvent, StopApplicationEvent,
                                CouponCreatedEvent, EditorCreateEvent)
from stoqlib.gui.utils.keybindings import add_bindings, get_accels
from stoqlib.lib.message import info, warning, yesno
from stoqlib.lib.parameters import sysparam, ParameterDetails
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext

from ecf.cat52 import MODEL_CODES
from ecf.catgenerator import StoqlibCATGenerator
from ecf.couponprinter import CouponPrinter
from ecf.ecfdomain import ECFPrinter, FiscalSaleHistory
from ecf.ecfprinterdialog import ECFListDialog
from ecf.ecfmemorydialog import FiscalMemoryDialog
from ecf.paulistainvoicedialog import PaulistaInvoiceDialog

_ = stoqlib_gettext
log = logging.getLogger(__name__)

params = [
    # Some fiscal printers can print up to 8 rows and 70 characters each row.
    # But we want to write an documentation to make sure it will work
    # on every fiscal printer
    ParameterDetails(
        u'ADDITIONAL_INFORMATION_ON_COUPON',
        _(u'ECF'),
        _(u'Additional information on fiscal coupon'),
        _(u'This will be printed in the promotional message area of the fiscal coupon\n'
          u'IMPORTANT NOTE:\n'
          u'This template cannot have more than 2 line, and each line more '
          u'than 50 characters, and you have to break it manually using the characters '
          u'"\\n" or (enter key) or the fiscal printer may not print it correctly.'),
        unicode, multiline=True, initial=u'', wrap=False),

    ParameterDetails(
        u'ENABLE_DOCUMENT_ON_INVOICE',
        _(u'ECF'),
        _(u'Enable document on invoice'),
        _(u'Once this parameter is set, we will confirm the client document '
          u'when  registering a fiscal coupon.'),
        bool, initial=False),

    ParameterDetails(
        u'ALLOW_CANCEL_LAST_COUPON',
        _(u'ECF'),
        _(u'Allow to cancel the last fiscal coupon'),
        _(u'When set to false, the user will not be able to cancel the last coupon, '
          u'only return it.'),
        bool, initial=True),

    ParameterDetails(
        u'CAT52_DEST_DIR',
        _(u'ECF'),
        _(u'Cat 52 destination directory'),
        _(u'Where the file generated after a Z-reduction should be saved.'),
        unicode, initial=u'~/.stoq/cat52', editor='directory-chooser'),
]


class ECFUI(object):
    def __init__(self):
        self._ui = None
        self.default_store = get_default_store()
        self._printer_verified = False
        # Delay printer creation until we are accessing pos or till app. Other
        # applications should still be accessible without a printer
        self._printer = None

        self._setup_params()
        self._setup_events()

        self._till_summarize_action = gtk.Action(
            'Summary', _('Summary'), None, None)
        self._till_summarize_action.connect(
            'activate', self._on_TillSummary__activate)

        add_bindings([
            ('plugin.ecf.read_memory', '<Primary>F9'),
            ('plugin.ecf.summarize', '<Primary>F11'),
        ])

    #
    # Private
    #

    def _setup_params(self):
        for detail in params:
            sysparam.register_param(detail)

    def _setup_events(self):
        SaleStatusChangedEvent.connect(self._on_SaleStatusChanged)
        SaleAvoidCancelEvent.connect(self._on_SaleAvoidCancel)
        TillOpenEvent.connect(self._on_TillOpen)
        TillCloseEvent.connect(self._on_TillClose)
        TillAddCashEvent.connect(self._on_TillAddCash)
        TillAddTillEntryEvent.connect(self._on_AddTillEntry)
        TillRemoveCashEvent.connect(self._on_TillRemoveCash)
        StartApplicationEvent.connect(self._on_StartApplicationEvent)
        StopApplicationEvent.connect(self._on_StopApplicationEvent)
        CouponCreatedEvent.connect(self._on_CouponCreatedEvent)
        GerencialReportPrintEvent.connect(self._on_GerencialReportPrintEvent)
        GerencialReportCancelEvent.connect(self._on_GerencialReportCancelEvent)
        CheckECFStateEvent.connect(self._on_CheckECFStateEvent)
        HasPendingReduceZ.connect(self._on_HasPendingReduceZ)
        HasOpenCouponEvent.connect(self._on_HasOpenCouponEvent)
        EditorCreateEvent.connect(self._on_EditorCreateEvent)

    def _create_printer(self):
        if self._printer:
            return self._printer

        station = get_current_station(self.default_store)
        printer = self.default_store.find(ECFPrinter, station=station,
                                          is_active=True).one()
        if not printer:
            return None

        try:
            self._printer = CouponPrinter(printer)
        except SerialException as e:
            warning(_('Error opening serial port'), str(e))
        except DriverError as e:
            warning(str(e))
        return None

    def _validate_printer(self):
        if self._printer is None:
            raise DeviceError(
                _("This operation requires a connected fiscal printer"))
        # Check fiscal printer setup. If something went wrong with the setup,
        # block the till
        if not self._printer._driver.setup_complete():
            raise DeviceError(_("An error occurred during fiscal printer setup"))

        if not self._printer_verified:
            log.info('ecfui._validate_printer')
            if not self._printer.check_serial():
                raise DeviceError(
                    _("Fiscalprinters serial number is different!"))

            self._printer_verified = True

    def _add_ui_menus(self, appname, app, uimanager):
        self._current_app = app
        if appname == 'pos':
            self._create_printer()
            self._add_pos_menus(uimanager)
        elif appname == 'till':
            self._create_printer()
            self._add_till_menus(uimanager)
        elif appname == 'sales':
            # The sales app needs the printer to check if the
            # sale being returned is the last sale on the ECF.
            self._create_printer()
        elif appname == 'admin':
            self._add_admin_menus(uimanager)
            app.tasks.add_item(
                _('Fiscal Printers'), 'fiscal-printer', 'printer',
                self._on_ConfigurePrinter__activate)

    def _remove_ui_menus(self, uimanager):
        if not self._ui:
            return
        uimanager.remove_ui(self._ui)
        self._ui = None

    def _add_admin_menus(self, uimanager):
        ui_string = """<ui>
          <menubar name="menubar">
            <placeholder action="AppMenubarPH">
              <menu action="ConfigureMenu">
              <placeholder name="ConfigurePH">
                <menuitem action="ConfigurePrinter"/>
              </placeholder>
              </menu>
            </placeholder>
          </menubar>
        </ui>"""

        ag = gtk.ActionGroup('ECFMenuActions')
        ag.add_actions([
            ('ECFMenu', None, _('ECF')),
            ('ConfigurePrinter', None, _('Configure fiscal printer...'),
             None, None, self._on_ConfigurePrinter__activate),
        ])
        uimanager.insert_action_group(ag, 0)
        self._ui = uimanager.add_ui_from_string(ui_string)

    def _add_ecf_menu(self, uimanager):
        ui_string = """<ui>
          <menubar name="menubar">
            <placeholder name="ExtraMenubarPH">
              <menu action="ECFMenu">
                <menuitem action="CancelLastDocument"/>
                <menuitem action="Summary"/>
                <menuitem action="ReadMemory"/>
              </menu>
            </placeholder>
          </menubar>
        </ui>"""

        group = get_accels('plugin.ecf')

        ag = gtk.ActionGroup('ECFMenuActions')
        ag.add_actions([
            ('ECFMenu', None, _('ECF')),
            ('ReadMemory', None, _('Read Memory'),
             group.get('read_memory'), None, self._on_ReadMemory__activate),
            ('CancelLastDocument', None, _('Cancel Last Document'),
             None, None, self._on_CancelLastDocument__activate),
        ])
        ag.add_action_with_accel(self._till_summarize_action,
                                 group.get('summarize'))

        can_cancel = sysparam.get_bool('ALLOW_CANCEL_LAST_COUPON')
        cancel_coupon_menu = ag.get_action('CancelLastDocument')
        cancel_coupon_menu.set_visible(can_cancel)

        uimanager.insert_action_group(ag, 0)
        self._ui = uimanager.add_ui_from_string(ui_string)

    def _add_pos_menus(self, uimanager):
        if sysparam.get_bool('POS_SEPARATE_CASHIER'):
            return
        self._add_ecf_menu(uimanager)

    def _add_till_menus(self, uimanager):
        self._add_ecf_menu(uimanager)

    def _check_ecf_state(self):
        log.info('ecfui._check_printer')
        try:
            self._validate_printer()
        except (DriverError, DeviceError):
            warning(_("It was not possible to communicate with the printer"))
            raise SystemExit

        self._has_open_coupon()

    def _has_open_coupon(self):
        self._validate_printer()
        if self._printer.has_open_coupon():
            warning(_("The ECF has an open coupon. It will be canceled now."))
            self._printer.cancel()

    def _open_till(self, till):
        log.info('ECFCouponPrinter.open_till(%r)' % (till, ))

        # Callsite catches DeviceError
        self._validate_printer()

        retval = True
        while True:
            try:
                self._printer.open_till()
            except CouponOpenError:
                self._printer.cancel()
                retval = False
            except DriverError:
                response = warning(
                    _(u"It's not possible to emit a read X for the "
                      "configured printer.\nWould you like to ignore "
                      "this error and continue?"),
                    buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                             (_(u"Ignore"), gtk.RESPONSE_YES),
                             (_(u"Try Again"), gtk.RESPONSE_NONE)))
                if response == gtk.RESPONSE_NONE:
                    continue
                elif response == gtk.RESPONSE_CANCEL:
                    retval = False

            break

        return retval

    def _has_pending_reduce(self):
        self._validate_printer()
        return self._printer.has_pending_reduce()

    def _close_till(self, till, previous_day):
        log.info('ECFCouponPrinter.close_till(%r, %r)' % (till, previous_day))

        # XXX: this is so ugly, but the printer stops responding
        # if its printing something. We should wait a little bit...
        # This only happens if closing the till from the current day.
        if not previous_day:
            time.sleep(4)

        # Callsite catches DeviceError
        self._validate_printer()

        printer = self._printer.get_printer()

        if (sysparam.get_bool('ENABLE_DOCUMENT_ON_INVOICE') and not
            (printer.user_number and printer.register_date and
             printer.register_cro)):
            response = warning(
                short=_(u"You need to set some details about your ECF "
                        "if you want to save the paulista invoice file. "
                        "Go to the admin application and fill the "
                        "required information for the ECF."),
                buttons=((_(u"Cancel Close Till"), gtk.RESPONSE_CANCEL), ))
            return False

        retval = True
        while True:
            try:
                self._printer.close_till(previous_day=previous_day)
            except CouponOpenError:
                self._printer.cancel()
                retval = False
            except DriverError:
                response = warning(
                    short=_(u"It's not possible to emit a reduce Z for the "
                            "configured printer.\nWould you like to ignore "
                            "this error and continue?"),
                    buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                             (_(u"Ignore"), gtk.RESPONSE_YES),
                             (_(u"Try Again"), gtk.RESPONSE_NONE)))
                if response == gtk.RESPONSE_NONE:
                    continue
                elif response == gtk.RESPONSE_CANCEL:
                    retval = False

            break

        if self._needs_cat52(printer):
            day = datetime.date.today()
            if previous_day:
                # XXX: Make sure this is tested
                day = till.opening_date

            dir = sysparam.get_string('CAT52_DEST_DIR')
            dir = os.path.expanduser(dir)
            if not os.path.exists(dir):
                os.mkdir(dir)

            generator = StoqlibCATGenerator(self.default_store, day, printer)
            generator.write(dir)

        self._reset_last_doc()

        return retval

    def _needs_cat52(self, printer):
        # If the param is not enabled, we dont need.
        if not sysparam.get_bool('ENABLE_DOCUMENT_ON_INVOICE'):
            return False

        # Even if the parameter is enabled, we can only generate cat52 for
        # the printer we support, and that dont have MFD:
        # If the printer has an MFD, it should not be present in the
        # MODEL_CODES variable
        model = MODEL_CODES.get((printer.brand,
                                 printer.model))
        if not model:
            return False

        return True

    def _set_last_sale(self, sale, store):
        printer = store.fetch(self._printer._printer)
        printer.last_sale = sale
        printer.last_till_entry = None

    def _set_last_till_entry(self, till_entry, store):
        printer = store.fetch(self._printer._printer)
        printer.last_till_entry = till_entry
        printer.last_sale = None

    def _reset_last_doc(self):
        # Last ecf document is not a sale or a till_entry anymore.
        store = new_store()
        printer = store.fetch(self._printer._printer)
        printer.last_till_entry = None
        printer.last_sale = None
        store.commit()

    def _add_cash(self, till, value):
        log.info('ECFCouponPrinter.add_cash(%r, %r)' % (till, value, ))

        # XXX: this is so ugly, but the printer stops responding
        # if its printing something. We should wait a little bit...
        time.sleep(4)

        # Callsite catches DeviceError
        self._validate_printer()

        self._printer.add_cash(value)

    def _remove_cash(self, till, value):
        log.info('ECFCouponPrinter.remove_cash(%r, %r)' % (till, value, ))

        # Callsite catches DeviceError
        self._validate_printer()

        self._printer.remove_cash(value)

    def _confirm_sale(self, sale):
        log.info('ECFCouponPrinter.confirm_sale(%r)' % (sale, ))

        self._validate_printer()

    def _undo_returned_sale(self, sale):
        log.info('Undoing a returned_sale of the sale(%r)' % (sale, ))

    def _coupon_create(self, fiscalcoupon, sale):
        # External sales are an exception to the general rule and should not
        # generate an ecf.
        if sale and sale.is_external():
            return

        # Callsite catches DeviceError
        self._validate_printer()

        coupon = self._printer.create_coupon(fiscalcoupon)
        assert coupon
        for signal, callback in [
                ('open', self._on_coupon__open),
                ('identify-customer', self._on_coupon__identify_customer),
                ('customer-identified', self._on_coupon__customer_identified),
                ('add-item', self._on_coupon__add_item),
                ('remove-item', self._on_coupon__remove_item),
                ('add-payments', self._on_coupon__add_payments),
                ('totalize', self._on_coupon__totalize),
                ('close', self._on_coupon__close),
                ('cancel', self._on_coupon__cancel),
                ('get-coo', self._on_coupon__get_coo),
                ('get-supports-duplicate-receipt', self._on_coupon__get_supports_duplicate),
                ('print-payment-receipt', self._on_coupon__print_payment_receipt)]:
            fiscalcoupon.connect_object(signal, callback, coupon)
        return coupon

    def _get_last_document(self, store):
        station = api.get_current_station(store)
        return ECFPrinter.get_last_document(station=station, store=store)

    def _is_ecf_last_sale(self, sale):
        store = sale.store
        is_last_sale = store.find(ECFPrinter, last_sale=sale).count() > 0
        return is_last_sale

    def _confirm_last_document_cancel(self, last_doc):
        if last_doc.last_sale is None and last_doc.last_till_entry is None:
            info(_("There is no sale nor till entry to cancel"))
            return

        if last_doc.last_sale:
            msg = _("Do you really want to cancel the sale number %s "
                    "and value %.2f ?") % (last_doc.last_sale.identifier,
                                           last_doc.last_sale.total_amount)
        elif last_doc.last_till_entry.value > 0:
            msg = _("Do you really want to cancel the last cash added "
                    "number %d and value %.2f ?") % (
                last_doc.last_till_entry.identifier,
                last_doc.last_till_entry.value)
        else:
            msg = _("Do you really want to cancel the last cash removed "
                    "number %d and value %.2f ?") % (
                last_doc.last_till_entry.identifier,
                last_doc.last_till_entry.value)
        return yesno(msg, gtk.RESPONSE_NO, _("Cancel Last Document"),
                     _("Not now"))

    def _cancel_last_till_entry(self, last_doc, store):
        last_till_entry = store.fetch(last_doc.last_till_entry)
        value = last_till_entry.value
        till = Till.get_current(store)
        try:
            self._printer.cancel_last_coupon()
            if last_till_entry.value > 0:
                till_entry = till.add_debit_entry(
                    # TRANSLATORS: cash out = sangria, cash in = suprimento
                    value, _(u"Cash out: last cash in cancelled"))
                self._set_last_till_entry(till_entry, store)
            else:
                till_entry = till.add_credit_entry(
                    # TRANSLATORS: cash out = sangria, cash in = suprimento
                    -value, _(u"Cash in: last cash out cancelled"))
                self._set_last_till_entry(till_entry, store)
            info(_("Document was cancelled"))
        except Exception:
            info(_("Cancelling failed, nothing to cancel"))
            return

    def _cancel_last_sale(self, last_doc, store):
        if last_doc.last_sale.status == Sale.STATUS_RETURNED:
            return
        sale = store.fetch(last_doc.last_sale)
        value = sale.total_amount
        sale.cancel(force=True)
        comment = _(u"Cancelling last document on ECF")
        SaleComment(store=store, sale=sale, comment=comment,
                    author=api.get_current_user(store))
        till = Till.get_current(store)
        # TRANSLATORS: cash out = sangria
        till.add_debit_entry(value, _(u"Cash out: last sale cancelled"))
        last_doc.last_sale = None
        info(_("Document was cancelled"))

    def _cancel_last_document(self):
        try:
            self._validate_printer()
        except DeviceError as e:
            warning(str(e))
            return

        store = new_store()
        last_doc = self._get_last_document(store)
        if not self._confirm_last_document_cancel(last_doc):
            store.close()
            return

        if last_doc.last_till_entry:
            self._cancel_last_till_entry(last_doc, store)
        elif last_doc.last_sale:
            # Verify till balance before cancel the last sale.
            till = Till.get_current(store)
            if last_doc.last_sale.total_amount > till.get_balance():
                warning(_("You do not have this value on till."))
                store.close()
                return
            cancelled = self._printer.cancel_last_coupon()
            if not cancelled:
                info(_("Cancelling sale failed, nothing to cancel"))
                store.close()
                return
            else:
                self._cancel_last_sale(last_doc, store)
        store.commit()

    def _till_summarize(self):
        try:
            self._validate_printer()
        except DeviceError as e:
            warning(str(e))
            return

        self._printer.summarize()
        self._reset_last_doc()

    def _fiscal_memory_dialog(self):
        try:
            self._validate_printer()
        except DeviceError as e:
            warning(str(e))
            return
        retval = run_dialog(FiscalMemoryDialog, None, self.default_store, self._printer)
        if retval:
            self._reset_last_doc()

    def _get_client_document(self, sale):
        """Returns a Settable with two attributes: document, a string with
        the client cpf or cnpj and document_type, being one of
        (FiscalSaleHistory.TYPE_CPF, FiscalSaleHistory.TYPE_CNPJ )
        """
        client_role = sale.get_client_role()
        if isinstance(client_role, Individual):
            document_type = FiscalSaleHistory.TYPE_CPF
            document = client_role.cpf
        elif isinstance(client_role, Company):
            document_type = FiscalSaleHistory.TYPE_CNPJ
            document = client_role.cnpj
        else:
            return

        if document:
            return Settable(document_type=document_type,
                            document=document)

    def _identify_customer(self, coupon, sale=None):
        if not sysparam.get_bool('ENABLE_DOCUMENT_ON_INVOICE'):
            return

        model = None
        initial_client_document = None
        if sale:
            model = self._get_client_document(sale)

        # Sale may have no client.
        if model:
            initial_client_document = model.document

        model = run_dialog(PaulistaInvoiceDialog, self._current_app,
                           self.default_store, model)

        # The user has chosen the 'without cpf' option, but we still need to
        # inform a invalid CPF, otherwise the current client's cpf will be used
        if not model:
            coupon.identify_customer('-', '-', u'', None)
            return

        # The document didn't change.
        if model.document == initial_client_document:
            return
        coupon.identify_customer('-', '-', model.document,
                                 model.document_type)
        return model.document

    #
    # Events
    #

    def _on_StartApplicationEvent(self, appname, app):
        self._add_ui_menus(appname, app, app.window.uimanager)

    def _on_StopApplicationEvent(self, appname, app):
        self._remove_ui_menus(app.window.uimanager)

    def _on_SaleStatusChanged(self, sale, old_status):
        if sale.status == Sale.STATUS_CONFIRMED:
            if old_status == Sale.STATUS_RETURNED:
                self._undo_returned_sale(sale)
            else:
                self._confirm_sale(sale)
                self._set_last_sale(sale, sale.store)

    def _on_SaleAvoidCancel(self, sale):
        if not sysparam.get_bool('ALLOW_CANCEL_LAST_COUPON'):
            return False
        if self._is_ecf_last_sale(sale):
            info(_("That is last sale in ECF. Return using the menu "
                   "ECF - Cancel Last Document"))
            return True
        return False

    def _on_TillOpen(self, till):
        return self._open_till(till)

    def _on_TillClose(self, till, previous_day):
        return self._close_till(till, previous_day)

    def _on_TillAddCash(self, till, value):
        self._add_cash(till, value)

    def _on_TillRemoveCash(self, till, value):
        self._remove_cash(till, value)

    def _on_CouponCreatedEvent(self, coupon, sale):
        self._coupon_create(coupon, sale)

    def _on_AddTillEntry(self, till_entry, store):
        self._set_last_till_entry(till_entry, store)

    def _on_HasPendingReduceZ(self):
        return self._has_pending_reduce()

    def _on_HasOpenCouponEvent(self):
        self._has_open_coupon()

    #
    # Callbacks
    #

    def _on_coupon__open(self, coupon):
        self._validate_printer()
        document = None
        if not coupon.identify_customer_at_end:
            document = self._identify_customer(coupon)
        coupon.open()
        return document

    def _on_coupon__identify_customer(self, coupon, person):
        if person.individual:
            individual = person.individual
            document_type = FiscalSaleHistory.TYPE_CPF
            document = individual.cpf
        elif person.company:
            company = person.company
            document_type = FiscalSaleHistory.TYPE_CNPJ
            document = company.cnpj
        else:
            raise TypeError(
                "identify_customer needs a individual or a company")
        name = person.name
        address = person.get_address_string()

        coupon.identify_customer(name, address, document, document_type)

    def _on_coupon__customer_identified(self, coupon):
        return coupon.is_customer_identified()

    def _on_coupon__add_item(self, coupon, item):
        self._validate_printer()
        return coupon.add_item(item)

    def _on_coupon__remove_item(self, coupon, item_id):
        coupon.remove_item(item_id)

    def _on_coupon__add_payments(self, coupon, sale):
        coupon.add_payments(sale)

    def _on_coupon__totalize(self, coupon, sale):
        coupon.totalize(sale)

    def _on_coupon__close(self, coupon, sale):
        if coupon.identify_customer_at_end:
            self._identify_customer(coupon, sale)

        return coupon.close(sale)

    def _on_coupon__cancel(self, coupon):
        if coupon.closed:
            # In this case, the Sale and TillEntries will be rolled back by
            # fiscalprinter. We only need to cancel the last coupon on the ecf
            if not self._printer.cancel_last_coupon():
                info(_("Coupon cancellation failed..."))
        else:
            coupon.cancel()

    def _on_coupon__get_coo(self, coupon):
        return coupon.get_coo()

    def _on_coupon__get_supports_duplicate(self, coupon):
        return coupon.supports_duplicate_receipt

    def _on_coupon__print_payment_receipt(self, coupon, coo, payment, value, receipt):
        coupon.print_payment_receipt(coo, payment, value, receipt)

    def _on_TillSummary__activate(self, action):
        self._till_summarize()

    def _on_ReadMemory__activate(self, action):
        self._fiscal_memory_dialog()

    def _on_CancelLastDocument__activate(self, action):
        self._cancel_last_document()

    def _on_ConfigurePrinter__activate(self, action=None):
        run_dialog(ECFListDialog, None)

    def _on_GerencialReportCancelEvent(self):
        self._printer._driver.gerencial_report_close()

    def _on_GerencialReportPrintEvent(self, receipt, close_previous=False):
        try:
            self._validate_printer()
        except DeviceError as e:
            warning(str(e))
            return

        if close_previous:
            # FIXME: dont call _driver directly
            # Try closing any previously opened report. This is TEF specific, to
            # workaround the tests where they turn off the printer
            self._printer._driver.gerencial_report_close()

        self._printer.print_report(receipt)

    def _on_CheckECFStateEvent(self):
        self._check_ecf_state()

    def _on_EditorCreateEvent(self, editor, model, store, *args):
        from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
        manager = get_plugin_manager()
        nfe_active = manager.is_active('nfe')
        if not nfe_active and isinstance(editor, SaleDetailsDialog):
            # Only display the coupon number if the nfe is not active.
            editor.invoice_label.set_text(_('Coupon Number'))
            editor.invoice_number.update(model.coupon_id)
