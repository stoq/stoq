#
# Stoqdrivers template driver
#
# Copyright (C) 2007 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
# USA.
#

import datetime
from decimal import Decimal
from kiwi.python import Settable
from zope.interface import implements

from stoqdrivers.enum import TaxType
from stoqdrivers.interfaces import ICouponPrinter
from stoqdrivers.printers.capabilities import Capability
from stoqdrivers.serialbase import SerialBase
from stoqdrivers.translation import stoqdrivers_gettext

_ = stoqdrivers_gettext


class MP25(SerialBase):
    implements(ICouponPrinter)

    supported = True
    model_name = "Template Driver"
    coupon_printer_charset = "ascii"

    def __init__(self, port, consts=None):
        SerialBase.__init__(self, port)

    #
    # This implements the ICouponPrinter Interface
    #

    def summarize(self):
        # Leitura X 
        pass

    def close_till(self, previous_day):
        # Redução Z
        pass

    def till_add_cash(self, value):
        pass

    def till_remove_cash(self, value):
        pass

    def till_read_memory(self, start, end):
        pass

    def till_read_memory_by_reductions(self, start, end):
        pass

    def coupon_identify_customer(self, customer, address, document):
        pass

    def coupon_open(self):
        pass

    def coupon_cancel(self):
        pass

    def coupon_close(self, message):
        coupon_id = 123
        return coupon_id

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity, unit, discount, markup, unit_desc):
        item_id = 123
        return item_id

    def coupon_cancel_item(self, item_id):
        pass

    def coupon_add_payment(self, payment_method, value, description):
        return Decimal("123")

    def coupon_totalize(self, discount, markup, taxcode):
        return Decimal("123")

    def get_capabilities(self):
        return dict(
            item_code=Capability(max_len=13),
            item_id=Capability(digits=4),
            items_quantity=Capability(min_size=1, digits=4, decimals=3),
            item_price=Capability(digits=6, decimals=2),
            item_description=Capability(max_len=29),
            payment_value=Capability(digits=12, decimals=2),
            promotional_message=Capability(max_len=320),
            payment_description=Capability(max_len=48),
            customer_name=Capability(max_len=30),
            customer_id=Capability(max_len=28),
            customer_address=Capability(max_len=80),
            add_cash_value=Capability(min_size=0.1, digits=12, decimals=2),
            remove_cash_value=Capability(min_size=0.1, digits=12, decimals=2),
            )

    def get_constants(self):
        return self._consts

    def query_status(self):
        return 'XXX'

    def status_reply_complete(self, reply):
        return len(reply) == 23

    def _get_serial(self):
        return 'ABC12345678'

    def get_tax_constants(self):
        constants = []
        constants.append((TaxType.CUSTOM,
                          '01',
                          Decimal('18.00')))
        constants.append((TaxType.CUSTOM,
                          '02',
                          Decimal('25.00')))

        constants.extend([
            (TaxType.SUBSTITUTION, 'FF', None),
            (TaxType.EXEMPTION,    'II', None),
            (TaxType.NONE,         'NN', None),
            ])

        return constants

    def get_payment_constants(self):
        methods = []
        methods.append(('01', 'DINHEIRO'))
        methods.append(('02', 'CHEQUE'))
        return methods

    def get_sintegra(self):
        taxes = []
        taxes.append(('2500', Decimal("0")))
        taxes.append(('1800', Decimal("0")))
        taxes.append(('CANC', Decimal("0")))
        taxes.append(('DESC', Decimal("0")))
        taxes.append(('I', Decimal("0")))
        taxes.append(('N', Decimal("0")))
        taxes.append(('F', Decimal("0")))

        return Settable(
             opening_date=datetime.date(2000, 1, 1),
             serial=self._get_serial(),
             serial_id='001',
             coupon_start=0,
             coupon_end=100,
             cro=230,
             crz=1232,
             period_total=Decimal("1123"),
             total=Decimal("2311123"),
             taxes=taxes)

