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
import os
import time

import gtk
from kiwi.log import Logger
from kiwi.python import Settable
from stoqdrivers.exceptions import CouponOpenError, DriverError
from stoqlib.database.runtime import (get_current_station, get_connection,
                                      new_transaction)
from stoqlib.domain.events import (SaleStatusChangedEvent, TillAddCashEvent,
                                   TillRemoveCashEvent, TillOpenEvent,
                                   TillCloseEvent, TillAddTillEntryEvent,
                                   GerencialReportPrintEvent,
                                   GerencialReportCancelEvent,
                                   CheckECFStateEvent,
                                   HasPendingReduceZ, ECFIsLastSaleEvent)
from stoqlib.domain.interfaces import IIndividual, ICompany
from stoqlib.domain.person import PersonAdaptToIndividual, PersonAdaptToCompany
from stoqlib.domain.renegotiation import RenegotiationData
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.exceptions import DeviceError
from stoqlib.gui.keybindings import add_bindings, get_accels
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.events import StartApplicationEvent, CouponCreatedEvent
from stoqlib.lib.message import info, warning, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

from cat52 import MODEL_CODES
from catgenerator import StoqlibCATGenerator
from couponprinter import CouponPrinter
from ecfdomain import ECFPrinter, FiscalSaleHistory
from ecfprinterdialog import ECFListDialog
from ecfmemorydialog import FiscalMemoryDialog
from paulistainvoicedialog import PaulistaInvoiceDialog

_ = stoqlib_gettext
log = Logger("stoq-ecf-plugin")


