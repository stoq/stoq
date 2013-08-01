# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

from zope.interface import implementer

from stoqlib.lib.defaults import quantize
from stoqlib.lib.interfaces import IPaymentOperation, IPaymentOperationManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IPaymentOperationManager)
class PaymentOperationManager(object):

    def __init__(self):
        self._methods = {}
        self._fallback_operation = None

    def register(self, name, klass):
        """
        :param name:
        :param klass:
        """
        if not IPaymentOperation.providedBy(klass):
            raise ValueError(
                "%r does not implement required interface "
                "IPaymentOperation" % (klass, ))
        self._methods[name] = klass

    def register_fallback(self, klass):
        if not IPaymentOperation.providedBy(klass):
            raise ValueError(
                "%r does not implement required interface "
                "IPaymentOperation" % (klass, ))
        self._fallback_operation = klass

    def get_operation_names(self):
        return list(self._methods.keys())

    def get(self, name):
        operation = self._methods.get(name)
        if not operation:
            operation = self._fallback_operation
        return operation


def generate_payments_values(value, n_values):
    """Calculates the values of payments

    :param value: value of payment to split
    :param n_values: the number of installments to split the value in
    :returns: a list with the values
    """
    if not n_values:
        raise ValueError(_('Need at least one value'))

    # Round off the individual installments
    # For instance, let's say we're buying something costing 100.00 and paying
    # in 3 installments, then we should have these payment values:
    # - Installment #1: 33.33
    # - Installment #2: 33.33
    # - Installment #3: 33.34
    normalized_value = quantize(value / n_values)
    normalized_values = [normalized_value] * n_values

    # Maybe adjust the last payment so it the total will sum up nicely,
    # for instance following the example above, this will add
    # 0.01 to the third installment, 100 - (33.33 * 3)
    # This is not always needed, since the individual installments might
    # sum up exact, eg 50 + 50
    difference = value - (normalized_value * n_values)
    if difference:
        normalized_values[-1] += difference

    return normalized_values
