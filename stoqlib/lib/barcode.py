# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Parse barcodes containing weight or price information, as those printed
by scales"""

from decimal import Decimal

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BarcodeInfo:
    (MODE_WEIGHT,
     MODE_PRICE) = range(2)

    (OPTION_4_DIGITS_PRICE,
     OPTION_5_DIGITS_PRICE,
     OPTION_4_DIGITS_WEIGHT,
     OPTION_5_DIGITS_WEIGHT,
     OPTION_6_DIGITS_WEIGHT) = range(5)

    options = {
        OPTION_4_DIGITS_PRICE: _(u'4 Digits Code with Price'),
        OPTION_5_DIGITS_PRICE: _(u'5 Digits Code with Price'),
        OPTION_4_DIGITS_WEIGHT: _(u'4 Digits Code with Weight'),
        OPTION_5_DIGITS_WEIGHT: _(u'5 Digits Code with Weight'),
        OPTION_6_DIGITS_WEIGHT: _(u'6 Digits Code with Weight'),
    }

    modes = {
        OPTION_4_DIGITS_PRICE: MODE_PRICE,
        OPTION_5_DIGITS_PRICE: MODE_PRICE,
        OPTION_4_DIGITS_WEIGHT: MODE_WEIGHT,
        OPTION_5_DIGITS_WEIGHT: MODE_WEIGHT,
        OPTION_6_DIGITS_WEIGHT: MODE_WEIGHT,
    }

    digits = {
        OPTION_4_DIGITS_PRICE: 4,
        OPTION_5_DIGITS_PRICE: 5,
        OPTION_4_DIGITS_WEIGHT: 4,
        OPTION_5_DIGITS_WEIGHT: 5,
        OPTION_6_DIGITS_WEIGHT: 6,
    }

    def __init__(self, code, price, weight, mode):
        self.code = code
        self.price = price
        self.weight = weight
        self.mode = mode


def parse_barcode(barcode, fmt=BarcodeInfo.OPTION_4_DIGITS_PRICE):
    if not barcode.startswith('2') or len(barcode) != 13:
        return None

    digits = BarcodeInfo.digits[fmt]
    mode = BarcodeInfo.modes[fmt]

    if mode == BarcodeInfo.MODE_PRICE:
        code = barcode[1:1 + digits]
        price = Decimal(barcode[7:-1]) / Decimal('1e2')
        weight = None
    elif mode == BarcodeInfo.MODE_WEIGHT:
        code = barcode[1:1 + digits]
        price = None
        weight = Decimal(barcode[8:-1]) / Decimal('1e3')

    return BarcodeInfo(code, price, weight, mode)


if __name__ == '__main__':  # pragma nocover
    barcode_ = '2000100005279'
    # 2 0001 00 00527 9

    print(parse_barcode('2000100005279', BarcodeInfo.OPTION_4_DIGITS_PRICE))
    print(parse_barcode('2123456005279', BarcodeInfo.OPTION_6_DIGITS_WEIGHT))