class ECFUI(object):
    def __init__(self):
        self.conn = get_connection()
        self._printer_verified = False
        self._printer = self._create_printer()

        SaleStatusChangedEvent.connect(self._on_SaleStatusChanged)
        ECFIsLastSaleEvent.connect(self._on_ECFIsLastSale)
        TillOpenEvent.connect(self._on_TillOpen)
        TillCloseEvent.connect(self._on_TillClose)
        TillAddCashEvent.connect(self._on_TillAddCash)
        TillAddTillEntryEvent.connect(self._on_AddTillEntry)
        TillRemoveCashEvent.connect(self._on_TillRemoveCash)
        StartApplicationEvent.connect(self._on_StartApplicationEvent)
        CouponCreatedEvent.connect(self._on_CouponCreatedEvent)
        GerencialReportPrintEvent.connect(self._on_GerencialReportPrintEvent)
        GerencialReportCancelEvent.connect(self._on_GerencialReportCancelEvent)
        CheckECFStateEvent.connect(self._on_CheckECFStateEvent)
        HasPendingReduceZ.connect(self._on_HasPendingReduceZ)

        self._till_summarize_action = gtk.Action(
            'Summary', _('Summary'), None, None)
        self._till_summarize_action.connect(
            'activate', self._on_TillSummary__activate)

        add_bindings([
            ('plugin.ecf.read_memory', '<Control>F9'),
            ('plugin.ecf.summarize', '<Control>F11'),
            ])

    #
    # Private
    #

    def _create_printer(self):
        station = get_current_station(self.conn)
        printer = ECFPrinter.selectOneBy(station=station, is_active=True,
                                         connection=self.conn)
        if printer:
            return CouponPrinter(printer)

    def _validate_printer(self):
        if self._printer is None:
            raise DeviceError(
                _("This operation requires a connected fiscal printer"))

        if not self._printer_verified:
            if not self._printer.check_serial():
                raise DeviceError(
                    _("Fiscalprinters serial number is different!"))

            self._printer_verified = True

    def _add_ui_menus(self, appname, app, uimanager):
        if appname == 'pos':
            self._add_pos_menus(uimanager)
        elif appname == 'till':
            self._add_till_menus(uimanager)
        elif appname == 'admin':
            self._add_admin_menus(uimanager)
            app.main_window.tasks.add_item(
                _('Fiscal Printers'), 'fiscal-printer', 'printer',
                self._on_ConfigurePrinter__activate)

    def _add_admin_menus(self, uimanager):
        ui_string = """<ui>
          <menubar name="menubar">
            <menu action="ConfigureMenu">
            <placeholder name="ConfigurePH">
              <menuitem action="ConfigurePrinter"/>
            </placeholder>
            </menu>
          </menubar>
        </ui>"""

        ag = gtk.ActionGroup('ECFMenuActions')
        ag.add_actions([
            ('ECFMenu', None, _('ECF')),
            ('ConfigurePrinter', None, _('Configure fiscal printer...'),
             None, None, self._on_ConfigurePrinter__activate),
            ])
        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

    def _add_pos_menus(self, uimanager):
        if sysparam(self.conn).POS_SEPARATE_CASHIER:
            return

        ui_string = """<ui>
          <menubar name="menubar">
            <placeholder name="ExtraMenu">
              <menu action="ECFMenu">
                <menuitem action="CancelLastDocument" name="CancelLastDocument"/>
                <menuitem action="Summary" name="Summary"/>
                <menuitem action="ReadMemory" name="ReadMemory"/>
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

        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

    def _add_till_menus(self, uimanager):
        ui_string = """<ui>
          <menubar name="menubar">
            <placeholder name="ExtraMenu">
              <menu action="ECFMenu">
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
            ])
        ag.add_action_with_accel(self._till_summarize_action,
                                 group.get('summarize'))
        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

    def _check_ecf_state(self):
        log.info('ecfui._check_printer')
        try:
            self._validate_printer()
        except (DriverError, DeviceError):
            warning('Não foi possível comunicar com a impressora.')
            raise SystemExit

        has_open = self._printer.has_open_coupon()
        if has_open:
            warning('A ECF tem um cupom aberto. Ele será cancelado agora.')
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

        if (sysparam(self.conn).ENABLE_PAULISTA_INVOICE and not
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

            dir = sysparam(self.conn).CAT52_DEST_DIR.path
            dir = os.path.expanduser(dir)
            if not os.path.exists(dir):
                os.mkdir(dir)

            generator = StoqlibCATGenerator(self.conn, day, printer)
            generator.write(dir)

        return retval

    def _needs_cat52(self, printer):
        # If the param is not enabled, we dont need.
        if not sysparam(self.conn).ENABLE_PAULISTA_INVOICE:
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

    def _set_last_sale(self, sale, trans):
        printer = trans.get(self._printer._printer)
        printer.last_sale = sale
        printer.last_till_entry = None

    def _set_last_till_entry(self, till_entry, trans):
        printer = trans.get(self._printer._printer)
        printer.last_till_entry = till_entry
        printer.last_sale = None

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

    def _coupon_create(self, fiscalcoupon):

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
            ('print-payment-receipt', self._on_coupon__print_payment_receipt),
            ]:
            fiscalcoupon.connect_object(signal, callback, coupon)
        return coupon

    def _get_last_document(self, trans):
        printer = self._printer.get_printer()
        return ECFPrinter.get_last_document(station=printer.station,
                                            conn=trans)

    def _confirm_last_document_cancel(self, last_doc):
        if last_doc.last_sale is None and last_doc.last_till_entry is None:
            info(_("There is no sale nor till entry to cancel"))
            return

        if last_doc.last_sale:
            msg = _("Do you really want to cancel the sale number %d "
                    "and value %.2f ?") % (last_doc.last_sale.id,
                                           last_doc.last_sale.total_amount)
        elif last_doc.last_till_entry.value > 0:
            msg = _("Do you really want to cancel the last cash added "
                    "number %d and value %.2f ?") % (
                        last_doc.last_till_entry.id,
                        last_doc.last_till_entry.value)
        else:
            msg = _("Do you really want to cancel the last cash removed "
                    "number %d and value %.2f ?") % (
                        last_doc.last_till_entry.id,
                        last_doc.last_till_entry.value)
        return yesno(msg, gtk.RESPONSE_NO, _("Cancel Last Document"),
                     _("Not now"))

    def _cancel_last_till_entry(self, last_doc, trans):
        till_entry = trans.get(last_doc.last_till_entry)
        try:
            self._printer.cancel_last_coupon()
            if till_entry.value > 0:
                till_entry.description = _("Cash out")
            else:
                till_entry.description = _("Cash in")
            till_entry.value = -till_entry.value
            last_doc.last_till_entry = None
            info(_("Document was cancelled"))
        except:
            info(_("Cancelling failed, nothing to cancel"))
            return

    def _cancel_last_sale(self, last_doc, trans):
        if last_doc.last_sale.status == Sale.STATUS_RETURNED:
            return
        sale = trans.get(last_doc.last_sale)
        renegotiation = RenegotiationData(
            reason=_("Cancel last document"),
            paid_total=sale.total_amount,
            invoice_number=sale.id,
            penalty_value=0,
            sale=sale,
            responsible=sale.salesperson,
            new_order=None,
            connection=trans)
        sale.return_(renegotiation)
        last_doc.last_sale = None
        info(_("Document was cancelled"))

    def _cancel_last_document(self):
        try:
            self._validate_printer()
        except DeviceError, e:
            warning(e)
            return

        trans = new_transaction()
        last_doc = self._get_last_document(trans)
        if not self._confirm_last_document_cancel(last_doc):
            trans.close()
            return

        if last_doc.last_till_entry:
            self._cancel_last_till_entry(last_doc, trans)
        else:
            # Verify till balance before cancel the last sale.
            till = Till.get_current(trans)
            if last_doc.last_sale.total_amount > till.get_balance():
                warning(_("You do not have this value on till."))
                trans.close()
                return
            cancelled = self._printer.cancel()
            if not cancelled:
                info(_("Cancelling sale failed, nothing to cancel"))
                trans.close()
                return
            else:
                self._cancel_last_sale(last_doc, trans)
        trans.commit()

    def _till_summarize(self):
        try:
            self._validate_printer()
        except DeviceError, e:
            warning(e)
            return

        self._printer.summarize()

    def _fiscal_memory_dialog(self):
        try:
            self._validate_printer()
        except DeviceError, e:
            warning(e)
            return
        run_dialog(FiscalMemoryDialog, None, self.conn, self._printer)

    def _get_client_document(self, sale):
        """Returns a Settable with two attributes: document, a string with
        the client cpf or cnpj and document_type, being one of
        (FiscalSaleHistory.TYPE_CPF, FiscalSaleHistory.TYPE_CNPJ )
        """
        client_role = sale.get_client_role()
        if isinstance(client_role, PersonAdaptToIndividual):
            document_type = FiscalSaleHistory.TYPE_CPF
            document = client_role.cpf
        elif isinstance(client_role, PersonAdaptToCompany):
            document_type = FiscalSaleHistory.TYPE_CNPJ
            document = client_role.cnpj
        else:
            return

        if document:
            return Settable(document_type=document_type,
                            document=document)

    def _identify_customer(self, coupon, sale=None):
        model = None
        if sale:
            model = self._get_client_document(sale)

        if sysparam(self.conn).ENABLE_PAULISTA_INVOICE and not model:
            model = run_dialog(PaulistaInvoiceDialog, self, self.conn)

        if model:
            coupon.identify_customer('-', '-', model.document,
                                     model.document_type)

    #
    # Events
    #

    def _on_StartApplicationEvent(self, appname, app):
        self._add_ui_menus(appname, app, app.main_window.uimanager)

    def _on_SaleStatusChanged(self, sale, old_status):
        if sale.status == Sale.STATUS_CONFIRMED:
            self._confirm_sale(sale)
            self._set_last_sale(sale, sale.get_connection())

    def _on_ECFIsLastSale(self, sale):
        last_doc = self._get_last_document(sale.get_connection())
        return last_doc.last_sale == sale

    def _on_TillOpen(self, till):
        return self._open_till(till)

    def _on_TillClose(self, till, previous_day):
        return self._close_till(till, previous_day)

    def _on_TillAddCash(self, till, value):
        self._add_cash(till, value)

    def _on_TillRemoveCash(self, till, value):
        self._remove_cash(till, value)

    def _on_CouponCreatedEvent(self, coupon):
        self._coupon_create(coupon)

    def _on_AddTillEntry(self, till_entry, trans):
        self._set_last_till_entry(till_entry, trans)

    def _on_HasPendingReduceZ(self):
        return self._has_pending_reduce()

    #
    # Callbacks
    #

    def _on_coupon__open(self, coupon):
        self._validate_printer()
        if not coupon.identify_customer_at_end:
            self._identify_customer(coupon)
        coupon.open()

    def _on_coupon__identify_customer(self, coupon, person):
        if IIndividual(person, None):
            individual = IIndividual(person)
            document_type = FiscalSaleHistory.TYPE_CPF
            document = individual.cpf
        elif ICompany(person, None):
            company = ICompany(person)
            document_type = FiscalSaleHistory.TYPE_CNPJ
            document = company.cnpj
        else:
            raise TypeError(
                "identify_customer needs an object implementing "
                "IIndividual or ICompany")
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
        except DeviceError, e:
            warning(e)
            return

        if close_previous:
            # FIXME: dont call _driver directly
            # Try closing any previously opened report. This is TEF specific, to
            # workaround the tests where they turn off the printer
            self._printer._driver.gerencial_report_close()

        self._printer.print_report(receipt)

    def _on_CheckECFStateEvent(self):
        self._check_ecf_state()
