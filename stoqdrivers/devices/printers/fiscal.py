# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Fiscal Printer
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
## Author(s):   Johan Dahlin     <jdahlin@async.com.br>
##              Henrique Romano  <henrique@async.com.br>
##

from kiwi.argcheck import argcheck, number, percent

from stoqdrivers.exceptions import (CloseCouponError, PaymentAdditionError,
                                    PendingReadX, PendingReduceZ,
                                    CouponOpenError)
from stoqdrivers.constants import (TAX_NONE,TAX_IOF, TAX_ICMS, TAX_SUBSTITUTION,
                                   TAX_EXEMPTION, UNIT_EMPTY, UNIT_LITERS,
                                   UNIT_WEIGHT, UNIT_METERS, MONEY_PM, CHEQUE_PM)
from stoqdrivers.devices.printers.base import BasePrinter

#
# Extra data types to argcheck
#

class taxcode(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (TAX_NONE, TAX_IOF, TAX_ICMS, TAX_SUBSTITUTION,
                         TAX_EXEMPTION):
            raise ValueError("%s must be one of TAX_* constants" % name)

class unit(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (UNIT_WEIGHT, UNIT_METERS, UNIT_LITERS,
                         UNIT_EMPTY):
            raise ValueError("%s must be one of UNIT_* constants" % name)

class payment_method(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (MONEY_PM, CHEQUE_PM):
            raise ValueError("%s must be one of *_PM constants" % name)

#
# FiscalPrinter interface
#

class FiscalPrinter(BasePrinter):
    log_domain = 'fp'
    def __init__(self, config_file=None):
        BasePrinter.__init__(self, config_file)
        self.has_been_totalized = False

    @argcheck(str, str, str)
    def open(self, customer, address, document):
        self.info('coupon_open')
        return self._driver.coupon_open(customer, address, document)

    @argcheck(str, number, number, unit, str, taxcode, percent, percent)
    def add_item(self, code, quantity, price, unit, description,
                 taxcode, discount, charge):
        if discount and charge:
            raise TypeError("discount and charge can not be used together")

        self.info('coupon_add_item')
        return self._driver.coupon_add_item(code, quantity, price,
                                            unit, description,
                                            taxcode, discount, charge)
    @argcheck(percent, percent, taxcode)
    def totalize(self, discount, charge, taxcode):
        if discount and charge:
            raise TypeError("discount and charge can not be used together")

        self.info('coupon_totalize')
        result = self._driver.coupon_totalize(discount, charge, taxcode)
        self.has_been_totalized = True
        return result

    @argcheck(payment_method, float, str)
    def add_payment(self, payment_method, value, description=''):
        self.info('coupon_add_payment')
        if not self.has_been_totalized:
            raise PaymentAdditionError("You must totalize the coupon "
                                       "before add payments.")
        result = self._driver.coupon_add_payment(payment_method, value,
                                                 description)
        return result
        
    def cancel(self):
        self.info('coupon_cancel')
        return self._driver.coupon_cancel()

    def cancel_item(self, item_id):
        self.info('coupon_cancel_item')
        return self._driver.coupon_cancel_item(item_id)

    @argcheck(str)
    def close(self, message=''):
        self.info('coupon_close')
        if not self.has_been_totalized:
            raise CloseCouponError("You must totalize the coupon before close "
                                   "it.")
        return self._driver.coupon_close(message)

    def summarize(self):
        self.info('summarize')
        return self._driver.summarize()

    def close_till(self):
        self.info('close_till')
        return self._driver.close_till()

    def get_status(self):
        self.info('get_status')
        return self._driver.get_status()

def test():
    p = FiscalPrinter()

    while True:
        try:
            p.open('Zee germans', 'Home', 'yaya')
            break
        except CouponOpenError:
            p.cancel()
        except PendingReadX:
            p.summarize()
            return
        except PendingReduceZ:
            p.close_till()
            return

    i1 = p.add_item("foo", 1, 10.00, UNIT_EMPTY, "description", TAX_NONE, 0, 0)
    i2 = p.add_item("HK001", 5, 1.53, UNIT_LITERS, "Bohemia Beer", TAX_NONE,
                    0, 0)
    p.cancel_item(i1)

    coupon_total = p.totalize(0.0, 0, TAX_NONE)

    p.add_payment(MONEY_PM, 5.00, '')
    p.add_payment(MONEY_PM, 2.00, '')
    p.add_payment(MONEY_PM, 1.00, '')

    p.close()

if __name__ == '__main__':
    test()
