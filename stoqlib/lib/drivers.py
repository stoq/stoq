# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano         <henrique@async.com.br>
##              Evandro Vale Miquelito  <evandro@async.com.br>
##
""" Useful functions for StoqDrivers interaction """

import socket

import gtk
from zope.interface import implements
from sqlobject.sqlbuilder import OR, AND
from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.devices.printers.cheque import ChequePrinter
from stoqdrivers.devices.scales.scales import Scale
from stoqdrivers.constants import (UNIT_EMPTY, UNIT_CUSTOM, TAX_NONE,
                                   MONEY_PM, CHEQUE_PM, CUSTOM_PM)
from stoqdrivers.exceptions import (CouponOpenError, DriverError,
                                    OutofPaperError, PrinterOfflineError)

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import warning, info, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.defaults import METHOD_GIFT_CERTIFICATE, get_all_methods_dict
from stoqlib.lib.runtime import new_transaction
from stoqlib.database import finish_transaction
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.devices import DeviceSettings
from stoqlib.domain.interfaces import (IIndividual, ICompany, IPaymentGroup,
                                       ICheckPM, IMoneyPM, IContainer)

_ = stoqlib_gettext
_printer = None
_scale = None


#
# General routines
#


def _get_fiscalprinter(conn):
    """ Returns a FiscalPrinter instance pre-configured to the current
    workstation.
    """
    global _printer
    if _printer:
        return _printer

    setting = get_fiscal_printer_settings_by_hostname(conn,
                                                      socket.gethostname())
    if setting and setting.is_active:
        _printer = FiscalPrinter(brand=setting.brand, model=setting.model,
                                 device=setting.get_port_name(),
                                 consts=setting.constants)
    else:
        warning(_(u"There is no fiscal printer"),
               _(u"There is no fiscal printer configured for this "
                "station (\"%s\") or the printer is not enabled "
                "currently." % socket.gethostname()))
    return _printer

def _get_scale(conn):
    """ Returns a Scale instance pre-configured for the current
    workstation.
    """
    global _scale
    if _scale:
        return _scale
    setting = get_scale_settings_by_hostname(conn, socket.gethostname())
    if setting and setting.is_active:
        _scale = Scale(brand=setting.brand, model=setting.model,
                       device=setting.get_port_name())
    else:
        warning(_(u"There is no scale configured"),
               _(u"There is no scale configured for this station "
                "(\"%s\") or the scale is not enabled currently"
                % socket.gethostname()))
    return _scale

def _emit_reading(conn, cmd):
    printer = _get_fiscalprinter(conn)
    if not printer:
        return False
    try:
        getattr(printer, cmd)()
    except CouponOpenError:
        return printer.cancel()
    except DriverError:
        return False
    return True


#
# Public API
#


def get_device_settings_by_hostname(conn, hostname, device_type):
    ipaddr = socket.gethostbyname(hostname)
    query = OR(DeviceSettings.q.host == hostname,
               DeviceSettings.q.host == ipaddr)
    query = AND(query, DeviceSettings.q.type == device_type)
    result = DeviceSettings.select(query, connection=conn)
    result_quantity = result.count()
    if result_quantity > 1:
        raise DatabaseInconsistency("It's not possible to have more than "
                                    "one setting for the same device type"
                                    " and the same machine")
    return result_quantity and result[0] or None

def get_fiscal_printer_settings_by_hostname(conn, hostname):
    """ Returns the DeviceSettings object representing the printer currently
    associated with the given hostname or None if there is not settings for
    it.
    """
    return get_device_settings_by_hostname(conn, hostname,
                                           DeviceSettings.FISCAL_PRINTER_DEVICE)

def get_current_cheque_printer_settings(conn):
    res = get_device_settings_by_hostname(conn, socket.gethostname(),
                                          DeviceSettings.CHEQUE_PRINTER_DEVICE)
    if not res:
        return None
    elif not isinstance(res, DeviceSettings):
        raise TypeError("Invalid setting returned by "
                        "get_current_cheque_printer_settings")
    return ChequePrinter(brand=res.brand, model=res.model,
                         device=res.get_port_name())

