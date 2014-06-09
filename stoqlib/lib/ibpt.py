# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
"""
Identify and apply to a product, the defined taxes by
IBPT - Instituto Brasileiro de Planejamento Tributário (Brazilian Institute
of Tributary Planning)
According to Law 12,741 of 12/08/2012 - Taxes in Coupon.
"""
from kiwi.environ import environ

import csv
from decimal import Decimal

taxes_data = {}


def load_taxes_csv():
    # Avoid load taxes more than once.
    if taxes_data:
        return

    filename = environ.find_resource('csv', 'tabela_ibpt.csv')
    csv_file = (csv.reader(open(filename, "r")))
    for (ncm, ex, tabela, nac, imp, __) in csv_file:
        if tabela == '1':
            continue
        tax_dict = taxes_data.setdefault(ncm, {})
        tax_dict[ex] = (nac, imp)


def calculate_tax_for_item(item):
    """ Calculate the IBPT tax for a give item.

    :param item: a |saleitem|
    :returns: the IBPT tax or ``0`` if it does not exist
    :rtype: decimal
    """
    load_taxes_csv()

    sellable = item.sellable
    product = sellable.product
    if not product:
        return Decimal("0")
    ncm = product.ncm or ''
    options = taxes_data.get(ncm.lstrip('0'), {})
    n_options = len(options)
    if n_options == 0:
        tax_value = Decimal("0"), Decimal("0")
    elif n_options == 1:
        tax_value = options['']
    else:
        ex_tipi = product.ex_tipi or ''
        tax_value = options.get(ex_tipi.lstrip('0')) or options['']

    if product.icms_template:
        origin = product.icms_template.orig
    else:
        # If the product does not have any fiscal information, defaults to
        # national origin
        origin = 0

    # Values (0, 3, 4, 5, 8) represent the taxes codes of brazilian origin.
    if origin in [0, 3, 4, 5, 8]:
        tax_origin_value = Decimal(tax_value[0]) / 100
    # Different codes, represent taxes of international origin.
    else:
        tax_origin_value = Decimal(tax_value[1]) / 100

    total_item = item.price * item.quantity
    item_tax = total_item * tax_origin_value
    return item_tax
