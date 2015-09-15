# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2014 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Payment management implementations.

This module is centered around payments.

The main payment class is |payment| which is a transfer of money,
to or from a |branch|.

Certain changes to a payment is saved in :class:`PaymentChangeHistory`
"""

# pylint: enable=E1101

import logging

from kiwi.currency import currency
from storm.references import Reference, ReferenceSet

from stoqlib.database.expr import TransactionTimestamp
from stoqlib.database.properties import (DateTimeCol, BoolCol,
                                         PriceCol, UnicodeCol, IdentifierCol,
                                         IdCol, EnumCol)
from stoqlib.domain.account import AccountTransaction
from stoqlib.domain.base import Domain
from stoqlib.domain.event import Event
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
from stoqlib.lib.dateutils import create_date_interval, localnow, localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = logging.getLogger(__name__)


class Payment(Domain):
    """Payment, a transfer of money between a |branch| and |client| or a
    |supplier|.

    Payments between:

    * a client and a branch are :obj:`.TYPE_IN`, has a |sale| associated.
    * branch and a supplier are :obj:`.TYPE_OUT`, has a |purchase| associated.

    Payments are sometimes referred to as *installments*.

    Sales and purchase orders can be accessed via the
    :obj:`payment group <.group>`

    +-------------------------+-------------------------+
    | **Status**              | **Can be set to**       |
    +-------------------------+-------------------------+
    | :obj:`STATUS_PREVIEW`   | :obj:`STATUS_PENDING`   |
    +-------------------------+-------------------------+
    | :obj:`STATUS_PENDING`   | :obj:`STATUS_PAID`,     |
    |                         | :obj:`STATUS_CANCELLED` |
    +-------------------------+-------------------------+
    | :obj:`STATUS_PAID`      | :obj:`STATUS_PENDING`,  |
    |                         | :obj:`STATUS_CANCELLED` |
    +-------------------------+-------------------------+
    | :obj:`STATUS_CANCELLED` | None                    |
    +-------------------------+-------------------------+

    .. graphviz::

       digraph status {
         STATUS_PREVIEW -> STATUS_PENDING;
         STATUS_PENDING -> STATUS_PAID;
         STATUS_PENDING -> STATUS_CANCELLED;
         STATUS_PAID -> STATUS_PENDING;
         STATUS_PAID -> STATUS_CANCELLED;
       }

    Simple sale workflow:

    * Creating a sale, status is set to :obj:`STATUS_PREVIEW`
    * Confirming the sale, status is set to :obj:`STATUS_PENDING`
    * Paying the installment, status is set to :obj:`STATUS_PAID`
    * Cancelling the payment, status is set to :obj:`STATUS_CANCELLED`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/payment.html>`__
    """

    __storm_table__ = 'payment'

    #: incoming to the company, accounts receivable, payment from
    #: a |client| to a |branch|
    TYPE_IN = u'in'

    #: outgoing from the company, accounts payable, a payment from
    #: |branch| to a |supplier|
    TYPE_OUT = u'out'

    #: payment group this payment belongs to hasn't been confirmed,
    # should normally be filtered when showing a payment list
    STATUS_PREVIEW = u'preview'

    #: payment group has been confirmed and the payment has not been received
    STATUS_PENDING = u'pending'

    #: the payment has been received
    STATUS_PAID = u'paid'

    # FIXME: Remove these two
    #: Unused.
    STATUS_REVIEWING = u'reviewing'

    #: Unused.
    STATUS_CONFIRMED = u'confirmed'

    #: payment was cancelled, for instance the payments of the group was changed, or
    #: the group was cancelled.
    STATUS_CANCELLED = u'cancelled'

    statuses = {STATUS_PREVIEW: _(u'Preview'),
                STATUS_PENDING: _(u'To Pay'),
                STATUS_PAID: _(u'Paid'),
                STATUS_REVIEWING: _(u'Reviewing'),
                STATUS_CONFIRMED: _(u'Confirmed'),
                STATUS_CANCELLED: _(u'Cancelled')}

    #: type of payment :obj:`.TYPE_IN` or :obj:`.TYPE_OUT`
    payment_type = EnumCol(allow_none=False, default=TYPE_IN)

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status, see |payment| for more information.
    status = EnumCol(allow_none=False, default=STATUS_PREVIEW)

    #: description payment, usually something like "1/3 Money for Sale 1234"
    description = UnicodeCol(default=None)

    # FIXME: use TransactionTimestamp() instead to avoid server/client date
    #        inconsistencies

    #: when this payment was opened
    open_date = DateTimeCol(default_factory=localnow)

    #: when this payment is due
    due_date = DateTimeCol()

    #: when this payment was paid
    paid_date = DateTimeCol(default=None)

    #: when this payment was cancelled
    cancel_date = DateTimeCol(default=None)

    # FIXME: Figure out when and why this differs from value
    #: base value
    base_value = PriceCol(default=None)

    #: value of the payment
    value = PriceCol()

    #: the actual amount that was paid, including penalties, interest, discount etc.
    paid_value = PriceCol(default=None)

    #: interest of this payment
    interest = PriceCol(default=0)

    #: discount, an absolute value with the difference between the
    #: sales price and :obj:`.value`
    discount = PriceCol(default=0)

    #: penalty of the payment
    penalty = PriceCol(default=0)

    # FIXME: Figure out what this is used for
    #: number of the payment
    payment_number = UnicodeCol(default=None)

    branch_id = IdCol(allow_none=False)

    #: |branch| associated with this payment.
    #: For a :obj:`.TYPE_IN` payment, this is the branch that will receive
    #: the money. For a :obj:`.TYPE_IN` payment, this is the branch that
    #: will make the payment
    branch = Reference(branch_id, 'Branch.id')

    method_id = IdCol()

    #: |paymentmethod| for this payment
    #: payment
    method = Reference(method_id, 'PaymentMethod.id')

    group_id = IdCol()

    #: |paymentgroup| for this payment
    group = Reference(group_id, 'PaymentGroup.id')

    category_id = IdCol()

    #: |paymentcategory| this payment belongs to, can be None
    category = Reference(category_id, 'PaymentCategory.id')

    #: list of :class:`comments <stoqlib.domain.payment.comments.PaymentComment>` for
    #: this payment
    comments = ReferenceSet('id', 'PaymentComment.payment_id')

    #: :class:`check data <stoqlib.domain.payment.method.CheckData>` for
    #: this payment
    check_data = Reference('id', 'CheckData.payment_id', on_remote=True)

    #: |accounttransaction| for this payment
    transaction = Reference('id', 'AccountTransaction.payment_id', on_remote=True)

    #: indicates if a bill has been received. They are usually delivered by
    #: mail before the due date. This is not indicating whether the payment has
    #: been paid, just that the receiver has notified the payer somehow.
    bill_received = BoolCol(default=False)

    attachment_id = IdCol()

    #: |attachment| for this payment
    attachment = Reference(attachment_id, 'Attachment.id')

    def __init__(self, store=None, **kw):
        if not 'value' in kw:
            raise TypeError('You must provide a value argument')
        if not 'base_value' in kw or not kw['base_value']:
            kw['base_value'] = kw['value']
        Domain.__init__(self, store=store, **kw)

    def _check_status(self, status, operation_name):
        fmt = 'Invalid status for %s operation: %s'
        assert self.status == status, (
            fmt % (operation_name,
                   self.statuses[self.status]))

    #
    # ORMObject hooks
    #

    def delete(self):
        # First call hooks, do this first so the hook
        # have access to everything it needs
        self.method.operation.payment_delete(self)
        # FIXME: BUG 5581 check if it is really safe to remove the payment
        # when using with synced databases
        self.store.remove(self)

    @classmethod
    def create_repeated(cls, store, payment, repeat_type, start_date, end_date):
        """Create a set of repeated payments.
        Given a type of interval (*repeat_type*), a start date and an end_date,
        this creates a list of payments for that interval.

        Note, this will also update the description of the payment that's passed
        in.
        :param store: a store
        :param payment: the payment to repeat
        :param repeat_type: the kind of repetition (weekly, monthly etc)
        :param start_date: the date to start this repetition
        :param end_date: the date to end this repetition
        :returns: a list of repeated payments
        """
        dates = create_date_interval(interval_type=repeat_type,
                                     start_date=start_date,
                                     end_date=end_date)
        n_dates = dates.count()
        if n_dates == 1:
            raise AssertionError
        description = payment.description
        payment.description = u'1/%d %s' % (n_dates, description)
        payment.due_date = dates[0]

        payments = []
        for i, date in enumerate(dates[1:]):
            p = Payment(open_date=payment.open_date,
                        branch=payment.branch,
                        payment_type=payment.payment_type,
                        status=payment.status,
                        description=u'%d/%d %s' % (i + 2, n_dates,
                                                   description),
                        value=payment.value,
                        base_value=payment.base_value,
                        due_date=date,
                        method=payment.method,
                        group=payment.group,
                        category=payment.category,
                        store=store)
            payments.append(p)
        return payments

    #
    # Properties
    #

    @property
    def comments_number(self):
        """The number of |paymentcomments| for this payment"""
        return self.comments.count()

    @property
    def bank_account_number(self):
        """For check payments, the :class:`bank account <BankAccount>` number"""
        # This is used by test_payment_method, and is a convenience
        # property, ideally we should move it to payment operation
        # somehow
        if self.method.method_name == u'check':
            data = self.method.operation.get_check_data_by_payment(self)
            bank_account = data.bank_account
            if bank_account:
                return bank_account.bank_number

    @property
    def installment_number(self):
        payments = self.group.get_valid_payments().order_by(
            Payment.identifier)
        for i, payment in enumerate(payments):
            if self == payment:
                return i + 1

    @property
    def status_str(self):
        """The :obj:`Payment.status` as a translated string"""
        if not self.status in self.statuses:
            raise DatabaseInconsistency('Invalid status for Payment '
                                        'instance, got %d' % self.status)
        return self.statuses[self.status]

    def get_days_late(self):
        """For due payments, the number of days late this payment is

        :returns: the number of days late
        """
        if self.status == Payment.STATUS_PAID:
            return 0

        days_late = localtoday().date() - self.due_date.date()
        if days_late.days < 0:
            return 0

        return days_late.days

    def set_pending(self):
        """Set a :obj:`.STATUS_PREVIEW` payment as :obj:`.STATUS_PENDING`.
        This also means that this is valid payment and its owner
        actually can charge it
        """
        self._check_status(self.STATUS_PREVIEW, u'set_pending')
        self.status = self.STATUS_PENDING

    def set_not_paid(self, change_entry):
        """Set a :obj:`.STATUS_PAID` payment as :obj:`.STATUS_PENDING`.
        This requires clearing paid_date and paid_value

        :param change_entry: a :class:`PaymentChangeHistory` object,
          that will hold the changes information
        """
        self._check_status(self.STATUS_PAID, u'set_not_paid')

        if self.transaction:
            self.transaction.create_reverse()

        change_entry.last_status = self.STATUS_PAID
        change_entry.new_status = self.STATUS_PENDING

        sale = self.group and self.group.sale

        if sale and sale.can_set_not_paid():
            sale.set_not_paid()
        self.status = self.STATUS_PENDING
        self.paid_date = None
        self.paid_value = None

    def pay(self, paid_date=None, paid_value=None,
            source_account=None, destination_account=None,
            account_transaction_number=None):
        """Pay the current payment set its status as :obj:`.STATUS_PAID`

        If this payment belongs to a sale, and all other payments from the sale
        are paid then the sale will be set as paid.
        """
        if self.status != Payment.STATUS_PENDING:
            raise ValueError(_(u"This payment is already paid."))
        self._check_status(self.STATUS_PENDING, u'pay')

        paid_value = paid_value or (self.value - self.discount +
                                    self.interest)
        self.paid_value = paid_value
        self.paid_date = paid_date or TransactionTimestamp()
        self.status = self.STATUS_PAID

        if (self.is_separate_payment() or
            self.method.operation.create_transaction()):
            AccountTransaction.create_from_payment(
                self,
                code=account_transaction_number,
                source_account=source_account,
                destination_account=destination_account)

        sale = self.group and self.group.sale
        if sale:
            sale.create_commission(self)

            # When paying payments of a sale, check if the other payments are
            # paid. If they are, this means you can change the sale status to
            # paid as well.
            if sale.can_set_paid():
                sale.set_paid()

        if self.value == self.paid_value:
            msg = _(u"{method} payment with value {value:.2f} was paid").format(
                method=self.method.method_name,
                value=self.value)
        else:
            msg = _(u"{method} payment with value original value "
                    u"{original_value:.2f} was paid with value "
                    u"{value:.2f}").format(method=self.method.method_name,
                                           original_value=self.value,
                                           value=self.paid_value)
        Event.log(self.store, Event.TYPE_PAYMENT, msg.capitalize())

    def cancel(self, change_entry=None):
        """Cancel the payment, set it's status to :obj:`.STATUS_CANCELLED`
        """
        # TODO Check for till entries here and call cancel_till_entry if
        # it's possible. Bug 2598
        if not self.can_cancel():
            raise StoqlibError(_(u"Invalid status for cancel operation, "
                                 u"got %s") % self.status_str)

        if self.transaction:
            self.transaction.create_reverse()

        old_status = self.status
        self.status = self.STATUS_CANCELLED
        self.cancel_date = TransactionTimestamp()

        if change_entry is not None:
            change_entry.last_status = old_status
            change_entry.new_status = self.status

        msg = _(u"{method} payment with value {value:.2f} was cancelled").format(
            method=self.method.method_name,
            value=self.value)
        Event.log(self.store, Event.TYPE_PAYMENT, msg.capitalize())

    def change_due_date(self, new_due_date):
        """Changes the payment due date.
        :param new_due_date: The new due date for the payment.
        :rtype: datetime.date
        """
        if self.status in [Payment.STATUS_PAID, Payment.STATUS_CANCELLED]:
            raise StoqlibError(_(u"Invalid status for change_due_date operation, "
                                 u"got %s") % self.status_str)
        self.due_date = new_due_date

    def update_value(self, new_value):
        """Update the payment value.

        """
        self.value = new_value

    def can_cancel(self):
        return self.status in (Payment.STATUS_PREVIEW, Payment.STATUS_PENDING,
                               Payment.STATUS_PAID)

    def get_payable_value(self):
        """Returns the calculated payment value with the daily interest.

        Note that the payment group daily_interest must be between 0 and 100.

        :returns: the payable value
        """
        if self.status in [self.STATUS_PREVIEW, self.STATUS_CANCELLED]:
            return self.value
        if self.status in [self.STATUS_PAID, self.STATUS_REVIEWING,
                           self.STATUS_CONFIRMED]:
            return self.paid_value

        return self.value + self.get_interest()

    def get_penalty(self, date=None):
        """Calculate the penalty in an absolute value

        :param date: date of payment
        :returns: penalty
        :rtype: :class:`kiwi.currency.currency`
        """
        if date is None:
            date = localtoday().date()
        elif date < self.open_date.date():
            raise ValueError(_(u"Date can not be less then open date"))
        elif date > localtoday().date():
            raise ValueError(_(u"Date can not be greather then future date"))
        if not self.method.penalty:
            return currency(0)

        # Don't add penalty if we pay in time!
        if self.due_date.date() >= date:
            return currency(0)

        return currency(self.method.penalty / 100 * self.value)

    def get_interest(self, date=None, pay_penalty=True):
        """Calculate the interest in an absolute value

        :param date: date of payment
        :returns: interest
        :rtype: :class:`kiwi.currency.currency`
        """
        if date is None:
            date = localtoday().date()
        elif date < self.open_date.date():
            raise ValueError(_(u"Date can not be less then open date"))
        elif date > localtoday().date():
            raise ValueError(_(u"Date can not be greather then future date"))

        if not self.method.daily_interest:
            return currency(0)

        days = (date - self.due_date.date()).days
        if days <= 0:
            return currency(0)

        base_value = self.value + (pay_penalty and self.get_penalty(date=date))

        return currency(days * self.method.daily_interest / 100 * base_value)

    def has_commission(self):
        """Check if this |payment| already has a |commission|"""
        from stoqlib.domain.commission import Commission
        return self.store.find(Commission,
                               payment=self).any()

    def is_paid(self):
        """Check if the payment is paid.

        :returns: ``True`` if the payment is paid
        """
        return self.status == Payment.STATUS_PAID

    def is_pending(self):
        """Check if the payment is pending.

        :returns: ``True`` if the payment is pending
        """
        return self.status == Payment.STATUS_PENDING

    def is_preview(self):
        """Check if the payment is in preview state

        :returns: ``True`` if the payment is paid
        """
        return self.status == Payment.STATUS_PREVIEW

    def is_cancelled(self):
        """Check if the payment was cancelled.

        :returns: ``True`` if the payment was cancelled
        """
        return self.status == Payment.STATUS_CANCELLED

    def get_paid_date_string(self):
        """Get a paid date string

        :returns: the paid date string or PAID DATE if the payment isn't paid
        """
        if self.paid_date:
            return self.paid_date.date().strftime('%x')
        return _(u'NOT PAID')

    def get_open_date_string(self):
        """Get a open date string

        :returns: the open date string or empty string
        """
        if self.open_date:
            return self.open_date.date().strftime('%x')
        return u""

    def is_inpayment(self):
        """Find out if a payment is :obj:`incoming <.TYPE_IN>`

        :returns: ``True`` if it's incoming
        """
        return self.payment_type == self.TYPE_IN

    def is_outpayment(self):
        """Find out if a payment is :obj:`outgoing <.TYPE_OUT>`

        :returns: ``True`` if it's outgoing
        """
        return self.payment_type == self.TYPE_OUT

    def is_separate_payment(self):
        """Find out if this payment is created separately from a
        sale, purchase or renegotiation
        :returns: ``True`` if it's separate.
        """

        # FIXME: This is a hack, we should rather store a flag
        #        in the database that tells us how the payment was
        #        created.
        group = self.group
        if not group:
            # Should never happen
            return False

        if group.sale:
            return False
        elif group.purchase:
            return False
        elif group._renegotiation:
            return False

        return True

    def is_of_method(self, method_name):
        """Find out if the payment was made with a certain method

        :returns: ``True`` if it's a payment of that method
        """
        return self.method.method_name == method_name


class PaymentChangeHistory(Domain):
    """ A class to hold information about changes to a payment.

    Only one tuple (last_due_date, new_due_date) or (last_status, new_status)
    should be non-null at a time.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/payment_change_history.html>`__
    """

    __storm_table__ = 'payment_change_history'

    payment_id = IdCol()

    #: the changed |payment|
    payment = Reference(payment_id, 'Payment.id')

    #: the reason of the change
    change_reason = UnicodeCol(default=None)

    #: when the changed happened
    change_date = DateTimeCol(default_factory=localnow)

    #: the due date that was set before the changed
    last_due_date = DateTimeCol(default=None)

    #: the due date that was set after changed
    new_due_date = DateTimeCol(default=None)

    #: status before the change
    last_status = EnumCol(allow_none=False, default=Payment.STATUS_PREVIEW)

    #: status after change
    new_status = EnumCol(allow_none=False, default=Payment.STATUS_PREVIEW)
