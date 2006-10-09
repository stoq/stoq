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

from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.exceptions import (PendingReduceZ,
                                    PendingReadX,
                                    CouponOpenError,)
from stoqdrivers.constants import (TAX_SUBSTITUTION,
                                   UNIT_CUSTOM,
                                   TAX_NONE,
                                   UNIT_LITERS,
                                   MONEY_PM,)
def example():
    printer = FiscalPrinter()
    printer.cancel()
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
                                Decimal("2.00"), TAX_SUBSTITUTION,
                                unit=UNIT_CUSTOM, unit_desc=u"mç")
    item2_id = printer.add_item("654321", u"Heineken Beer",
                                Decimal("1.53"), TAX_NONE,
                                items_quantity=Decimal("5"),
                                unit=UNIT_LITERS)
    printer.cancel_item(item1_id)
    coupon_total = printer.totalize(discount=Decimal('1.0'))
    printer.add_payment(MONEY_PM, Decimal('2.00'))
    printer.add_payment(MONEY_PM, Decimal('11.00'))
    coupon_id = printer.close()
    print "+++ coupon %d created." % coupon_id

if __name__ == "__main__":
    example()
