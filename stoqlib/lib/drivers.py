# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##              Johan Dahlin            <jdahlin@async.com.br>
##
""" Useful functions for StoqDrivers interaction """

from decimal import Decimal

import gtk
from kiwi.argcheck import argcheck
from kiwi.log import Logger
from zope.interface import implements
from stoqdrivers.devices.printers.cheque import ChequePrinter
from stoqdrivers.devices.scales.scales import Scale
from stoqdrivers.constants import (UNIT_EMPTY, UNIT_CUSTOM, TAX_NONE,
                                   MONEY_PM, CHEQUE_PM, CUSTOM_PM)
from stoqdrivers.exceptions import (CouponOpenError, DriverError,
                                    OutofPaperError, PrinterOfflineError,
                                    CouponNotOpenError)

from stoqlib.database.database import finish_transaction
from stoqlib.database.runtime import (new_transaction, get_current_branch,
                                      get_current_station)
from stoqlib.domain.devices import DeviceSettings
from stoqlib.domain.giftcertificate import GiftCertificateItem
from stoqlib.domain.interfaces import (IIndividual, ICompany, IPaymentGroup,
                                       IContainer)
from stoqlib.domain.payment.methods import CheckPM, MoneyPM
from stoqlib.domain.sale import Sale
from stoqlib.domain.service import ServiceSellableItem
from stoqlib.domain.sellable import ASellableItem
from stoqlib.domain.till import Till
from stoqlib.exceptions import TillError
from stoqlib.lib.defaults import (METHOD_GIFT_CERTIFICATE, get_all_methods_dict,
                                  get_method_names)
from stoqlib.lib.message import warning, info, yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import run_dialog

_ = stoqlib_gettext
_printer = None
_scale = None
log = Logger("stoqlib.drivers")

#
# Private
#

def _get_fiscalprinter(conn):
    """ Returns a FiscalPrinter instance pre-configured to the current
    workstation.
    """
    global _printer
    if _printer:
        return _printer
    station = get_current_station(conn)
    setting = get_fiscal_printer_settings_by_station(conn, station)
    if setting and setting.is_active:
        _printer = setting.get_interface()
    else:
        warning(_(u"There is no fiscal printer"),
               _(u"There is no fiscal printer configured for this "
                "station (\"%s\") or the printer is not enabled "
                "currently." % station.name))

    return _printer

def _get_scale(conn):
    """ Returns a Scale instance pre-configured for the current
    workstation.
    """
    global _scale
    if _scale:
        return _scale
    station = get_current_station(conn)
    setting = get_scale_settings_by_station(conn, station)
    if setting and setting.is_active:
        _scale = Scale(brand=setting.brand,
                       model=setting.model,
                       device=setting.get_port_name())
    else:
        warning(_(u"There is no scale configured"),
               _(u"There is no scale configured for this station "
                "(\"%s\") or the scale is not enabled currently"
                 % station.name))
    return _scale

#
# Public API
#


def get_device_settings_by_station(conn, station, device_type):
    return DeviceSettings.selectOneBy(station=station, type=device_type,
                                      connection=conn)

def get_fiscal_printer_settings_by_station(conn, station):
    """ Returns the DeviceSettings object representing the printer currently
    associated with the given station or None if there is not settings for
    it.
    """
    return get_device_settings_by_station(conn, station,
                                          DeviceSettings.FISCAL_PRINTER_DEVICE)

def get_current_cheque_printer_settings(conn):
    res = get_device_settings_by_station(conn, get_current_station(conn),
                                         DeviceSettings.CHEQUE_PRINTER_DEVICE)
    if not res:
        return None
    elif not isinstance(res, DeviceSettings):
        raise TypeError("Invalid setting returned by "
                        "get_current_cheque_printer_settings")
    return ChequePrinter(brand=res.brand,
                         model=res.model,
                         device=res.get_port_name())

def get_scale_settings_by_station(conn, station):
    """ Return the DeviceSettings object representing the scale currently
    associated with the given station or None if there is no settings for
    it.
    """
    return get_device_settings_by_station(conn, station,
                                          DeviceSettings.SCALE_DEVICE)

