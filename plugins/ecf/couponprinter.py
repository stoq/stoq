# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
"""FiscalPrinting (ECF) integration."""

from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.log import Logger
from zope.interface import implements
from stoqdrivers.enum import TaxType, UnitType
from stoqdrivers.exceptions import (DriverError, CouponNotOpenError,
                                    CancelItemError)

from stoqlib.database.runtime import new_transaction
from stoqlib.database.orm import const
from stoqlib.domain.devices import FiscalDayHistory, FiscalDayTax
from stoqlib.domain.interfaces import IContainer
from stoqlib.exceptions import DeviceError
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

    def has_open_coupon(self):
        return self._driver.has_open_coupon()

    def open_till(self):
        """
        Opens the till
        """
        log.info("Opening till")

        self._register_emitted_document(ECFDocumentHistory.TYPE_SUMMARY)
        self._driver.summarize()

    def has_pending_reduce(self):
        return self._driver.has_pending_reduce()

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
        except DriverError, details:
            warning(_("Could not cancel coupon"),
                str(details))
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
        try:
            self._register_emitted_document(
                                        ECFDocumentHistory.TYPE_MEMORY_READ)
            self._driver.till_read_memory(start_date, end_date)
        except DriverError, details:
            warning(_("Could not read memory"),
                str(details))

    def memory_by_reductions(self, start, end):
        try:
            self._register_emitted_document(
                                        ECFDocumentHistory.TYPE_MEMORY_READ)
            self._driver.till_read_memory_by_reductions(start, end)
        except DriverError, details:
            warning(_("Could not read memory"),
                str(details))

    def create_coupon(self, coupon):
        return Coupon(coupon, self._printer, self._driver)

    def check_serial(self):
        driver_serial = self._driver.get_serial()
        if self._printer.device_serial != driver_serial:
            warning(_("Invalid serial number for fiscal printer connected to %s") % (
                self._printer.device_name))
            return False

        return True

    def print_report(self, report):
        self._driver.gerencial_report_open()
        self._driver.gerencial_report_print(report)
        self._driver.gerencial_report_close()

    # Private
    def _register_emitted_document(self, type):
        """Register an emitted document.
        """
        # We are registering this before the actual emission, so, coo and crz are -1 offset.
        # gnf though is already the correct value.
        coo = self._driver.get_coo() + 1
        gnf = self._driver.get_gnf()
        crz = None
        if type == ECFDocumentHistory.TYPE_Z_REDUCTION:
            crz = self._driver.get_crz() + 1

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
                               reduction_date=const.NOW(),
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
    Sellable object. Currently, services can't be added, and they
    are just ignored -- be aware, if a coupon with only services is
    emitted, it will not be opened in fact, but just ignored.
    """
    implements(IContainer)

    def __init__(self, coupon, printer, driver):
        self._coupon = coupon
        self._printer = printer
        self._driver = driver
        self._item_ids = {}

        self._customer_document = None
        self._customer_document_type = None

    def _get_capability(self, name):
        return self._driver.get_capabilities()[name]

    #
    # IContainer implementation
    #

    def add_item(self, item):
        """
        @param item: A L{SellableItem} subclass
        @returns: id of the item.:
          0 >= if it was added successfully
          -1 if an error happend
          0 if added but not printed (gift certificates, free deliveries)
        """
        sellable = item.sellable
        max_len = self._get_capability("item_description").max_len
        description = sellable.description[:max_len]
        unit_desc = ''
        if not sellable.unit:
            unit = UnitType.EMPTY
        else:
            if sellable.unit.unit_index == UnitType.CUSTOM:
                unit_desc = sellable.unit.description
            unit = sellable.unit.unit_index or UnitType.EMPTY
        max_len = self._get_capability("item_code").max_len
        code = sellable.code[:max_len]

        try:
            tax_constant = self._printer.get_tax_constant_for_device(sellable)
        except DeviceError, e:
            warning(_("Could not print item"), str(e))
            return -1

        try:
            return self._driver.add_item(code, description, item.price,
                                         tax_constant.device_value,
                                         item.quantity, unit,
                                         unit_desc=unit_desc)
        except DriverError, e:
            warning(_("Could not print item"), str(e))
            return -1

    @argcheck(int)
    def remove_item(self, item_id):
        self._driver.cancel_item(item_id)

    #
    # Fiscal coupon related functions
    #

    def identify_customer(self, name, address, document, document_type):
        max_id = self._get_capability("customer_id").max_len
        max_name = self._get_capability("customer_name").max_len
        max_addr = self._get_capability("customer_address").max_len

        self._customer_document = document
        self._customer_document_type = document_type

        self._driver.identify_customer(name[:max_name], address[:max_addr],
                                       document[:max_id])

    def is_customer_identified(self):
        return self._driver.coupon_is_customer_identified()

    def open(self):
        return self._driver.open()

    def totalize(self, sale):
        return self._driver.totalize(sale.discount_value,
                                     Decimal('0'),
                                     TaxType.NONE)

    def cancel(self):
        return self._driver.cancel()

    def _get_payment_method_constant(self, payment):
        constant = self._printer.get_payment_constant(payment)
        if not constant:
            raise DeviceError(
                _("The payment method used in this sale (%s) is not "
                  "configured in the fiscal printer.") % (payment.method.method_name, ))

        return constant

    def add_payments(self, sale):
        """ Add the payments defined in the sale to the coupon. Note that this
        function must be called after all the payments has been created.
        """
        log.info("setting up payments for %r" % (sale, ))

        log.info("we have %d payments" % (sale.payments.count()), )

        card_payments = {}
        # Merge card payments by nsu
        for payment in sale.payments:
            if payment.method.method_name != 'card':
                continue
            operation = payment.method.operation
            card_data = operation.get_card_data_by_payment(payment)
            card_payments.setdefault(card_data.nsu, 0)
            card_payments[card_data.nsu] += payment.value

        for payment in sale.payments:
            constant = self._get_payment_method_constant(payment)

            # When adding a money payment, use base_value so that the payback
            # is show correctly.
            if payment.method.method_name == 'money':
                self._driver.add_payment(constant.device_value,
                                         payment.base_value)

            # Card payments were merged above. Use that instead.
            elif payment.method.method_name == 'card':
                operation = payment.method.operation
                card_data = operation.get_card_data_by_payment(payment)
                # This payment was already addded
                if not card_data.nsu in card_payments:
                    continue
                self._driver.add_payment(constant.device_value,
                                         card_payments[card_data.nsu])
                del card_payments[card_data.nsu]
            # In other cases, add the real value of payment.
            else:
                self._driver.add_payment(constant.device_value,
                                         payment.value)

        return True

    def close(self, sale):
        self._create_fiscal_sale_data(sale)
        coupon_id = self._driver.close()
        return coupon_id

    def _create_fiscal_sale_data(self, sale):
        trans = sale.get_connection()
        FiscalSaleHistory(sale=sale,
                          document_type=self._customer_document_type,
                          document=self._customer_document,
                          coo=self.get_coo(),
                          document_counter=self.get_ccf(),
                          connection=trans)

    def get_ccf(self):
        return self._driver.get_ccf()

    def get_coo(self):
        return self._driver.get_coo()

    @property
    def supports_duplicate_receipt(self):
        return self._driver.supports_duplicate_receipt

    @property
    def identify_customer_at_end(self):
        return self._driver.identify_customer_at_end

    def print_payment_receipt(self, coo, payment, value, receipt):
        """Print a payment receipt for a payment in a coupon

        @param coo: the coo for the coupon
        @param payment:
        @param receipt: the text to be printed
        """
        constant = self._get_payment_method_constant(payment)
        receipt_id = self._driver.get_payment_receipt_identifier(constant.constant_name)

        self._driver.payment_receipt_open(receipt_id, coo, constant.device_value,
                                          value)
        self._driver.payment_receipt_print(receipt)
        self._driver.payment_receipt_close()

        # Right now, we are printing the two receipts at once
        #if self.supports_duplicate_receipt:
        #    self._driver.payment_receipt_print_duplicate()
