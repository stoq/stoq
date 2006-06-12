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

from stoqdrivers.constants import (TAX_NONE, MONEY_PM, TAX_SUBSTITUTION,
                                   UNIT_CUSTOM, UNIT_LITERS, TAX_ICMS)
from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.exceptions import (CancelItemError, CloseCouponError,
                                    PaymentAdditionError, CouponNotOpenError,
                                    AlreadyTotalized, InvalidValue)

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
                              u"000001", u"Cigarro", Decimal("1.30"),
                              TAX_SUBSTITUTION, Decimal("2.0"),
                              unit=UNIT_CUSTOM, unit_desc="mc")
        FlowTest._printer.open()

    def test2_CancelItemTwice(self):
        i1 = FlowTest._printer.add_item(u"000001", u"Cigarro", Decimal("1.30"),
                                        TAX_SUBSTITUTION, Decimal("2.0"),
                                        unit=UNIT_CUSTOM, unit_desc=u"mc")
        i2 = FlowTest._printer.add_item(u"000002", u"Cerveja", Decimal("5.20"),
                                        TAX_SUBSTITUTION, Decimal("3.0"),
                                        unit=UNIT_LITERS)
        i3 = FlowTest._printer.add_item(u"000003", u"Isqueiro", Decimal("2.30"),
                                        TAX_ICMS, Decimal("1.0"),
                                        unit=UNIT_CUSTOM, unit_desc="pc")
        FlowTest._printer.cancel_item(i3)
        self.failUnlessRaises(CancelItemError,
                              FlowTest._printer.cancel_item, i3)

    def test3_CloseCouponWithoutTotalize(self):
        self.failUnlessRaises(CloseCouponError, FlowTest._printer.close)

    def test4_AddItemWithoutValue(self):
        self.failUnlessRaises(InvalidValue, FlowTest._printer.add_item,
                              "000004", "Nothing", Decimal("0.0"),
                              TAX_NONE, items_quantity=Decimal("1.0"))

    def test5_AddPaymentWithoutTotalize(self):
        self.failUnlessRaises(PaymentAdditionError,
                              FlowTest._printer.add_payment, MONEY_PM,
                              Decimal("100.0"), "")
        FlowTest._printer.totalize(Decimal("0"), Decimal("0"), TAX_NONE)

    def test6_AddItemWithCouponTotalized(self):
        self.failUnlessRaises(AlreadyTotalized, FlowTest._printer.add_item,
                              u"000001", u"Cigarro", Decimal("2.30"),
                              TAX_SUBSTITUTION, Decimal("4.0"),
                              unit=UNIT_CUSTOM, unit_desc="mc")

    def test7_CloseCouponWithoutPayments(self):
        if FlowTest._printer.brand != "dataregis":
            self.failUnlessRaises(CloseCouponError, FlowTest._printer.close)
        else:
            print ("skipping test (it isn't supported on `%s')"
                   % FlowTest._printer.brand)
        FlowTest._printer.add_payment(MONEY_PM, Decimal("100.0"))
        FlowTest._printer.close()

def test():
    s = makeSuite(FlowTest)
    TextTestRunner(verbosity=2).run(s)

if __name__ == "__main__":
    test()
