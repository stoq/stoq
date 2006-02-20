# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
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
## Author(s):   Henrique Romano        <henrique@async.com.br>
##
" A simple test case to check if the coupon workflow is managed properly. "

import sys
from decimal import Decimal

from stoqdrivers.constants import UNIT_EMPTY, TAX_NONE, MONEY_PM
from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.exceptions import (
    CouponOpenError, CancelItemError, CloseCouponError, PaymentAdditionError,
    ItemAdditionError, PendingReduceZ, PendingReadX, CouponNotOpenError,
    AlreadyTotalized)

#
# Currently this test works perfectly with:
#
# * Sweda IFS9000I
# * Bematech MP25FI
# * Dataregis 375EP
# * PertoPay 2023
#
# TODO:
#
# * Check if all the tests works with the others supported printers
#   -- the main test here is ensure the exceptions raised, i.e. the
#   same exceptions must be raised on the same erros conditions on
#   all the printers.
#
#

class InvalidResult(Exception):
    """ Invalid result for the test. """

def testAddItemWithoutCoupon(printer):
    try:
        printer.open()
        printer.cancel()
        printer.add_item("000001", Decimal("2"), Decimal("1.30"),
                         UNIT_EMPTY, "Cigarro", TAX_NONE,
                         Decimal("0"), Decimal("0"))
    except CouponNotOpenError:
        print "* Test Add Item Without Coupon: OK."
    except PendingReadX:
        print ("*** A read X is needed and will be made right now\n"
               "*** restart the tests after that.\n\n")
        printer.summarize()
        sys.exit()
    except PendingReduceZ:
        print ("*** A reduce Z is needed and will be made right now\n"
               "*** restart the tests after that.\n\n")
        printer.close_till()
        sys.exit()
    else:
        raise InvalidResult("CouponNotOpenError exception expected.")

def testCancelItemTwice(printer):
    item_1 = printer.add_item("000001", Decimal("2"), Decimal("1.30"),
                              UNIT_EMPTY, "Cigarro", TAX_NONE,
                              Decimal("0"), Decimal("0"))
    item_2 = printer.add_item("000002", Decimal("3"), Decimal("5.20"),
                              UNIT_EMPTY, "Cerveja", TAX_NONE,
                              Decimal("0"), Decimal("0"))
    item_3 = printer.add_item("000003", Decimal("1"), Decimal("2.30"),
                              UNIT_EMPTY,"Isqueiro", TAX_NONE,
                              Decimal("0"), Decimal("0"))
    try:
        printer.cancel_item(item_3)
        printer.cancel_item(item_3)
    except CancelItemError:
        print "Test Cancel Item Twice: OK."
    else:
        raise InvalidResult("CancelItemError exception expected.")

def testCloseCouponWithoutTotalize(printer):
    try:
        printer.close()
    except CloseCouponError:
        print "Test Close Coupon Without Totalize: OK."
    else:
        raise InvalidResult("CloseCouponError exception expected.")

def testAddPaymentWithoutTotalize(printer):
    try:
        printer.add_payment(MONEY_PM, Decimal("100.0"), "")
    except PaymentAdditionError:
        print "Test Add Payment Without Totalize: OK."
    else:
        raise InvalidResult("PaymentAdditionError exception expected.")

def testAddItemWithCouponTotalized(printer):
    printer.totalize(0, 0, TAX_NONE)
    try:
        printer.add_item("0005", Decimal("4"), Decimal("2.30"), UNIT_EMPTY,
                         "Cigarro", TAX_NONE, Decimal("0"), Decimal("0"))
    except AlreadyTotalized:
        print "Test Add Item With Coupon Totalized: OK."
    else:
        raise InvalidResult("AlreadyTotalized exception expected.")

def testCloseCouponWithoutPayments(printer):
    try:
        printer.close()
    except CloseCouponError:
        print "Test Close Coupon Without Payments: OK."
    else:
        raise InvalidResult("CloseCouponError exception expected.")


def test():
    printer = FiscalPrinter()

    if printer.brand == "dataregis" or printer.brand == "perto":
        print ("+++ Skipping test `Add Item Without Coupon', since it "
               "isn't supported on `%s'" % printer.brand)
    else:
        testAddItemWithoutCoupon(printer)
    printer.open()
    testCancelItemTwice(printer)
    testCloseCouponWithoutTotalize(printer)
    testAddPaymentWithoutTotalize(printer)
    printer.totalize(Decimal("0"), Decimal("0"), TAX_NONE)
    testAddItemWithCouponTotalized(printer)
    if printer.brand == "dataregis":
        print ("+++ Skipping test `Close Coupon Without Payments', since "
               "it isn't supported on Dataregis")
    else:
        testCloseCouponWithoutPayments(printer)
    printer.add_payment(MONEY_PM, Decimal("100.0"), "")
    printer.close()

if __name__ == "__main__":
    test()
