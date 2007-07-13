# -*- Mode: Python; coding: iso-8859-1 -*-
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
## Author(s):   Henrique Romano  <henrique@async.com.br>
##              Johan Dahlin     <jdahlin@async.com.br>
##
##
"""
A simple implementation of a virtual printer.
"""
import datetime
from decimal import Decimal

from kiwi.python import Settable
from zope.interface import implements

from stoqdrivers.enum import PaymentMethodType, TaxType, UnitType
from stoqdrivers.exceptions import (CouponTotalizeError, PaymentAdditionError,
                                    CloseCouponError, CouponOpenError,
                                    CancelItemError, ItemAdditionError,
                                    DriverError)
from stoqdrivers.interfaces import ICouponPrinter, IChequePrinter
from stoqdrivers.printers.base import BaseDriverConstants
from stoqdrivers.printers.capabilities import Capability
from stoqdrivers.translation import stoqdrivers_gettext

_ = lambda msg: stoqdrivers_gettext(msg)

class CouponItem:
    def __init__(self, id, quantity, value):
        self.id, self.quantity, self.value = id, quantity, value

    def get_total_value(self):
        return self.quantity * self.value

class FakeConstants(BaseDriverConstants):
    _constants = {
        UnitType.WEIGHT:      'F',
        UnitType.METERS:      'G ',
        UnitType.LITERS:      'H',
        UnitType.EMPTY:       'I',

        PaymentMethodType.MONEY: 'M',
        PaymentMethodType.CHECK: 'C',
        PaymentMethodType.BILL: 'B',
        PaymentMethodType.CREDIT_CARD: 'R',
        PaymentMethodType.DEBIT_CARD: 'D',
        PaymentMethodType.FINANCIAL: 'F',
        PaymentMethodType.GIFT_CERTIFICATE: 'G',

        }

    _tax_constants = [
        (TaxType.SUBSTITUTION, 'TS', None),
        (TaxType.EXEMPTION,    'TE', None),
        (TaxType.NONE,         'TN', None),
        (TaxType.CUSTOM,       'T1', Decimal(18)),
        (TaxType.CUSTOM,       'T2', Decimal(12)),
        (TaxType.CUSTOM,       'T3', Decimal(5)),
        (TaxType.SERVICE,      'S0', Decimal(3)),
        ]


