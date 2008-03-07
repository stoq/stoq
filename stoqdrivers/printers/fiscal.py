# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin     <jdahlin@async.com.br>
##              Henrique Romano  <henrique@async.com.br>
##

import datetime
from decimal import Decimal

from kiwi.argcheck import number, percent
from kiwi.log import Logger

from stoqdrivers.exceptions import (CloseCouponError, PaymentAdditionError,
                                    AlreadyTotalized, InvalidValue)
from stoqdrivers.enum import PaymentMethodType, TaxType, UnitType
from stoqdrivers.printers.base import BasePrinter
from stoqdrivers.printers.capabilities import capcheck
from stoqdrivers.utils import encode_text
from stoqdrivers.translation import stoqdrivers_gettext

_ = lambda msg: stoqdrivers_gettext(msg)

log = Logger('stoqdrivers.fiscalprinter')

#
# Extra data types to argcheck
#

class taxcode(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (TaxType.NONE, TaxType.ICMS, TaxType.SUBSTITUTION,
                         TaxType.EXEMPTION):
            raise ValueError("%s must be one of TaxType.* constants" % name)

class unit(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (UnitType.WEIGHT, UnitType.METERS, UnitType.LITERS,
                         UnitType.EMPTY, UnitType.CUSTOM):
            raise ValueError("%s must be one of UNIT_* constants" % name)

class payment_method(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (PaymentMethodType.MONEY, PaymentMethodType.CHECK,
                         PaymentMethodType.CUSTOM):
            raise ValueError("%s must be one of *_PM constants" % name)

#
# FiscalPrinter interface
#

class FiscalPrinter(BasePrinter):
    def __init__(self, brand=None, model=None, device=None, config_file=None,
                 *args, **kwargs):
        BasePrinter.__init__(self, brand, model, device, config_file, *args,
                             **kwargs)
        self._has_been_totalized = False
        self.payments_total_value = Decimal("0.0")
        self.totalized_value = Decimal("0.0")
        self._capabilities = self._driver.get_capabilities()
        self._charset = self._driver.coupon_printer_charset

    def get_capabilities(self):
        return self._capabilities

    def _format_text(self, text):
        return encode_text(text, self._charset)

    @capcheck(basestring, basestring, basestring)
    def identify_customer(self, customer_name, customer_address, customer_id):
        log.info('identify_customer(customer_name=%r, '
                  'customer_address=%r, customer_id=%r)' % (
            customer_name, customer_address, customer_id))

        self._driver.coupon_identify_customer(
            self._format_text(customer_name),
            self._format_text(customer_address),
            self._format_text(customer_id))

    def coupon_is_customer_identified(self):
        return self._driver.coupon_is_customer_identified()

    def open(self):
        log.info('coupon_open()')

        return self._driver.coupon_open()

    @capcheck(basestring, basestring, Decimal, str, Decimal, unit,
              Decimal, Decimal, basestring)
    def add_item(self, item_code, item_description, item_price, taxcode,
                 items_quantity=Decimal("1.0"), unit=UnitType.EMPTY,
                 discount=Decimal("0.0"), surcharge=Decimal("0.0"),
                 unit_desc=""):
        log.info("add_item(code=%r, description=%r, price=%r, "
                 "taxcode=%r, quantity=%r, unit=%r, discount=%r, "
                 "surcharge=%r, unit_desc=%r)" % (
            item_code, item_description, item_price, taxcode,
            items_quantity, unit, discount, surcharge, unit_desc))

        if self._has_been_totalized:
            raise AlreadyTotalized("the coupon is already totalized, you "
                                   "can't add more items")
        if discount and surcharge:
            raise TypeError("discount and surcharge can not be used together")
        elif unit != UnitType.CUSTOM and unit_desc:
            raise ValueError("You can't specify the unit description if "
                             "you aren't using UnitType.CUSTOM constant.")
        elif unit == UnitType.CUSTOM and not unit_desc:
            raise ValueError("You must specify the unit description when "
                             "using UnitType.CUSTOM constant.")
        elif unit == UnitType.CUSTOM and len(unit_desc) != 2:
            raise ValueError("unit description must be 2-byte sized string")
        if not item_price:
            raise InvalidValue("The item value must be greater than zero")

        return self._driver.coupon_add_item(
            self._format_text(item_code), self._format_text(item_description),
            item_price, taxcode, items_quantity, unit, discount, surcharge,
            unit_desc=self._format_text(unit_desc))

    @capcheck(percent, percent, taxcode)
    def totalize(self, discount=Decimal("0.0"), surcharge=Decimal("0.0"),
                 taxcode=TaxType.NONE):
        log.info('totalize(discount=%r, surcharge=%r, taxcode=%r)' % (
            discount, surcharge, taxcode))

        if discount and surcharge:
            raise TypeError("discount and surcharge can not be used together")
        if surcharge and taxcode == TaxType.NONE:
            raise ValueError("to specify a surcharge you need specify its "
                             "tax code")
        result = self._driver.coupon_totalize(discount, surcharge, taxcode)
        self._has_been_totalized = True
        self.totalized_value = result
        return result

    @capcheck(basestring, Decimal, basestring)
    def add_payment(self, payment_method, payment_value, description=''):
        log.info("add_payment(method=%r, value=%r, description=%r)" % (
            payment_method, payment_value, description))

        if not self._has_been_totalized:
            raise PaymentAdditionError(_("You must totalize the coupon "
                                         "before add payments."))
        result = self._driver.coupon_add_payment(
            payment_method, payment_value,
            self._format_text(description))
        self.payments_total_value += payment_value
        return result

    def cancel(self):
        log.info('coupon_cancel()')
        retval = self._driver.coupon_cancel()
        self._has_been_totalized = False
        self.payments_total_value = Decimal("0.0")
        self.totalized_value = Decimal("0.0")
        return retval

    def cancel_last_coupon(self):
        """Cancel the last non fiscal coupon or the last sale."""
        self._driver.cancel_last_coupon()

    @capcheck(int)
    def cancel_item(self, item_id):
        log.info('coupon_cancel_item(item_id=%r)' % (item_id,))

        return self._driver.coupon_cancel_item(item_id)

    @capcheck(basestring)
    def close(self, promotional_message=''):
        log.info('coupon_close(promotional_message=%r)' % (
            promotional_message))

        if not self._has_been_totalized:
            raise CloseCouponError(_("You must totalize the coupon before "
                                     "closing it"))
        if not self.payments_total_value:
            raise CloseCouponError(_("It is not possible close the coupon "
                                     "since there are no payments defined."))
        if self.totalized_value > self.payments_total_value:
            raise CloseCouponError(_("Isn't possible close the coupon since "
                                     "the payments total (%.2f) doesn't "
                                     "match the totalized value (%.2f).")
                                   % (self.payments_total_value,
                                      self.totalized_value))
        res = self._driver.coupon_close(
            self._format_text(promotional_message))
        self._has_been_totalized = False
        self.payments_total_value = Decimal("0.0")
        self.totalized_value = Decimal("0.0")
        return res

    def summarize(self):
        log.info('summarize()')

        return self._driver.summarize()

    def close_till(self, previous_day=False):
        log.info('close_till(previous_day=%r)' % (previous_day,))

        return self._driver.close_till(previous_day)

    @capcheck(Decimal)
    def till_add_cash(self, add_cash_value):
        log.info('till_add_cash(add_cash_value=%r)' % (add_cash_value,))

        return self._driver.till_add_cash(add_cash_value)

    @capcheck(Decimal)
    def till_remove_cash(self, remove_cash_value):
        log.info('till_remove_cash(remove_cash_value=%r)' % (
            remove_cash_value,))

        return self._driver.till_remove_cash(remove_cash_value)

    @capcheck(datetime.date, datetime.date)
    def till_read_memory(self, start, end):
        assert start <= end <= datetime.date.today(), (
            "start must be less then end and both must be less today")
        log.info('till_read_memory(start=%r, end=%r)' % (
            start, end))

        return self._driver.till_read_memory(start, end)

    @capcheck(int, int)
    def till_read_memory_by_reductions(self, start, end):
        assert end >= start > 0, ("start must be less then end "
                                  "and both must be positive")
        log.info('till_read_memory_by_reductions(start=%r, end=%r)' % (
            start, end))

        self._driver.till_read_memory_by_reductions(start, end)

    def get_serial(self):
        log.info('get_serial()')

        return self._driver.get_serial()

    def query_status(self):
        log.info('query_status()')

        return self._driver.query_status()

    def status_reply_complete(self, reply):
        log.info('status_reply_complete(%s)' % (reply,))
        return self._driver.status_reply_complete(reply)

    def get_tax_constants(self):
        log.info('get_tax_constants()')

        return self._driver.get_tax_constants()

    def get_payment_constants(self):
        log.info('get_payment_constants()')

        return self._driver.get_payment_constants()

    def get_sintegra(self):
        log.info('get_sintegra()')

        return self._driver.get_sintegra()
