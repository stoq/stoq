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
"""FiscalPrinting (ECF) integration."""

from decimal import Decimal
import datetime

from kiwi.argcheck import argcheck
from kiwi.log import Logger
from zope.interface import implements
from stoqdrivers.enum import TaxType, UnitType
from stoqdrivers.exceptions import (DriverError, CouponNotOpenError,
                                    CancelItemError)

from stoqlib.database.runtime import new_transaction
from stoqlib.domain.devices import FiscalDayHistory, FiscalDayTax
from stoqlib.domain.interfaces import (IIndividual, ICompany, IPaymentGroup,
                                       IContainer)
from stoqlib.exceptions import DeviceError
from stoqlib.lib.defaults import get_all_methods_dict, get_method_names
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

from ecfdomain import FiscalSaleHistory, ECFDocumentHistory

_ = stoqlib_gettext

log = Logger("stoq-ecf-plugin.couponprinter")


class CouponPrinter(object):
    """
    CouponPrinter is a wrapper around the FiscalPrinter class inside
    stoqdrivers, refer to it for documentation
    """
    def __init__(self, printer):
        # This is an ECFPrinter instance
        self._printer = printer
        # and this is a FiscalPrinter instance
        self._driver = printer.get_fiscal_driver()

    #
    # Public API
    #

    def open_till(self):
        """
        Opens the till
        """
        log.info("Opening till")

        self._register_emitted_document(ECFDocumentHistory.TYPE_SUMMARY)
        self._driver.summarize()

    def close_till(self, previous_day=False):
        """
        Closes the till
        @param value: optional, how much to remove from the till
          before closing it
        """
        log.info("Updating sintegra data")
        self._update_sintegra_data()

        log.info("Closing till")
        self._register_emitted_document(ECFDocumentHistory.TYPE_Z_REDUCTION)
        self._driver.close_till(previous_day=previous_day)

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
            self._driver.cancel()
        except CouponNotOpenError:
            return False
        except CancelItemError:
            return False

        return True

    def cancel_last_coupon(self):
        """Cancel the last non-fiscal coupon or sale."""
        self._driver.cancel_last_coupon()

    def add_cash(self, value):
        """
        Remove cash to the till
        @param value: a positive value indicating how much to add
        """
        assert value > 0
        self._driver.till_add_cash(value)

    def remove_cash(self, value):
        """
        Remove cash from the till
        @param value: a positive value indicating how much to remove
        """
        assert value > 0
        self._driver.till_remove_cash(value)

    def summarize(self):
        """sends a summarize (leituraX) command to the printer"""
        try:
            self._register_emitted_document(ECFDocumentHistory.TYPE_SUMMARY)
            self._driver.summarize()
        except DriverError, details:
                    warning(_("Could not print summary"),
                        str(details))

    def memory_by_date(self, start_date, end_date):
        self._register_emitted_document(ECFDocumentHistory.TYPE_MEMORY_READ)
        self._driver.till_read_memory(start_date, end_date)

    def memory_by_reductions(self, start, end):
        self._register_emitted_document(ECFDocumentHistory.TYPE_MEMORY_READ)
        self._driver.till_read_memory_by_reductions(start, end)

    def create_coupon(self, coupon):
        return Coupon(coupon, self._printer, self._driver)

    def check_serial(self):
        driver_serial = self._driver.get_serial()
        if self._printer.device_serial != driver_serial:
            warning(_("Invalid serial number for fiscal printer connected to %s" % (
                self._printer.device_name)))
            return False

        return True

    # Private
    def _register_emitted_document(self, type):
        """Register an emitted document.
        """
        # We are registering this before the actual emission, so, coo and crz are -1 offset.
        # gnf though is already the correct value.
        coo = self._driver.get_coo()+1
        gnf = self._driver.get_gnf()
        crz = None
        if type == ECFDocumentHistory.TYPE_Z_REDUCTION:
            crz = self._driver.get_crz()+1

        trans = new_transaction()
        doc = ECFDocumentHistory(connection=trans,
                              printer=self._printer,
                              type=type,
                              coo=coo,
                              gnf=gnf,
                              crz=crz)

        trans.commit(close=True)
        return doc

    def _update_sintegra_data(self):
        data = self._driver.get_sintegra()
        if data is None:
            return

        trans = new_transaction()
        # coupon_start and coupon_end are actually, start coo, and current coo.
        coupon_start = data.coupon_start
        coupon_end = data.coupon_end
        # 0 means that the start coo isn't known, fetch
        # the current coo from the the database and add 1
        # TODO: try to avoid this hack
        if coupon_start == 0:
            results = FiscalDayHistory.selectBy(
                station=self._printer.station,
                connection=trans).orderBy('-emission_date')
            if results.count():
                coupon_start = results[0].coupon_end + 1
            else:
                coupon_start = 1

        # Something went wrong or no coupons opened during the day
        if coupon_end <= coupon_start:
            trans.commit(close=True)
            return

        day = FiscalDayHistory(connection=trans,
                               emission_date=data.opening_date,
                               station=self._printer.station,
                               serial=data.serial,
                               # 1 -> 001, FIXME: should fix stoqdrivers
                               serial_id=int(data.serial_id),
                               coupon_start=coupon_start,
                               coupon_end=coupon_end,
                               crz=data.crz,
                               cro=data.cro,
                               reduction_date=datetime.datetime.today(),
                               period_total=data.period_total,
                               total=data.total)

        for code, value, type in data.taxes:
            FiscalDayTax(fiscal_day_history=day,
                         code=code, value=value,
                         type=type, connection=trans)
        trans.commit(close=True)

    def get_printer(self):
        return self._printer

    def get_driver(self):
        return self._driver


