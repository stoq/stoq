# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano <henrique@async.com.br>
##
"""
stoq/lib/drivers.py

   Useful functions for StoqDrivers compability.
"""

import gettext
import socket

import gtk
from sqlobject.sqlbuilder import OR
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.exceptions import _warn
from kiwi.ui.dialogs import warning
from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.constants import (UNIT_EMPTY, TAX_NONE, MONEY_PM,
                                   CHEQUE_PM)
from stoqdrivers.exceptions import (PendingReduceZ, PendingReadX,
                                    CouponOpenError, DriverError,
                                    ReduceZError, OutofPaperError,
                                    PrinterOfflineError)

from stoq.lib.runtime import new_transaction
from stoq.domain.interfaces import (IIndividual, IPaymentGroup,
                                    IMoneyPM, ICheckPM)
from stoq.domain.drivers import PrinterSettings

_ = gettext.gettext
_printer = None

MAX_DIALOG_MESSAGE_LEN = 70

def get_printer_settings_by_hostname(conn, hostname):
    """ Returns the PrinterSettings object associated with the given
    hostname or None if there is not settings for it.
    """
    ipaddr = socket.gethostbyname(hostname)
    query = OR(PrinterSettings.q.host == hostname,
               PrinterSettings.q.host == ipaddr)
    result = PrinterSettings.select(query, connection=conn)
    result_quantity = result.count()
    if result_quantity > 1:
        raise DatabaseInconsistency("It's not possible to have more than one "
                                    "printer setting for the same machine")
    elif result_quantity == 0:
        return None
    return result[0]

def _get_fiscalprinter(conn):
    """ Returns a FiscalPrinter instance pre-configured to the current
    workstation.
    """
    global _printer
    if _printer:
        return _printer

    setting = get_printer_settings_by_hostname(conn, socket.gethostname())
    if setting:
        _printer = FiscalPrinter(brand=setting.brand, model=setting.model,
                                 device=setting.get_device_name())
    else:
        _warn("There is no fiscalprinter configured for this station (%s)"
              % socket.gethostname())
    return _printer

def _cancel(printer):
    """ @returns: True if the reduce Z has been emitted, False otherwise.
    """
    try:
        printer.cancel()
    except DriverError:
        return False
    return True

def _emit_reading(conn, cmd):
    printer = _get_fiscalprinter(conn)
    if not printer:
        return
    try:
        getattr(printer, cmd)()
    except CouponOpenError:
        return _cancel(printer)
    except DriverError:
        return False
    return True

def emit_read_X(conn):
    return _emit_reading(conn, 'summarize')

def emit_reduce_Z(conn):
    return _emit_reading(conn, 'close_till')

def emit_coupon(conn, sale):
    """ Emit a coupon for a Sale instance.

    @returns: True if the coupon has been emitted, False otherwise.
    """
    printer = _get_fiscalprinter(conn)
    if not printer:
        return False

    person = sale.client.get_adapted()
    address = person.get_main_address().get_address_string()
    individual = IIndividual(person, connection=person.get_connection())
    if individual is None:
        raise DatabaseInconsistency("The client must have a Individual facet")
    cpf = individual.cpf

    while True:
        try:
            printer.open(person.name, address, cpf)
            break
        except CouponOpenError:
            if not _cancel(printer):
                return False
        except OutofPaperError:
            if warning(
                _("The printer has run out of paper"),
                _("The printer %s has run out of paper.\nAdd more paper "
                  "before continuing." % printer.get_printer_name()),
                buttons=((_("Confirm later"), gtk.RESPONSE_CANCEL),
                         (_("Resume"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                return False
            return emit_coupon(conn, sale)
        except PrinterOfflineError:
            if warning(
                _("The printer is offline"),
                _("The printer %s is offline, turn it on and try again"
                  % printer.get_printer_name()),
                buttons=((_("Confirm later"), gtk.RESPONSE_CANCEL),
                         (_("Resume"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                return False
            return emit_coupon(conn, sale)
        except DriverError, details:
            warning(_("Isn't possible emit the coupon"), str(details))
            return False

    # XXX: Should we allow services be added in the coupon?
    for item in sale.get_items():
        sellable = item.sellable
        # FIXME: TAX_NONE is a HACK, waiting for bug #2269
        # FIXME: UNIT_EMPTY is temporary and will be remove when bug #2247
        # is fixed.
        printer.add_item(sellable.code, item.quantity, item.price, UNIT_EMPTY,
                         sellable.description, TAX_NONE, 0, 0)

    printer.totalize(sale.discount_value, sale.charge_value, TAX_NONE)

    group = IPaymentGroup(sale)
    for payment in group.get_items():
        if ICheckPM.providedBy(payment.method):
            money_type = CHEQUE_PM
        elif IMoneyPM.providedBy(payment.method):
            money_type = MONEY_PM
        # FIXME: A default value, this is wrong but can't be better right
        # now, since stoqdrivers doesn't have support for any payment
        # method diferent than money and cheque.  This will be improved
        # when bug #2246 is fixed.
        else:
            _warn(("The payment type %d isn't supported yet. The default, "
                   "MONEY_PM, will be used." % payment.method))
            money_type = MONEY_PM

        printer.add_payment(money_type, payment.value, '')

    try:
        printer.close()
    except DriverError, details:
        warning(_("Isn't possible close the coupon"), str(details))
        return False