def get_current_scale_settings(conn):
    return get_scale_settings_by_station(conn, get_current_station(conn))

def create_virtual_printer_for_current_station():
    trans = new_transaction()
    station = get_current_station(trans)
    if get_fiscal_printer_settings_by_station(trans, station):
        trans.close()
        return
    settings = DeviceSettings(station=station,
                              device=DeviceSettings.DEVICE_SERIAL1,
                              brand='virtual',
                              model='Simple',
                              type=DeviceSettings.FISCAL_PRINTER_DEVICE,
                              connection=trans)
    settings.create_fiscal_printer_constants()
    trans.commit(close=True)

def check_virtual_printer_for_current_station(conn):
    """Returns True if the fiscal printer for the current station is
    a virtual one.
    """
    printer = _get_fiscalprinter(conn)
    if not printer:
        raise ValueError("There should be a fiscal printer defined "
                         "at this point")
    return printer.brand == 'virtual'

#
# Coupon & Cheque
#

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
    current_branch = get_current_branch(conn)
    main_address = current_branch.person.get_main_address()
    if not main_address:
        raise ValueError("The cheque can not be printed since there is no "
                         "main address defined for the current branch.")

    max_len = get_capability(printer, "cheque_city")
    city = main_address.city_location.city[:max_len]
    for idx, payment in enumerate(payments):
        method = payment.method
        if not isinstance(method, CheckPM):
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


class CouponPrinter(object):
    """
    CouponPrinter is a wrapper around the FiscalPrinter class inside
    stoqdrivers, refer to it for documentation
    """
    def __init__(self, conn):
        self.conn = conn
        self._printer = _get_fiscalprinter(conn)

    def _emit_reading(self, cmd):
        try:
            getattr(self._printer, cmd)()
        except CouponOpenError:
            return self._printer.cancel()
        except DriverError:
            return False
        return True

    def open_till(self, parent=None):
        """
        Opens the till
        @param parent: a gtk.Window subclass or None
        """
        log.info("Opening till")

        if Till.get_current(self.conn) is not None:
            warning("You already have a till operation opened. "
                    "Close the current Till and open another one.")
            return False

        from stoqlib.gui.editors.tilleditor import TillOpeningEditor
        trans = new_transaction()
        try:
            model = run_dialog(TillOpeningEditor, parent, trans)
        except TillError, e:
            warning(e)
            model = None

        retval = True
        while not self._emit_reading('summarize'):
            response = warning(
                _(u"It's not possible to emit a read X for the "
                      "configured printer.\nWould you like to ignore "
                      "this error and continue?"),
                buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                         (_(u"Ignore"), gtk.RESPONSE_YES),
                         (_(u"Try Again"), gtk.RESPONSE_NONE)))
            if response == gtk.RESPONSE_YES:
                retval = True
                break
            elif response == gtk.RESPONSE_CANCEL:
                retval = False
                break

        if retval:
            if model and model.value > 0:
                self.add_cash(model.value)

            if not finish_transaction(trans, model):
                retval = False

        trans.close()

        return retval

    def close_till(self, parent=None):
        """
        Closes the till
        @param parent: a gtk.Window subclass or None
        @returns: True if the till was closed, otherwise False
        """
        log.info("Closing till")

        till = Till.get_last_opened(self.conn)
        assert till

        from stoqlib.gui.editors.tilleditor import TillClosingEditor
        trans = new_transaction()
        model = run_dialog(TillClosingEditor, parent, trans)

        if not model:
            finish_transaction(trans, model)
            return

        opened_sales = Sale.selectBy(status=Sale.STATUS_OPENED,
                                     connection=trans)
        if opened_sales:
            # A new till object to "store" the sales that weren't
            # confirmed. Note that this new till operation isn't
            # opened yet, but it will be considered when opening a
            # new operation
            branch_station = opened_sales[0].till.station
            new_till = Till(connection=trans,
                            station=branch_station)
            for sale in opened_sales:
                sale.till = new_till

        if model.value > 0:
            # If we forgot to close the till and want to do a remove cash
            # we must emit a Read X before removing cash
            if till.needs_closing():
                self._emit_reading('summarize')
            self.remove_cash(model.value)

        retval = True
        while not self._emit_reading('close_till'):
            response = warning(
                short=_(u"It's not possible to emit a reduce Z for the "
                        "configured printer.\nWould you like to ignore "
                        "this error and continue?"),
                buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                         (_(u"Ignore"), gtk.RESPONSE_YES),
                         (_(u"Try Again"), gtk.RESPONSE_NONE)))
            if response  == gtk.RESPONSE_YES:
                retval = True
                break
            elif response == gtk.RESPONSE_CANCEL:
                retval = False

        if retval:
            # TillClosingEditor closes the till
            if not finish_transaction(trans, model):
                retval = False

        trans.close()

        return retval

    def cancel(self):
        """
        Cancel the current or the last made sale.
        @return: True it was canceled, False if there was nothing to cancel
        """
        # FIXME: We need to ask the fiscal printer which was the last
        #        made sale and cancel the sale with /that/ coupon number
        #        That requires each sale to have a reference to a coupon.
        #        See #3130 for more information

        try:
            self._printer.cancel()
        except CouponNotOpenError:
            return False

        trans = new_transaction()

        sale = Sale.get_last_confirmed(trans)
        if not sale:
            return False
        sale.cancel(sale.create_sale_return_adapter())

        trans.commit(close=True)

        return True

    def add_cash(self, value):
        self._printer.till_add_cash(value)

    def remove_cash(self, value):
        self._printer.till_remove_cash(value)

    def emit_coupon(self, sale):
        """ Emit a coupon for a Sale instance.

        @returns: True if the coupon has been emitted, False otherwise.
        """
        if not self._printer:
            raise ValueError("It is not possible to emit coupon "
                             "since there is no fiscal printer "
                             "configured for this station")

        products = sale.get_products()
        if not products:
            return True

        settings = get_fiscal_printer_settings_by_station(
            self.conn, get_current_station(self.conn))

        coupon = _FiscalCoupon(self._printer, sale, settings)
        if sale.client:
            coupon.identify_customer(sale.client.person)
        if not coupon.open():
            return False
        for product in products:
            coupon.add_item(product)
        if not coupon.totalize():
            return False
        if not coupon.setup_payments():
            return False
        return coupon.close()