def get_scale_settings_by_hostname(conn, hostname):
    """ Return the DeviceSettings object representing the scale currently
    associated with the given hostname or None if there is no
    settings for it.
    """
    return get_device_settings_by_hostname(conn, hostname,
                                           DeviceSettings.SCALE_DEVICE)

def get_current_scale_settings(conn):
    return get_scale_settings_by_hostname(conn, socket.gethostname())

def create_virtual_printer_for_current_host():
    conn = new_transaction()
    if get_fiscal_printer_settings_by_hostname(conn, socket.gethostname()):
        finish_transaction(conn)
        return
    DeviceSettings(host=socket.gethostname(),
                   device=DeviceSettings.DEVICE_SERIAL1,
                   brand='virtual', model='Simple',
                   type=DeviceSettings.FISCAL_PRINTER_DEVICE,
                   connection=conn)
    finish_transaction(conn, 1)


def check_virtual_printer_for_current_host(conn):
    """Returns True if the fiscal printer for the current host is
    a virtual one
    """
    printer = _get_fiscalprinter(conn)
    if not printer:
        raise ValueError("There should be a fiscal printer defined "
                         "at this point")
    return printer.brand == 'virtual'

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

def read_scale_info(conn):
    """ Read informations from the scale configured for this station.
    """
    scale = _get_scale(conn)
    dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_NONE)
    dlg.set_markup("<span size=\"medium\"><b>%s</b></span>"
                   % _("Waiting Scale Reading..."))
    dlg.set_position(gtk.WIN_POS_CENTER)
    def notifyfunc(scale, dummy):
        dlg.destroy()
    scale.notify_read(notifyfunc)
    dlg.run()
    return scale.read_data()

def get_capability(printer, name):
    return printer.get_capabilities()[name].max_len

