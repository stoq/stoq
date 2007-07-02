#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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

from decimal import Decimal

from stoqdrivers.printers.fiscal import FiscalPrinter
from stoqdrivers.exceptions import (PendingReduceZ,
                                    PendingReadX,
                                    CouponOpenError,)
from stoqdrivers.enum import PaymentMethodType, TaxType, UnitType

def example():
    printer = FiscalPrinter()
    printer.identify_customer('Henrique Romano', 'Async', '1234567890')
    while True:
        try:
            printer.open()
            break
        except PendingReduceZ:
            printer.close_till()
            return
        except PendingReadX:
            printer.summarize()
            return
        except CouponOpenError:
            printer.cancel()

    item1_id = printer.add_item("123456", u"Hollywóód",
                                Decimal("2.00"), TaxType.SUBSTITUTION,
                                unit=UnitType.CUSTOM, unit_desc=u"mç")
    item2_id = printer.add_item("654321", u"Heineken Beer",
                                Decimal("1.53"), TaxType.NONE,
                                items_quantity=Decimal("5"),
                                unit=UnitType.LITERS)
    printer.cancel_item(item1_id)
    coupon_total = printer.totalize(discount=Decimal('1.0'))
    printer.add_payment(PaymentMethodType.MONEY, Decimal('2.00'))
    printer.add_payment(PaymentMethodType.MONEY, Decimal('11.00'))
    coupon_id = printer.close()
    print "+++ coupon %d created." % coupon_id

if __name__ == "__main__":
    example()
