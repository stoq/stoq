# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import sys

import gobject
import gtk
from kiwi.log import Logger
from kiwi.utils import gsignal
from stoqdrivers.exceptions import (DriverError, CouponOpenError,
                                    OutofPaperError, PrinterOfflineError)
from zope.interface import implements

from stoqlib.api import api
from stoqlib.domain.events import (CardPaymentReceiptPrepareEvent,
                                   CardPaymentReceiptPrintedEvent,
                                   GerencialReportPrintEvent,
                                   GerencialReportCancelEvent,
                                   CancelPendingPaymentsEvent,
                                   HasPendingReduceZ)
from stoqlib.domain.interfaces import ICompany, IContainer
from stoqlib.domain.till import Till
from stoqlib.drivers.cheque import print_cheques_for_payment_group
from stoqlib.exceptions import DeviceError, TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.tilleditor import TillOpeningEditor, TillClosingEditor
from stoqlib.gui.events import CouponCreatedEvent
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard


_ = stoqlib_gettext


log = Logger('stoqlib.fiscalprinter')

(CLOSE_TILL_NONE,
 CLOSE_TILL_DB,
 CLOSE_TILL_ECF,
 CLOSE_TILL_BOTH) = range(4)


def _flush_interface():
    """ Sometimes we need to 'flush' interface, so that the dialog has some
    time to disaperar before we send a blocking command to the printer
    """
    while gtk.events_pending():
        gtk.main_iteration()

# FIXME: Maybe this should be a singleton