def print_cheques_for_payment_group(conn, group):
    """ Given a instance that implements the IPaymentGroup interface, iterate
    over all its items printing a cheque for them.
    """
    payments = group.get_items()
    printer = get_current_cheque_printer_settings(conn)
    if not printer:
        return
    printer_banks = printer.get_banks()
    current_branch = sysparam(conn).CURRENT_BRANCH
    main_address = current_branch.get_adapted().get_main_address()
    if not main_address:
        raise ValueError("The cheque can not be printed since there is no "
                         "main address defined for the current branch.")

    max_len = get_capability(printer, "cheque_city")
    city = main_address.city_location.city[:max_len]
    for idx, payment in enumerate(payments):
        method = payment.method
        if not ICheckPM.providedBy(method):
            continue
        check_data = method.get_check_data_by_payment(payment)
        bank_id = check_data.bank_data.bank_id
        try:
            bank = printer_banks[bank_id]
        except KeyError:
            continue
        thirdparty = group.get_thirdparty()
        info(_(u"Insert Cheque %d") % (idx+1))
        max_len = get_capability(printer, "cheque_thirdparty")
        thirdparty = thirdparty and thirdparty.name[:max_len] or ""
        printer.print_cheque(bank, payment.value, thirdparty, city)


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
            raise ValueError("It is not possible to emit coupon "
                             "since there is no fiscal printer "
                             "configured for this station")
        self._item_ids = {}

    def add_item(self, item):
        sellable = item.sellable
        max_len = get_capability(self.printer, "item_description")
        description = sellable.base_sellable_info.description[:max_len]
        unit_desc = ''
        if not sellable.unit:
            unit = UNIT_EMPTY
        else:
            if sellable.unit.index == UNIT_CUSTOM:
                unit_desc = sellable.unit.description
            unit = sellable.unit.index
        unit = unit or UNIT_EMPTY
        max_len = get_capability(self.printer, "item_code")
        code = sellable.get_code_str()[:max_len]

        # FIXME: TAX_NONE is a HACK, waiting for bug #2269
        item_id = self.printer.add_item(code, item.quantity, item.price,
                                        unit, description,  TAX_NONE, 0,
                                        0, unit_desc=unit_desc)
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
        max_len = get_capability(self.printer, "customer_id")
        conn = person.get_connection()
        if IIndividual(person, connection=conn):
            individual = IIndividual(person, connection=person.get_connection())
            document = individual.cpf[:max_len]
        elif ICompany(person, connection=conn):
            company = ICompany(person, connection=person.get_connection())
            document = company.cnpj[:max_len]
        else:
            raise TypeError(
                "identify_customer needs an object implementing "
                "IIndividual or ICompany")
        max_len = get_capability(self.printer, "customer_name")
        name = person.name[:max_len]
        max_len = get_capability(self.printer, "customer_address")
        address = person.get_address_string()[:max_len]
        self.printer.identify_customer(name, address, document)

    def open(self):
        while True:
            try:
                self.printer.open()
                break
            except CouponOpenError:
                if not self.cancel():
                    return False
            except OutofPaperError:
                if yesno(
                    _(u"The printer %s has run out of paper.\nAdd more paper "
                      "before continuing." % self.printer.get_printer_name()),
                    default=gtk.RESPONSE_OK,
                    buttons=((_(u"Confirm later"), gtk.RESPONSE_CANCEL),
                             (_(u"Resume"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                    return False
                return self.open()
            except PrinterOfflineError:
                if yesno(
                    _(u"The printer %s is offline, turn it on and try again"
                      % self.printer.get_printer_name()),
                    default=gtk.RESPONSE_OK,
                    buttons=((_(u"Confirm later"), gtk.RESPONSE_CANCEL),
                             (_(u"Resume"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                    return False
                return self.open()
            except DriverError, details:
                warning(_(u"It's not possible to emit the coupon"),
                        str(details))
                return False
        return True

    def totalize(self):
        discount = self.sale.discount_percentage
        charge = self.sale.charge_percentage
        if discount > charge:
            discount = discount - charge
            charge = 0
        elif charge > discount:
            charge = charge - discount
            discount = 0
        else:
            # If these values are greater than zero we will get problems in
            # stoqdrivers
            charge = discount = 0
        self.printer.totalize(discount, charge, TAX_NONE)
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
        if group.default_method == METHOD_GIFT_CERTIFICATE:
            self.printer.add_payment(MONEY_PM, sale.get_total_sale_amount(),
                                     '')
            return True

        settings = get_fiscal_printer_settings_by_hostname(self.conn,
                                                           socket.gethostname())
        pm_constants = settings.pm_constants
        if not pm_constants:
            raise ValueError("It is not possible to setup the payments for sale "
                             "%r, since there is no payment methods defined for "
                             "the current printer being used (%r)"
                             % (sale, self.printer))
        all_methods = get_all_methods_dict()
        for payment in group.get_items():
            method = payment.method
            method_iface = method.get_implemented_iface()
            if method_iface in (ICheckPM, IMoneyPM):
                if method_iface is ICheckPM:
                    method_id = CHEQUE_PM
                else:
                    method_id = MONEY_PM
                self.printer.add_payment(method_id, payment.base_value)
                continue
            method_id = None
            for identifier, iface in all_methods.items():
                if iface is method_iface:
                    if method_id is not None:
                        raise TypeError("There is the same identifier for two "
                                        "different payment method interfaces. "
                                        "The identifier is %d" % method_id)
                    method_id = identifier
            if method_id is None:
                raise ValueError("Can't find a valid identifier for the payment"
                                 " method interface: %r. It is not possible add"
                                 " the payment on the coupon" % method_iface)
            self.printer.add_payment(CUSTOM_PM, payment.base_value,
                                     custom_pm=pm_constants.get_value(method_id))
        return True

    def close(self):
        try:
            coo = self.printer.close()
        except DriverError, details:
            warning(_("It's not possible to close the coupon"), str(details))
            return False
        self.sale.coupon_id = coo
        return True