#
# Class definitions
#


class _FiscalCoupon:
    """ This class is used just to allow us cancel an item with base in a
    ASellable object. Currently, services can't be added, and they
    are just ignored -- be aware, if a coupon with only services is
    emitted, it will not be opened in fact, but just ignored.
    """
    implements(IContainer)

    def __init__(self, printer, sale, settings):
        self.printer = printer
        self.sale = sale
        self.settings = settings
        self._item_ids = {}

    #
    # IContainer implementation
    #

    @argcheck(ASellableItem)
    def add_item(self, item):
        # Do not add services to the coupon
        if isinstance(item, ServiceSellableItem):
            log.info("item %r couldn't added to the coupon, "
                     "since it is a service" % item)
            return
        # GiftCertificates are not printed on the fiscal printer
        # See #2985 for more information.
        elif isinstance(item, GiftCertificateItem):
            return

        sellable = item.sellable
        max_len = get_capability(self.printer, "item_description")
        description = sellable.base_sellable_info.description[:max_len]
        unit_desc = ''
        if not sellable.unit:
            unit = UNIT_EMPTY
        else:
            if sellable.unit.unit_index == UNIT_CUSTOM:
                unit_desc = sellable.unit.description
            unit = sellable.unit.unit_index or UNIT_EMPTY
        max_len = get_capability(self.printer, "item_code")
        code = sellable.get_code_str()[:max_len]
        constant = self._settings.get_tax_constant_for_device(sellable)
        item_id = self.printer.add_item(code, description, item.price,
                                        constant.device_value,
                                        item.quantity, unit,
                                        unit_desc=unit_desc)
        ids = self._item_ids.setdefault(item, [])
        ids.append(item_id)

    def get_items(self):
        return self._item_ids.keys()

    @argcheck(ASellableItem)
    def remove_item(self, item):
        # Services are not added, so don't try to remove them
        if isinstance(item, ServiceSellableItem):
            return
        for item_id in self._item_ids.pop(item):
            try:
                self.printer.cancel_item(item_id)
            except DriverError:
                return False
        return True

    #
    # Fiscal coupon related functions
    #

    def identify_customer(self, person):
        max_len = get_capability(self.printer, "customer_id")
        if IIndividual(person):
            individual = IIndividual(person)
            document = individual.cpf[:max_len]
        elif ICompany(person):
            company = ICompany(person)
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
                if not yesno(
                    _(u"The printer %s has run out of paper.\nAdd more paper "
                      "before continuing.") % self.printer.get_printer_name(),
                    gtk.RESPONSE_YES, _(u"Resume"), _(u"Confirm later")):
                    return False
                return self.open()
            except PrinterOfflineError:
                if not yesno(
                    (_(u"The printer %s is offline, turn it on and try"
                       "again") % self.printer.get_model_name()),
                    gtk.RESPONSE_YES, _(u"Resume"), _(u"Confirm later")):
                    return False
                return self.open()
            except DriverError, details:
                warning(_(u"It is not possible to emit the coupon"),
                        str(details))
                return False
        return True

    def totalize(self):
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True

        # Surcharge is currently disabled, see #2811
        #if discount > surcharge:
        #    discount = discount - surcharge
        #    surcharge = 0
        #elif surcharge > discount:
        #    surcharge = surcharge - discount
        #    discount = 0
        #else:
        #    # If these values are greater than zero we will get problems in
        #    # stoqdrivers
        #    surcharge = discount = 0
        surcharge = Decimal('0')

        discount = self.sale.discount_percentage

        try:
            self.printer.totalize(discount, surcharge, TAX_NONE)
        except DriverError, details:
            warning(_(u"It is not possible to totalize the coupon"),
                    str(details))
            return False
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
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True
        sale = self.sale
        group = IPaymentGroup(sale)
        if group.default_method == METHOD_GIFT_CERTIFICATE:
            self.printer.add_payment(MONEY_PM, sale.get_total_sale_amount())
            return True

        all_methods = get_all_methods_dict().items()
        method_id = None
        for payment in group.get_items():
            method = payment.method
            if isinstance(method, (CheckPM, MoneyPM)):
                if isinstance(method, CheckPM):
                    method_id = CHEQUE_PM
                else:
                    method_id = MONEY_PM
                self.printer.add_payment(method_id, payment.base_value)
                continue
            method_type = type(method)
            method_id = None
            for identifier, mtype in all_methods:
                if method_type == mtype:
                    if method_id is not None:
                        raise TypeError(
                            "There is the same identifier for two "
                            "different payment method interfaces. "
                            "The identifier is %d" % method_id)
                    method_id = identifier
            if method_id is None:
                raise ValueError(
                    "Can't find a valid identifier for the payment "
                    "method type: %s. It is not possible add "
                    "the payment on the coupon" %
                    method_type.__name__)

            constant = self._settings.get_payment_constant(method_id)
            if constant:
                self.printer.add_payment(CUSTOM_PM, payment.base_value,
                                         custom_pm=constant.device_value)
            else:
                method_name = get_method_names()[method_id]
                if not yesno(
                    _(u"The payment method used in this sale (%s) is not "
                      "configured in the fiscal printer." % method_name),
                    gtk.RESPONSE_YES, _(u"Use Money as payment method"),
                    _(u"Cancel the checkout")):
                    return False

                self.printer.add_payment(MONEY_PM, payment.base_value)

        for entry in group.get_till_entries():
            self.printer.add_payment(MONEY_PM, entry.value)

        return True

    def close(self):
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True
        try:
            coupon_id = self.printer.close()
        except DriverError, details:
            warning(_("It's not possible to close the coupon"), str(details))
            return False
        self.sale.coupon_id = coupon_id
        return True

