# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

from decimal import Decimal

from zope.interface import implements

from stoqlib.lib.defaults import calculate_delta_interval, quantize
from stoqlib.lib.interfaces import IPaymentOperation, IPaymentOperationManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PaymentOperationManager(object):
    implements(IPaymentOperationManager)

    def __init__(self):
        self._methods = {}

    def register(self, name, klass):
        """
        @param name:
        @param klass:
        """
        if not IPaymentOperation.providedBy(klass):
            raise ValueError(
                "%r does not  implement required interface "
                "IPaymentOperation" % (klass, ))
        self._methods[name] = klass

    def get_operation_names(self):
        return self._methods.keys()

    def get(self, name):
        return self._methods.get(name)


def generate_payments_values(value, installments_number,
                             interest=Decimal(0)):
    """Calculates the values of payments

    @param value: value of payment
    @param installments_number: the number of installments
    @param interest: a L{Decimal} with the interest
    @returns: a list with the values
    """
    assert installments_number > 0

    if interest:
        interest_rate = interest / 100 + 1
        normalized_value = quantize((value / installments_number)
                                    * interest_rate)
        interest_total = normalized_value * installments_number - value
    else:
        normalized_value = quantize(value / installments_number)
        interest_total = Decimal(0)

    payments = []
    payments_total = Decimal(0)
    for i in range(installments_number):
        payments.append(normalized_value)
        payments_total += normalized_value

    # Adjust the last payment so the total will sum up nicely.
    difference = -(payments_total - interest_total - value)
    if difference:
        payments[-1] += difference

    return payments


def generate_payments_due_dates(installments_number, first_due_date,
                                interval, interval_type):
    """Calculates the due dates of payments

    @param installments_number: the number of installments
    @param first_due_date: a L{datetime.datetime} or L{datetime.date}
    object containing the first due date
    @param interval: the interval between due_dates
    @param interval_type: an interval_type from L{stoqlib.lib.defaults}
    @returns: a list with the due_dates
    """
    assert installments_number > 0

    due_dates = []
    delta = calculate_delta_interval(interval_type, interval)
    d = first_due_date
    for i in range(installments_number):
        due_dates.append(d)
        d += delta

    return due_dates