#
# Class definitions
#


class Coupon(object):
    """ This class is used just to allow us cancel an item with base in a
    ASellable object. Currently, services can't be added, and they
    are just ignored -- be aware, if a coupon with only services is
    emitted, it will not be opened in fact, but just ignored.
    """
    implements(IContainer)

    def __init__(self, coupon, printer, driver):
        self._coupon = coupon
        self._printer = printer
        self._driver = driver
        self._item_ids = {}

    def _get_capability(self, name):
        return self._driver.get_capabilities()[name]

    #
    # IContainer implementation
    #

    def add_item(self, item):
        """
        @param item: A L{ASellableItem} subclass
        @returns: id of the item.:
          0 >= if it was added successfully
          -1 if an error happend
          0 if added but not printed (gift certificates, free deliveries)
        """
        sellable = item.sellable
        max_len = self._get_capability("item_description").max_len
        description = sellable.base_sellable_info.description[:max_len]
        unit_desc = ''
        if not sellable.unit:
            unit = UnitType.EMPTY
        else:
            if sellable.unit.unit_index == UnitType.CUSTOM:
                unit_desc = sellable.unit.description
            unit = sellable.unit.unit_index or UnitType.EMPTY
        max_len = self._get_capability("item_code").max_len
        code = sellable.get_code_str()[:max_len]

        try:
            tax_constant = self._printer.get_tax_constant_for_device(sellable)
        except DeviceError, e:
            warning(_("Could not print item"), str(e))
            return -1
        return self._driver.add_item(code, description, item.price,
                                     tax_constant.device_value,
                                     item.quantity, unit,
                                     unit_desc=unit_desc)

    @argcheck(int)
    def remove_item(self, item_id):
        self._driver.cancel_item(item_id)

    #
    # Fiscal coupon related functions
    #

    def identify_customer(self, person):
        max_len = self._get_capability("customer_id").max_len
        if IIndividual(person, None):
            individual = IIndividual(person)
            document = individual.cpf[:max_len]
        elif ICompany(person, None):
            company = ICompany(person)
            document = company.cnpj[:max_len]
        else:
            raise TypeError(
                "identify_customer needs an object implementing "
                "IIndividual or ICompany")
        max_len = self._get_capability("customer_name").max_len
        name = person.name[:max_len]
        max_len = self._get_capability("customer_address").max_len
        address = person.get_address_string()[:max_len]
        self._driver.identify_customer(name, address, document)

    def is_customer_identified(self):
        return self._driver.coupon_is_customer_identified()

    def open(self):
        return self._driver.open()

    def totalize(self, sale):
        return self._driver.totalize(sale.discount_percentage,
                                     Decimal('0'),
                                     TaxType.NONE)

    def cancel(self):
        return self._driver.cancel()

    def _get_payment_method_constant(self, method_type):
        all_methods = get_all_methods_dict().items()
        method_id = None

        for method_id, mtype in all_methods:
            if mtype == method_type:
                break
        else:
            raise ValueError(
                _("Can't find a valid identifier for the payment "
                  "method type: %s. It is not possible add "
                  "the payment on the coupon") %
                method_type.__name__)

        constant = self._printer.get_payment_constant(method_id)
        if not constant:
            method_name = get_method_names()[method_id]
            raise DeviceError(
                _("The payment method used in this sale (%s) is not "
                  "configured in the fiscal printer." % method_name))

        return constant

    def add_payments(self, sale):
        """ Add the payments defined in the sale to the coupon. Note that this
        function must be called after all the payments has been created.
        """
        log.info("setting up payments for %r" % (sale,))

        group = IPaymentGroup(sale)

        log.info("we have %d payments" % (group.get_items().count()),)
        for payment in group.get_items():
            constant = self._get_payment_method_constant(type(payment.method))
            self._driver.add_payment(constant.device_value,
                                     payment.base_value)

        return True

    def close(self, sale, document, document_type):
        self._create_fiscal_sale_data(sale, document, document_type)
        message = self._get_coupon_message(document)
        coupon_id = self._driver.close(message)
        return coupon_id

    def _get_coupon_message(self, document):
        msg = u""
        # If the customer is already identified, The document will be printed and there is no
        # need to add this message
        if document and not self.is_customer_identified():
            msg += _(u'Customer CPF/CNPJ: ') + document

        return msg

    def _create_fiscal_sale_data(self, sale, document, document_type):
        trans = new_transaction()
        FiscalSaleHistory(sale=sale,
                       document_type=document_type,
                       document=document,
                       coo=self.get_coo(),
                       document_counter=self.get_ccf(),
                       connection=trans)
        trans.commit(close=True)

    def get_ccf(self):
        return self._driver.get_ccf()

    def get_coo(self):
        return self._driver.get_coo()

    def print_payment_receipt(self, coo, payment, receipt):
        """Print a payment receipt for a payment in a coupon

        @param coo: the coo for the coupon
        @param payment:
        @param receipt: the text to be printed
        """
        constant = self._get_payment_method_constant(type(payment.method))
        receipt_id = self._driver.get_payment_receipt_identifier(constant.constant_name)

        self._driver.payment_receipt_open(receipt_id, coo, constant.device_value, payment.value)
        self._driver.payment_receipt_print(receipt)
        self._driver.payment_receipt_close()