class FiscalPrinterHelper(gobject.GObject):
    """

    Signals
    =======
      - B{till-status-changed} (bool, bool):
        - Emitted when the status of the till has changed. it can be
          open/closed, and while open/closed, it can be blocked

      - B{ecf-changed} (bool):
        - Emitted fater the check_till method is called, indicating if a
          ecf printer is present and functional.

    """
                                # Closed, Blocked
    gsignal('till-status-changed', bool, bool)
                        # has_ecf
    gsignal('ecf-changed', bool)

    def __init__(self, conn, parent):
        """ Creates a new FiscalPrinterHelper object
        @param conn:
        @param parent: a gtk.Window subclass or None
        """
        gobject.GObject.__init__(self)
        self.conn = conn
        self._parent = parent

    def open_till(self):
        """Opens the till
        """
        if Till.get_current(self.conn) is not None:
            warning("You already have a till operation opened. "
                    "Close the current Till and open another one.")
            return False

        trans = api.new_transaction()
        try:
            model = run_dialog(TillOpeningEditor, self._parent, trans)
        except TillError, e:
            warning(e)
            model = None

        retval = api.finish_transaction(trans, model)
        trans.close()
        if retval:
            self._till_status_changed(closed=False, blocked=False)
        return retval

    def close_till(self, close_db=True, close_ecf=True):
        """Closes the till

        close_db and close_ecf should be different than True only when
        fixing an conflicting status: If the DB is open but the ECF is
        closed, or the other way around.

        @param close_db: If the till in the DB should be closed
        @param close_ecf: If the till in the ECF should be closed
        @returns: True if the till was closed, otherwise False
        """

        if not self._previous_day:
            if not yesno(_("You can only close the till once per day. "
                           "You won't be able to make any more sales today.\n\n"
                           "Close the till?"),
                         gtk.RESPONSE_NO, _("Close Till"), _("Not now")):
                return
        else:
            # When closing from a previous day, close only what is needed.
            close_db = self._close_db
            close_ecf = self._close_ecf

        if close_db:
            till = Till.get_last_opened(self.conn)
            assert till

        trans = api.new_transaction()
        model = run_dialog(TillClosingEditor, self._parent, trans,
                           previous_day=self._previous_day, close_db=close_db,
                           close_ecf=close_ecf)

        if not model:
            api.finish_transaction(trans, model)
            return

        # TillClosingEditor closes the till
        retval = api.finish_transaction(trans, model)
        trans.close()
        if retval:
            self._till_status_changed(closed=True, blocked=False)
        return retval

    def needs_closing(self):
        """Checks if the last opened till was closed and asks the
        user if he wants to close it

        @returns:
            - CLOSE_TILL_BOTH if both DB and ECF needs closing.
            - CLOSE_TILL_DB if only DB needs closing.
            - CLOSE_TILL_ECF if only ECF needs closing.
            - CLOSE_TILL_NONE if both ECF and DB are consistent (they may be
                  closed, or open for the current day)
        """
        ecf_needs_closing = HasPendingReduceZ.emit()

        last_till = Till.get_last(self.conn)
        if last_till:
            db_needs_closing = last_till.needs_closing()
        else:
            db_needs_closing = False

        if db_needs_closing and ecf_needs_closing:
            return CLOSE_TILL_BOTH
        elif db_needs_closing and not ecf_needs_closing:
            return CLOSE_TILL_DB
        elif ecf_needs_closing and not db_needs_closing:
            return CLOSE_TILL_ECF
        else:
            return CLOSE_TILL_NONE

    def create_coupon(self):
        """ Creates a new fiscal coupon
        @returns: a new coupon
        """

        if sysparam(self.conn).DEMO_MODE:
            branch = api.get_current_branch(self.conn)
            company = ICompany(branch.person, None)
            if company and company.cnpj not in ['24.198.774/7322-35',
                                                '66.873.574/0001-82']:
                # FIXME: Find a better description for the warning bellow.
                warning(_("You are not allowed to sell in branches not "
                          "created by the demonstration mode"))
        coupon = FiscalCoupon(self._parent)

        try:
            CouponCreatedEvent.emit(coupon)
        except (DriverError, DeviceError):
            warning('Não foi possível abrir o cupom')
            coupon = None

        return coupon

    def setup_midnight_check(self):
        """Check the till after the day changes.

        If Stoq is open, the day changes, and the user tries to
        confirm a sale (or do any other fiscal operation), an
        error will happen.

        This method will call check_till that will eventually,
        disable fiscal related interface.
        """
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(1)

        # Get the delta between now and tomorrow (midnight)
        midnight = tomorrow.replace(hour=0, minute=0, second=0)
        delta = midnight - now

        # Call check_till at the first seconds of the next day.
        gobject.timeout_add(delta.seconds * 1000, self.check_till)

    def _till_status_changed(self, closed, blocked):
        self.emit('till-status-changed', closed, blocked)

    def _check_needs_closing(self):
        needs_closing = self.needs_closing()

        # DB and ECF are ok
        if needs_closing is CLOSE_TILL_NONE:
            self._previous_day = False
            # We still need to check if the till is open or closed.
            till = Till.get_current(self.conn)
            self._till_status_changed(closed=not till, blocked=False)
            return True

        close_db = needs_closing in (CLOSE_TILL_DB, CLOSE_TILL_BOTH)
        close_ecf = needs_closing in (CLOSE_TILL_ECF, CLOSE_TILL_BOTH)

        # DB or ECF is open from a previous day
        self._till_status_changed(closed=False, blocked=True)
        self._previous_day = True

        # Save this statuses in case the user chooses not to close now.
        self._close_db = close_db
        self._close_ecf = close_ecf

        manager = get_plugin_manager()
        if close_db and (close_ecf or not manager.is_active('ecf')):
            msg = _("You need to close the till from the previous day before "
                    "creating a new order.\n\nClose the Till?")
        elif close_db and not close_ecf:
            msg = _("The till in Stoq is opened, but in ECF "
                    "is closed.\n\nClose the till in Stoq?")
        elif close_ecf and not close_db:
            msg = _("The till in stoq is closed, but in ECF "
                    "is opened.\n\nClose the till in ECF?")

        if yesno(msg, gtk.RESPONSE_NO, _("Close Till"), _("Not now")):
            return self.close_till(close_db, close_ecf)

        return False

    def check_till(self):
        try:
            self._check_needs_closing()
            self.emit('ecf-changed', True)
        except (DeviceError, DriverError), e:
            warning(e)
            self.emit('ecf-changed', False)


