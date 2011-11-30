# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
import locale
from kiwi.datatypes import get_localeconv

LANG = locale.getlocale()[0]
currency_symbol = get_localeconv()['currency_symbol']

if LANG == 'pt_BR':
    from stoqlib.lib.cardinals_ptbr import to_words_as_money
    assert to_words_as_money # pyflakes
    currency_names = ['real', 'reais', 'centavo', 'centavos']
else:
    from stoqlib.lib.cardinals_en import to_words_as_money
    assert to_words_as_money # pyflakes
    currency_names = ['dollar', 'dollars', 'cent', 'cents']


def get_price_cardinal(price):
    """Return the price as a cardinal number"""
    return to_words_as_money(price, currency_names)
