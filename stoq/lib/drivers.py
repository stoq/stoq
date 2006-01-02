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
## Author(s):   Henrique Romano         <henrique@async.com.br>
##              Evandro Vale Miquelito  <evandro@async.com.br>
##
"""
stoq/lib/drivers.py

   Useful functions for StoqDrivers compability.
"""

import gettext
import socket

import gtk
from zope.interface import implements
from sqlobject.sqlbuilder import OR
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.exceptions import _warn
from kiwi.ui.dialogs import warning, error
from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.constants import (UNIT_EMPTY, TAX_NONE, MONEY_PM,
                                   CHEQUE_PM)
from stoqdrivers.exceptions import (CouponOpenError, DriverError,
                                    OutofPaperError, PrinterOfflineError)

from stoq.domain.drivers import PrinterSettings
from stoq.domain.interfaces import (IIndividual, IPaymentGroup,
                                    IMoneyPM, ICheckPM, IContainer)

_ = gettext.gettext
_printer = None

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
        error(_("There is no printer configured"),
              _("There is no printer configured this station (\"%s\")"
                % socket.gethostname()))
    return _printer

def _emit_reading(conn, cmd):
    printer = _get_fiscalprinter(conn)
    if not printer:
        return False
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

def emit_coupon(sale, conn):
    """ Emit a coupon for a Sale instance.

    @returns: True if the coupon has been emitted, False otherwise.
    """
    coupon = FiscalCoupon(conn, sale)
    person = sale.client.get_adapted()
    if person:
        coupon.identify_customer(person)
    if not coupon.open():
        return False
    map(coupon.add_item, sale.get_items())
    if not coupon.totalize():
        return False
    if not coupon.setup_payments():
        return False
    return coupon.close()

#
# Class definitions
#

class FiscalCoupon:
    """ This class is used just to allow us cancel an item with base in a
    AbstractSellable object.
    """
    implements(IContainer)
    
    #
    # IContainer implementation
    #

    def __init__(self, conn, sale):
        self.sale = sale
        self.conn = conn
        self.printer = _get_fiscalprinter(conn)
        if not self.printer:
            raise ValueError
        self._item_ids = {}

    def add_item(self, item):
        sellable = item.sellable
        description = sellable.base_sellable_info.description
        # FIXME: TAX_NONE is a HACK, waiting for bug #2269
        # FIXME: UNIT_EMPTY is temporary and will be remove when bug #2247
        # is fixed.
        item_id = self.printer.add_item(sellable.code, item.quantity,
                                        item.price, UNIT_EMPTY,
                                        description, TAX_NONE, 0, 0)
        self._item_ids[item] = item_id

    def get_items(self):
        return self._item_ids.values()

    def remove_item(self, sellable):
        item_id = self._item_ids[sellable]
        try:
            self.printer.cancel_item(item_id)
        except DriverError:
            return False
        del self._item_ids[sellable]
        return True

    #
    # Fiscal coupon related functions
    #

    def identify_customer(self, person):
        address = person.get_main_address().get_address_string()
        individual = IIndividual(person, connection=person.get_connection())
        if individual is None:
            raise DatabaseInconsistency("The client must have a "
                                        "Individual facet")
        cpf = individual.cpf
        self.printer.identify_customer(person.name, address, cpf)

    def open(self):
        while True:
            try:
                self.printer.open()
                break
            except CouponOpenError:
                if not self.cancel():
                    return False
            except OutofPaperError:
                if warning(
                    _("The printer has run out of paper"),
                    _("The printer %s has run out of paper.\nAdd more paper "
                      "before continuing." % printer.get_printer_name()),
                    buttons=((_("Confirm later"), gtk.RESPONSE_CANCEL),
                             (_("Resume"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                    return False
                return self.open()
            except PrinterOfflineError:
                if warning(
                    _("The printer is offline"),
                    _("The printer %s is offline, turn it on and try again"
                      % printer.get_printer_name()),
                    buttons=((_("Confirm later"), gtk.RESPONSE_CANCEL),
                             (_("Resume"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                    return False
                return self.open()
            except DriverError, details:
                warning(_("It's not possible to emit the coupon"), str(details))
                return False
        return True

    def totalize(self):
        self.printer.totalize(self.sale.discount_value,
                              self.sale.charge_value, TAX_NONE)
        return True

    def cancel(self):
        try:
            self.printer.cancel()
        except DriverError:
            return False
        return True

    def setup_payments(self):
        """ Add the payments defined in the sale to the coupon. Note that this
        function must be called after all the payments has been created.
        """
        sale = self.sale
        group = IPaymentGroup(sale, connection=self.conn)
        if not group:
            raise ValueError("The sale object must have a PaymentGroup facet at "
                             "this point.")
        if group.default_method == group.METHOD_GIFT_CERTIFICATE:
            self.printer.add_payment(MONEY_PM, 
                                     sale.get_total_sale_amount(), '')
        else:
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
                    _warn(_("The payment type %s isn't supported yet. The default, "
                            "MONEY_PM, will be used.") 
                          % payment.method.description)
                    money_type = MONEY_PM
                self.printer.add_payment(money_type, payment.base_value, '')
        return True

    def close(self):
        try:
            self.printer.close()
        except DriverError, details:
            warning(_("It's not possible to close the coupon"), str(details))
            return False
        return True