class FiscalCoupon(gobject.GObject):
    """ This class is used just to allow us cancel an item with base in a
    Sellable object. Currently, services can't be added, and they
    are just ignored -- be aware, if a coupon with only services is
    emitted, it will not be opened in fact, but just ignored.
    """
    implements(IContainer)

    gsignal('open')
    gsignal('identify-customer', object)
    gsignal('customer-identified', retval=bool)
    gsignal('add-item', object, retval=int)
    gsignal('remove-item', object)
    gsignal('add-payments', object)
    gsignal('totalize', object)
    gsignal('close', object, retval=int)
    gsignal('cancel')
    gsignal('get-coo', retval=int)
    gsignal('get-supports-duplicate-receipt', retval=bool)
                                   # coo, payment, value, text
    gsignal('print-payment-receipt', int, object, object, str)
    gsignal('cancel-payment-receipt')

    def __init__(self, parent):
        gobject.GObject.__init__(self)

        self._coo = None
        self._parent = parent
        self._item_ids = {}

    def emit(self, signal, *args):
        sys.last_value = None

        # This is evil, set/restore the excepthook
        oldhook = sys.excepthook
        sys.excepthook = lambda *x: None
        retval = gobject.GObject.emit(self, signal, *args)
        sys.excepthook = oldhook

        if sys.last_value is not None:
            #import traceback
            #print 'Exception caught in signal emission for %s::%s:' % (
            #    gobject.type_name(self), signal)
            #traceback.print_exception(sys.last_type, sys.last_value,
            #                          sys.last_traceback)
            raise sys.last_value
        return retval

    #
    # IContainer implementation
    #

    def add_item(self, sale_item):
        """ Adds an item to fiscal coupon

        @param sale_item: a sale item
        @returns: id of the sale_item.:
          0 >= if it was added successfully
          -1 if an error happend
          0 if added but not printed (free deliveries)
        """
        if sale_item.price <= 0:
            return 0

        log.info("adding sale item %r to coupon" % (sale_item, ))
        item_id = self.emit('add-item', sale_item)

        ids = self._item_ids.setdefault(sale_item, [])
        ids.append(item_id)
        return item_id

    def get_items(self):
        return self._item_ids.keys()

    def remove_item(self, sale_item):
        if sale_item.price <= 0:
            return

        for item_id in self._item_ids.pop(sale_item):
            log.info("removing sale item %r from coupon" % (sale_item, ))
            try:
                self.emit('remove-item', item_id)
            except DriverError:
                return False
        return True

    #
    # Fiscal coupon related functions
    #

    def identify_customer(self, person):
        self.emit('identify-customer', person)

    def is_customer_identified(self):
        return self.emit('customer-identified')

    def open(self):
        while True:
            log.info("opening coupon")
            try:
                self.emit('open')
                break
            except CouponOpenError:
                if not self.cancel():
                    return False
            except OutofPaperError:
                if not yesno(
                    _("The fiscal printer has run out of paper.\nAdd more paper "
                      "before continuing."),
                    gtk.RESPONSE_YES, _("Resume"), _("Confirm later")):
                    return False
                return self.open()
            except PrinterOfflineError:
                if not yesno(
                    (_(u"The fiscal printer is offline, turn it on and try "
                       "again")),
                    gtk.RESPONSE_YES, _(u"Resume"), _(u"Confirm later")):
                    return False
                return self.open()
            except (DriverError, DeviceError), e:
                warning(_(u"It is not possible to emit the coupon"),
                        str(e))
                return False

        self._coo = self.emit('get-coo')
        self.totalized = False
        self.coupon_closed = False
        self.payments_setup = False
        return True

    def confirm(self, sale, trans):
        # Actually, we are confirming the sale here, so the sale
        # confirmation process will be available to others applications
        # like Till and not only to the POS.
        model = run_dialog(ConfirmSaleWizard, self._parent, trans, sale)
        if not model:
            CancelPendingPaymentsEvent.emit()
            api.finish_transaction(trans, False)
            return False
        if sale.client and not self.is_customer_identified():
            self.identify_customer(sale.client.person)

        if not self.totalize(sale):
            api.finish_transaction(trans, False)
            return False

        if not self.setup_payments(sale):
            api.finish_transaction(trans, False)
            return False
        if not self.close(sale, trans):
            api.finish_transaction(trans, False)
            return False

        sale.confirm()

        if not self.print_receipts(sale):
            warning('A venda foi cancelada')
            sale.cancel()

        # Only finish the transaction after everything passed above.
        api.finish_transaction(trans, model)

        if sale.only_paid_with_money():
            sale.set_paid()
        else:
            sale.group.pay_money_payments()

        print_cheques_for_payment_group(trans, sale.group)
        return True

    def print_receipts(self, sale):
        #supports_duplicate = self.emit('get-supports-duplicate-receipt')
        # Vamos sempre imprimir sempre de uma vez, para simplificar
        supports_duplicate = False

        log.info('Printing payment receipts')

        # Merge card payments by nsu
        card_payments = {}
        for payment in sale.payments:
            if payment.method.method_name != 'card':
                continue
            operation = payment.method.operation
            card_data = operation.get_card_data_by_payment(payment)
            card_payments.setdefault(card_data.nsu, [])
            card_payments[card_data.nsu].append(payment)

        any_failed = False
        for nsu, payment_list in card_payments.items():
            receipt = CardPaymentReceiptPrepareEvent.emit(nsu, supports_duplicate)
            if receipt is None:
                continue

            value = sum([p.value for p in payment_list])

            # This is BS, but if any receipt failed to print, we must print
            # the remaining ones in Gerencial Rports
            if any_failed:
                retval = self.reprint_payment_receipt(receipt)
            else:
                retval = self.print_payment_receipt(payment_list[0], value, receipt)
            while not retval:
                if not yesno(_(u"Erro na impressão. Deseja tentar novamente?"),
                         gtk.RESPONSE_YES,
                         _("Sim"), _(u"Não")):
                    CancelPendingPaymentsEvent.emit()
                    try:
                        GerencialReportCancelEvent.emit()
                    except (DriverError, DeviceError), details:
                        log.info('Error canceling last receipt: %s' %
                                    details)
                        warning(u'Não foi possível cancelar o último'
                                 ' comprovante')
                    return False
                any_failed = True
                _flush_interface()
                retval = self.reprint_payment_receipt(receipt,
                                                      close_previous=True)

        # Only confirm payments receipt printed if *all* receipts wore
        # printed.
        for nsu in card_payments.keys():
            CardPaymentReceiptPrintedEvent.emit(nsu)

        return True

    def totalize(self, sale):
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True

        if self.totalized:
            return True

        log.info('Totalizing coupon')
        while True:
            try:
                self.emit('totalize', sale)
                self.totalized = True
                return True
            except (DriverError, DeviceError), details:
                log.info("It is not possible to totalize the coupon: %s"
                            % str(details))
                if not yesno(_(u"Erro na impressão. Deseja tentar novamente?"),
                         gtk.RESPONSE_YES,
                         _("Sim"), _(u"Não")):
                    CancelPendingPaymentsEvent.emit()
                    return False
                _flush_interface()

    def cancel(self):
        log.info('Canceling coupon')
        while True:
            try:
                self.emit('cancel')
                break
            except (DriverError, DeviceError), details:
                log.info("Error canceling coupon: %s" % str(details))
                if not yesno(_(u"Erro cancelando cupom. Deseja tentar novamente?"),
                         gtk.RESPONSE_YES,
                         _("Sim"), _(u"Não")):
                    return False
                _flush_interface()
        return True

    # FIXME: Rename to add_payment_group(group)
    def setup_payments(self, sale):
        """ Add the payments defined in the sale to the coupon. Note that this
        function must be called after all the payments has been created.
        """
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True

        if self.payments_setup:
            return True

        log.info('Adding payments to the coupon')
        while True:
            try:
                self.emit('add-payments', sale)
                self.payments_setup = True
                return True
            except (DriverError, DeviceError), details:
                log.info("It is not possible to add payments to the coupon: %s"
                            % str(details))
                if not yesno(_(u"Erro na impressão. Deseja tentar novamente?"),
                         gtk.RESPONSE_YES,
                         _("Sim"), _(u"Não")):
                    CancelPendingPaymentsEvent.emit()
                    return False
                _flush_interface()

    def close(self, sale, trans):
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True

        if self.coupon_closed:
            return True

        log.info('Closing coupon')
        while True:
            try:
                coupon_id = self.emit('close', sale)
                sale.coupon_id = coupon_id
                self.coupon_closed = True
                return True
            except (DeviceError, DriverError), details:
                log.info("It is not possible to close the coupon: %s"
                            % str(details))
                if not yesno(_(u"Erro na impressão. Deseja tentar novamente?"),
                         gtk.RESPONSE_YES,
                         _("Sim"), _(u"Não")):
                    CancelPendingPaymentsEvent.emit()
                    return False
                _flush_interface()

    def print_payment_receipt(self, payment, value, receipt):
        """Print the receipt for the payment.

        This must be called after the coupon is closed.
        """

        try:
            self.emit('print-payment-receipt', self._coo, payment, value, receipt)
            return True
        except (DriverError, DeviceError), details:
            log.info("Error printing payment receipt: %s"
                        % str(details))
            return False

    def reprint_payment_receipt(self, receipt, close_previous=False):
        """Re-Print the receipt for the payment.
        """

        try:
            GerencialReportPrintEvent.emit(receipt, close_previous)
            return True
        except (DriverError, DeviceError), details:
            log.info("Error printing gerencial report: %s"
                        % str(details))
            return False
