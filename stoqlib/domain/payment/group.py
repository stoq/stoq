# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin               <jdahlin@async.com.br>
##
"""Payment groups, a set of payments

The two use cases for payment groups are:

  - Sale
  - Purchase

Both of them contains a list of payments and they behaves slightly
differently
"""

import datetime

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from sqlobject.col import IntCol, DateTimeCol
from sqlobject.sqlbuilder import AND, IN, const
from stoqdrivers.enum import PaymentMethodType
from zope.interface import implements

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.base import InheritableModelAdapter
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import (IContainer, IPaymentGroup,
                                       IInPayment)
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.till import Till
from stoqlib.lib.defaults import get_method_names
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class AbstractPaymentGroup(InheritableModelAdapter):
    """A base class for payment group adapters. """

    (STATUS_PREVIEW,
     STATUS_OPEN,
     STATUS_CLOSED,
     STATUS_CANCELLED) = range(4)

    statuses = {STATUS_PREVIEW: _(u"Preview"),
                STATUS_OPEN: _(u"Open"),
                STATUS_CLOSED: _(u"Closed"),
                STATUS_CANCELLED: _(u"Cancelled")}

    implements(IPaymentGroup, IContainer)

    status = IntCol(default=STATUS_OPEN)
    open_date = DateTimeCol(default=datetime.datetime.now)
    close_date = DateTimeCol(default=None)
    cancel_date = DateTimeCol(default=None)
    default_method = IntCol(default=int(PaymentMethodType.MONEY))
    installments_number = IntCol(default=1)
    interval_type = IntCol(default=None)
    intervals = IntCol(default=None)

    #
    # IPaymentGroup implementation
    #

    #
    # FIXME: We should to remove all these methods without implementation, so
    # we can ensure that interface are properly implemented in subclasses.
    #
    def get_thirdparty(self):
        raise NotImplementedError

    def get_group_description(self):
        """Returns a small description for the payment group which will be
        used in payment descriptions
        """
        raise NotImplementedError

    def update_thirdparty_status(self):
        raise NotImplementedError

    def get_balance(self):
        # FIXME: Move sum to SQL statement
        return sum([s.value for s in self.get_items()])

    def get_total_received(self):
        # FIXME: Proper implementation
        return currency(0)

    def add_payment(self, value, description, method, destination=None,
                    due_date=None):
        if due_date is None:
            due_date = const.NOW()
        """Create a new payment and add it to the group"""
        conn = self.get_connection()
        destination = destination or sysparam(conn).DEFAULT_PAYMENT_DESTINATION
        till = Till.get_current(conn)
        return Payment(due_date=due_date, value=value, till=till,
                       description=description, group=self, method=method,
                       destination=destination, connection=conn)

    def confirm(self):
        """This can be implemented in a subclass, but it's not required"""

    def pay(self, payment):
        pass

    #
    # IContainer implementation
    #

    @argcheck(Payment)
    def add_item(self, payment):
        payment.group = self

    @argcheck(Payment)
    def remove_item(self, payment):
        Payment.delete(payment.id, connection=self.get_connection())

    def get_items(self):
        return Payment.selectBy(group=self,
                                connection=self.get_connection())

    #
    # Fiscal methods
    #

    def _create_fiscal_entry(self, entry_type, cfop, invoice_number,
                             iss_value=0, icms_value=0, ipi_value=0):
        conn = self.get_connection()
        return FiscalBookEntry(
            entry_type=entry_type,
            iss_value=iss_value,
            ipi_value=ipi_value,
            icms_value=icms_value,
            invoice_number=invoice_number,
            cfop=cfop,
            drawee=self.get_thirdparty(),
            branch=get_current_branch(conn),
            date=const.NOW(),
            payment_group=self,
            connection=conn)

    def create_icmsipi_book_entry(self, cfop, invoice_number, icms_value,
                                  ipi_value=0):
        self._create_fiscal_entry(FiscalBookEntry.TYPE_PRODUCT, cfop,
                                  invoice_number,
                                  icms_value=icms_value, ipi_value=ipi_value)

    def create_iss_book_entry(self, cfop, invoice_number, iss_value):
        self._create_fiscal_entry(FiscalBookEntry.TYPE_SERVICE, cfop,
                                  invoice_number,
                                  iss_value=iss_value)

    def _get_paid_payments(self):
        return Payment.select(AND(Payment.q.groupID == self.id,
                                  IN(Payment.q.status,
                                     [Payment.STATUS_PAID,
                                      Payment.STATUS_REVIEWING,
                                      Payment.STATUS_CONFIRMED])),
                              connection=self.get_connection())

    #
    # Public API
    #

    def can_cancel(self):
        """
        @returns: True if it's possible to cancel the payment, otherwise False
        """
        return self.status != AbstractPaymentGroup.STATUS_CANCELLED

    def cancel(self, renegotiation):
        """
        Cancels the payment group.
        This method does very little, it just changes the status and
        marks the payment group as cancelled. It's up to the subclasses
        to decide how to treat cancellation of all the contained payments
        @param renegotiation: renegotiation information
        @type renegotiation: L{RenegotiationData}
        """
        assert self.can_cancel()
        self.status = AbstractPaymentGroup.STATUS_CANCELLED
        self.cancel_date = const.NOW()

    def get_total_paid(self):
        return currency(self._get_paid_payments().sum('value') or 0)

    def set_method(self, method):
        self.default_method = method

    def add_inpayments(self):
        from stoqlib.domain.payment.methods import MoneyPM
        conn = self.get_connection()
        till = Till.get_current(conn)

        payment_count = self.get_items().count()
        if not payment_count:
            raise ValueError(
                'You must have at least one payment for each payment group')
        self.installments_number = payment_count

        for payment in self.get_items():
            assert payment.is_preview()
            payment.set_pending()
            assert IInPayment(payment, None)
            till.add_entry(payment)

            if isinstance(payment.method, MoneyPM):
                payment.pay()

    def check_close(self):
        """Verifies if the payment group can be closed and close it.

        @returns: the close status, True if it has been closed or
                 False if not.
        """
        if not self.status == AbstractPaymentGroup.STATUS_OPEN:
            raise ValueError("The status for this payment group should be "
                             "opened, got %s" % self.get_status_string())
        payments = self.get_items()
        statuses = [Payment.STATUS_CONFIRMED, Payment.STATUS_CANCELLED]
        for payment in payments:
            if payment.status not in statuses:
                return False
        self.status = AbstractPaymentGroup.STATUS_CLOSED
        return True

    def clear_preview_payments(self, ignore_method=None):
        """Delete payments of preview status associated to the current
        payment_group. It can happen if user open and cancel this wizard.
        @param ignore_method: a payment method which will be ignored
                              in the search for payments
        """
        query = dict(status=Payment.STATUS_PREVIEW, group=self)

        conn = self.get_connection()
        if ignore_method:
            query['method'] = ignore_method.selectOne(connection=conn)

        for payment in Payment.selectBy(connection=conn, **query):
            inpayment = IInPayment(payment, None)
            if not inpayment:
                continue
            payment.method.delete_inpayment(inpayment)

    #
    # Accessors
    #

    def get_status_string(self):
        if not self.status in AbstractPaymentGroup.statuses.keys():
            raise DatabaseInconsistency("Invalid status, got %d"
                                        % self.status)
        return self.statuses[self.status]

    def get_default_payment_method(self):
        """This hook must be redefined in a subclass when it's necessary"""
        return self.default_method

    def get_default_payment_method_name(self):
        """This hook must be redefined in a subclass when it's necessary"""
        method_names = get_method_names()
        if not self.default_method in method_names.keys():
            raise DatabaseInconsistency('Invalid payment method, got %d'
                                        % self.default_method)
        return method_names[self.default_method]