class Simple:
    implements(IChequePrinter, ICouponPrinter)

    model_name = "Virtual Printer"
    cheque_printer_charset = "latin-1"
    coupon_printer_charset = "latin-1"

    def __init__(self, port, consts):
        self._till_closed = False
        self._consts = consts or FakeConstants()
        self._reset_flags()

    #
    # Helper methods
    #

    def _reset_flags(self):
        self.is_coupon_opened = False
        self.items_quantity = 0
        self.is_coupon_totalized = False
        self.totalized_value = Decimal("0.0")
        self.has_payments = False
        self.payments_total = Decimal("0.0")
        self._items = {}

    def _check_coupon_is_opened(self):
        if not self.is_coupon_opened:
            raise CouponOpenError(_("There is no coupon opened!"))

    def _check_coupon_is_closed(self):
        if self.is_coupon_opened:
            raise CouponOpenError(_("There is a coupon already open"))

    #
    # ICouponPrinter implementation
    #

    def coupon_identify_customer(self, customer, address, document):
        self._customer_name = customer
        self._customer_document = document
        self._customer_address = address

    def coupon_open(self):
        self._check_coupon_is_closed()
        self.is_coupon_opened = True

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UnitType.EMPTY,
                        discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), unit_desc=""):
        self._check_coupon_is_opened()
        if self.is_coupon_totalized:
            raise ItemAdditionError(_("The coupon is already totalized, "
                                      "you can't add items anymore."))
        self.items_quantity += 1
        item_id = self.items_quantity
        self._items[item_id] = CouponItem(item_id, quantity, price)
        return item_id

    def coupon_cancel_item(self, item_id):
        self._check_coupon_is_opened()
        if not item_id in self._items:
            raise CancelItemError(_("There is no item with this ID (%d)")
                                  % item_id)
        elif self.is_coupon_totalized:
            raise CancelItemError(_("The coupon is already totalized, "
                                    "you can't cancel items anymore."))
        del self._items[item_id]

    def coupon_cancel(self):
        # FIXME: If we don't have a coupon open, verify that
        #        we've opened at least one
        #self._check_coupon_is_opened()
        self._reset_flags()

    def coupon_totalize(self, discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), taxcode=TaxType.NONE):
        self._check_coupon_is_opened()
        if not self.items_quantity:
            raise CouponTotalizeError(_("The coupon can't be totalized, since "
                                        "there is no items added"))
        elif self.is_coupon_totalized:
            raise CouponTotalizeError(_("The coupon is already totalized"))

        for item_id, item in self._items.items():
            self.totalized_value += item.get_total_value()

        surcharge_value = self.totalized_value * surcharge / 100
        discount_value = self.totalized_value * discount / 100
        self.totalized_value += (
            Decimal(-discount_value).quantize(Decimal('.01')) +
            Decimal(surcharge_value).quantize(Decimal('.01')))

        if not self.totalized_value > 0:
            raise CouponTotalizeError(_("Coupon totalized must be greater "
                                        "than zero!"))

        self.is_coupon_totalized = True
        return self.totalized_value

    def coupon_add_payment(self, payment_method, value, description=u"",
                           custom_pm=""):
        if not self.is_coupon_totalized:
            raise PaymentAdditionError(_("Isn't possible add payments to the "
                                         "coupon since it isn't totalized"))
        self.payments_total += value
        self.has_payments = True
        return self.totalized_value - self.payments_total

    def coupon_close(self, message=''):
        self._check_coupon_is_opened()
        if not self.is_coupon_totalized:
            raise CloseCouponError(_("Isn't possible close the coupon "
                                     "since it isn't totalized yet!"))
        elif not self.has_payments:
            raise CloseCouponError(_("Isn't possible close the coupon "
                                     "since there is no payments added."))
        elif self.totalized_value > self.payments_total:
            raise CloseCouponError(_("The payments total value doesn't "
                                     "match the totalized value."))
        self._reset_flags()
        return 0

    def get_capabilities(self):
        # fake values
        return dict(item_code=Capability(max_len=48),
                    item_id=Capability(max_size=32767),
                    items_quantity=Capability(digits=14, decimals=4),
                    item_price=Capability(digits=14, decimals=4),
                    item_description=Capability(max_len=200),
                    payment_value=Capability(digits=14, decimals=4),
                    promotional_message=Capability(max_len=492),
                    payment_description=Capability(max_len=80),
                    customer_name=Capability(max_len=30),
                    customer_id=Capability(max_len=29),
                    customer_address=Capability(max_len=80),
                    cheque_thirdparty=Capability(max_len=45),
                    cheque_value=Capability(digits=14, decimals=4),
                    cheque_city=Capability(max_len=27))

    def get_constants(self):
        return self._consts

    def summarize(self):
        return

    def close_till(self, previous_day=False):
        if self._till_closed:
            raise DriverError(
                "Reduce Z was already sent today, try again tomorrow")
        self._till_closed = True

        # Sintegra is disabled until we solve connection problems in stoqlib
        return None
        total = sum(i.get_total_value() for i in self._items.values())
        if self._items:
            last_item = max(self._items.keys())
        else:
            last_item = 1

        return Settable(
            opening_date=datetime.date.today(),
            serial='Stoq Virtual Printer',
            serial_id=000,
            coupon_start=1,
            coupon_end=last_item,
            crz=1,
            cro=1,
            period_total=total,
            total=total,
            tax_total=total)

    def till_add_cash(self, value):
        pass

    def till_remove_cash(self, value):
        pass

    def till_read_memory(self, start, end):
        pass

    def till_read_memory_by_reductions(self, start, end):
        pass


    #
    # IChequePrinter implementation
    #

    def print_cheque(self, value, thirdparty, city, date=None):
        return
