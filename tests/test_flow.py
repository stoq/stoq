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

from decimal import Decimal
from unittest import TestCase, makeSuite, TextTestRunner

from stoqdrivers.constants import UNIT_EMPTY, TAX_NONE, MONEY_PM
from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.exceptions import (CancelItemError, CloseCouponError,
                                    PaymentAdditionError, CouponNotOpenError,
                                    AlreadyTotalized)

class FlowTest(TestCase):
    """ Responsible for test the coupon workflow. Currently this test works
    with:

    * Sweda IFS9000I
    * Bematech MP25FI
    * Dataregis 375EP
    * PertoPay 2023
    """
    _printer = None

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        if FlowTest._printer is None:
            FlowTest._printer = FiscalPrinter()

    def test1_AddItemWithoutCoupon(self):
        if (FlowTest._printer.brand == "dataregis"
            or FlowTest._printer.brand == "perto"):
            print ("skipping test (it isn't supported on `%s')"
                   % FlowTest._printer.brand)
            return
        self.failUnlessRaises(CouponNotOpenError, FlowTest._printer.add_item,
                              "000001", Decimal("2"), Decimal("1.30"),
                              UNIT_EMPTY, "Cigarro", TAX_NONE, Decimal("0"),
                              Decimal("0"))
        FlowTest._printer.open()

    def test2_CancelItemTwice(self):
        i1 = FlowTest._printer.add_item("000001", Decimal("2"), Decimal("1.30"),
                                        UNIT_EMPTY, "Cigarro", TAX_NONE,
                                        Decimal("0"), Decimal("0"))
        i2 = FlowTest._printer.add_item("000002", Decimal("3"), Decimal("5.20"),
                                        UNIT_EMPTY, "Cerveja", TAX_NONE,
                                        Decimal("0"), Decimal("0"))
        i3 = FlowTest._printer.add_item("000003", Decimal("1"), Decimal("2.30"),
                                        UNIT_EMPTY,"Isqueiro", TAX_NONE,
                                        Decimal("0"), Decimal("0"))
        FlowTest._printer.cancel_item(i3)
        self.failUnlessRaises(CancelItemError,
                              FlowTest._printer.cancel_item, i3)

    def test3_CloseCouponWithoutTotalize(self):
        self.failUnlessRaises(CloseCouponError, FlowTest._printer.close)

    def test4_AddPaymentWithoutTotalize(self):
        self.failUnlessRaises(PaymentAdditionError,
                              FlowTest._printer.add_payment, MONEY_PM,
                              Decimal("100.0"), "")
        FlowTest._printer.totalize(Decimal("0"), Decimal("0"), TAX_NONE)

    def test5_AddItemWithCouponTotalized(self):
        self.failUnlessRaises(AlreadyTotalized, FlowTest._printer.add_item,
                              "0005", Decimal("4"), Decimal("2.30"),
                              UNIT_EMPTY, "Cigarro", TAX_NONE, Decimal("0"),
                              Decimal("0"))

    def test6_CloseCouponWithoutPayments(self):
        if FlowTest._printer.brand != "dataregis":
            self.failUnlessRaises(CloseCouponError, FlowTest._printer.close)
        else:
            print ("skipping test (it isn't supported on `%s')"
                   % FlowTest._printer.brand)
        FlowTest._printer.add_payment(MONEY_PM, Decimal("100.0"), "")
        FlowTest._printer.close()

def test():
    s = makeSuite(FlowTest)
    TextTestRunner(verbosity=2).run(s)

if __name__ == "__main__":
    test()
