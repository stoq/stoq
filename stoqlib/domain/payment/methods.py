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
## Author(s):   Evandro Vale Miquelito     <evandro@async.com.br>
##              Johan Dahlin               <jdahlin@async.com.br>
##
""" Payment method implementations. """

from decimal import Decimal
import datetime

from dateutil.relativedelta import relativedelta
from kiwi.argcheck import argcheck
from sqlobject import IntCol, DateTimeCol, ForeignKey, BoolCol
from stoqdrivers.enum import PaymentMethodType
from zope.interface import implements

from stoqlib.database.columns import DecimalCol
from stoqlib.domain.till import Till
from stoqlib.domain.account import BankAccount
from stoqlib.domain.base import (Domain, InheritableModel)
from stoqlib.domain.interfaces import (IInPayment, ICreditProvider,
                                       IActive, IOutPayment,
                                       IDescribable)
from stoqlib.domain.person import Person
from stoqlib.domain.payment.destination import PaymentDestination
from stoqlib.domain.payment.payment import (Payment, PaymentAdaptToInPayment,
                                            AbstractPaymentGroup)
from stoqlib.exceptions import (PaymentError, DatabaseInconsistency,
                                PaymentMethodError)
from stoqlib.lib.defaults import get_all_methods_dict, quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

PaymentDestination # pyflakes

#
# Domain Classes
#

class CheckData(Domain):
    """Stores check informations and also a history of possible
    devolutions.

    B{Importante attributes}:
        - I{bank_data}: information about the bank account of this check.
        - I{payment}: the payment object.
    """
    payment = ForeignKey('Payment')
    bank_data = ForeignKey('BankAccount')


class BillCheckGroupData(Domain):
    """Stores general information for payment groups which store checks.

    B{Importante attributes}:
        - I{interest}: a percentage that represents the
                       interest. This value
                       must be betwen 0 and 100.
        - I{interval_types}: a useful attribute when generating multiple
                             payments. callsites you ensure to use it
                             properly sending valid constants which define
                             period types for payment generation. All the
                             interval_types constants are at
                             L{stoq.lib.defaults} path.
    """
    installments_number = IntCol(default=1)
    first_duedate = DateTimeCol(default=datetime.datetime.now)
    interest = DecimalCol(default=0)
    interval_type = IntCol(default=None)
    intervals = IntCol(default=1)
    group = ForeignKey('AbstractPaymentGroup')


class CreditProviderGroupData(Domain):
    """Stores general information for payment groups which store methods of
    credit provider such finance, credit card and debit card.
    """
    installments_number = IntCol(default=1)
    # Attribute payment_type is one of the TYPE_* constants defined in
    # BasePMProviderInfo
    payment_type = ForeignKey('PaymentMethodDetails')
    provider = ForeignKey('PersonAdaptToCreditProvider')
    group = ForeignKey('AbstractPaymentGroup')


class CardInstallmentSettings(Domain):
    """General settings for card payment method.

    B{Importante attributes}:
        - I{payment_day}: which day in the month is the credit provider going
                          to pay the store? Usually they pay in the same day
                          every month.
        - I{closing_day}: which day the credit provider stoq counting sales
                          to pay in the payment_day? Sales after this day
                          will be paid only in the next month.
    """
    # Note that payment_day and closing_day can not have a value greater
    # than 28.
    payment_day = IntCol()
    closing_day = IntCol()

    def calculate_payment_duedate(self, first_duedate):
        if first_duedate.day > self.closing_day:
            first_duedate += relativedelta(month=+1)
        return first_duedate.replace(day=self.payment_day)


#
# PaymentMethods
#


class APaymentMethod(InheritableModel):
    """Base payment method adapter class for for Check and Bill.

    B{Importante attributes}:
        - I{interest}: a value for the interest.
                       It must always be in the format:
                       0 <= interest <= 100
        - I{destination}: the suggested destination for the payment when it
                          is paid.
    """

    implements(IActive, IDescribable)

    description = None

    active_editable = True
    is_active = BoolCol(default=True)
    daily_penalty = DecimalCol(default=0)
    interest = DecimalCol(default=0)
    destination = ForeignKey('PaymentDestination', default=None)



    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This provider is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This provider is already active')
        self.active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description

    #
    # Private API
    #

    def _check_installments_number(self, installments_number, max=None):
        if max is None:
            max = self.get_max_installments_number()
        if installments_number > max:
            raise ValueError(
                'The number of installments can not be greater than %d '
                'for payment method %r' % (max, self))

    def _check_interest_value(self, interest):
        interest = interest or Decimal(0)
        if not isinstance(interest, (int, Decimal)):
            raise TypeError('interest argument must be integer '
                            'or Decimal, got %s instead'
                            % type(interest))
        conn = self.get_connection()
        if (sysparam(conn).MANDATORY_INTEREST_CHARGE and
            interest != self.interest):
            raise PaymentError('The interest charge is mandatory '
                               'for this establishment. Got %s of '
                               'interest, it should be %s'
                               % (interest, self.interest))
        if not (0 <= interest <= 100):
            raise ValueError("Argument interest must be "
                             "between 0 and 100, got %s"
                             % interest)

    def _calculate_payment_value(self, total_value, installments_number,
                                iface, interest=None):
        if not installments_number:
            raise ValueError('The payment_qty argument must be greater '
                             'than zero')

        if iface is IInPayment:
            self._check_installments_number(installments_number)

        self._check_interest_value(interest)

        if not interest:
            return total_value / installments_number

        interest_rate = interest / 100 + 1
        return (total_value / installments_number) * interest_rate

    def _create_payment(self, iface, payment_group, value, due_date=None,
                        method_details=None, description=None, base_value=None):
        conn = self.get_connection()
        created_number = self.get_payment_number_by_group(payment_group)

        if due_date is None:
            due_date = datetime.datetime.today()
        if method_details:
            max = method_details.get_max_installments_number()
            destination = method_details.destination
        else:
            destination = self.destination
            max = self.get_max_installments_number()
        if iface is IInPayment:
            if created_number == max:
                raise PaymentMethodError('You can not create more inpayments '
                                         'for this payment group since the '
                                         'maximum allowed for this payment '
                                         'method is %d' % max)
            elif created_number > max:
                raise DatabaseInconsistency('You have more inpayments in '
                                            'database than the maximum '
                                            'allowed for this payment method')
        if not description:
            description = self.describe_payment(payment_group)

        # We only need a till for inpayments
        if iface is IInPayment:
            till = Till.get_current(conn)
        elif iface is IOutPayment:
            till = None
        else:
            raise AssertionError(iface)
        payment = Payment(connection=conn,
                          destination=destination,
                          due_date=due_date,
                          value=value,
                          base_value=base_value,
                          group=payment_group,
                          method=self,
                          method_details=method_details,
                          till=till,
                          description=description)
        facet = payment.addFacet(iface, connection=conn)
        self.after_payment_created(facet)
        return facet

    def _create_payments(self, iface, group, value, due_dates):
        installments = len(due_dates)
        interest = Decimal(0)

        normalized_value = self._calculate_payment_value(
            value, installments, iface, interest)

        normalized_value = quantize(normalized_value)
        if interest:
            interest_total = normalized_value * installments - value
        else:
            interest_total = Decimal(0)

        payments = []
        payments_total = Decimal(0)
        group_desc = group.get_group_description()
        for i, due_date in enumerate(due_dates):
            payment = self._create_payment(iface,
                group, normalized_value, due_date,
                description=self.describe_payment(group, i+1, installments))
            payments.append(payment)
            payments_total += normalized_value

        # Adjust the last payment so it the total will sum up nicely.
        difference = -(payments_total - interest_total - value)
        if difference:
            adapted = payment.get_adapted()
            adapted.value += difference
            adapted.base_value += difference
        return payments

    #
    # Public API
    #

    def describe_payment(self, payment_group, installment=1, installments=1):
        """
        @param payment_group: a L{APaymentGroup}
        @param installment: current installment
        @param installments: total installments
        @returns: a payment description
        """
        assert installment > 0
        assert installments > 0
        assert installments >= installment
        group_desc = payment_group.get_group_description()
        return _(u'1/1 %s for %s') % (self.description, group_desc)

    @argcheck(AbstractPaymentGroup, Decimal, datetime.datetime, object,
              basestring, Decimal)
    def create_inpayment(self, payment_group, value, due_date=None,
                         details=None, description=None,
                         base_value=None):
        """
        Creates a new inpayment
        @param payment_group: a L{APaymentGroup} subclass
        @param value: value of payment
        @param due_date: optional, due date of payment
        @param details: optional
        @param description: optional, description of the payment
        @param base_value: optional
        @returns: a L{PaymentAdaptToInPayment}
        """
        return self._create_payment(IInPayment, payment_group,
                                    value, due_date,
                                    details, description,
                                    base_value)

    @argcheck(AbstractPaymentGroup, Decimal, datetime.datetime, object,
              basestring, Decimal)
    def create_outpayment(self, payment_group, value, due_date=None,
                          details=None, description=None,
                          base_value=None):
        """
        Creates a new outpayment
        @param payment_group: a L{APaymentGroup} subclass
        @param value: value of payment
        @param due_date: optional, due date of payment
        @param details: optional
        @param description: optional, description of the payment
        @param base_value: optional
        @returns: a L{PaymentAdaptToOutPayment}
        """
        return self._create_payment(IOutPayment, payment_group,
                                    value, due_date,
                                    details, description,
                                    base_value)

    @argcheck(AbstractPaymentGroup, Decimal, object)
    def create_inpayments(self, payment_group, value, due_dates):
        """
        Creates a list of new inpayments, the values of the individual
        payments are calculated by taking the value and dividing it by
        the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.
        @param payment_group: a L{APaymentGroup} subclass
        @param value: total value of all payments
        @param due_dates: a list of datetime objects
        @returns: a list of L{PaymentAdaptToInPayment}
        """
        return self._create_payments(IInPayment, payment_group,
                                     value, due_dates)


    @argcheck(AbstractPaymentGroup, Decimal, object)
    def create_outpayments(self, payment_group, value, due_dates):
        """
        Creates a list of new outpayments, the values of the individual
        payments are calculated by taking the value and dividing it by
        the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.
        @param payment_group: a L{APaymentGroup} subclass
        @param value: total value of all payments
        @param due_dates: a list of datetime objects
        @returns: a list of L{PaymentAdaptToOutPayment}
        """
        return self._create_payments(IOutPayment, payment_group,
                                     value, due_dates)

    def get_implemented_iface(self):
        """ Return the payment method interface implemented. If there is more
        than one, raise a ValueError exception -- This should not happens,
        if so, this is a bug.
        """
        res = []
        for iface in get_all_methods_dict().values():
            if iface.providedBy(self):
                res.append(iface)
        if len(res) == 0:
            raise DatabaseInconsistency("The payment method of ID %d doesn't "
                                        "implements a valid payment method "
                                        "interface" % self.id)
        elif len(res) > 1:
            raise DatabaseInconsistency("The payment method of ID %d "
                                        "implements more than one payment "
                                        "method iface (= %r)" % (self, res))
        return res[0]

    @classmethod
    def get_active_methods(cls, conn):
        """Returns a list of payment method interfaces tied with the
        active payment methods
        """
        return APaymentMethod.selectBy(is_active=True, connection=conn)

    @classmethod
    def get_by_enum(cls, conn, enum):
        """
        Returns the Payment method associated with a enum

        @param enum: a PaymentMethodType enum
        @returns: the payment method class
        @type: L{APaymentMethod} instance
        """
        assert isinstance(enum, PaymentMethodType), enum

        if enum == PaymentMethodType.MONEY:
            method_type = MoneyPM
        elif enum == PaymentMethodType.CHECK:
            method_type = CheckPM
        elif enum == PaymentMethodType.BILL:
            method_type = BillPM
        elif enum == PaymentMethodType.FINANCIAL:
            method_type = FinancePM
        elif enum == PaymentMethodType.GIFT_CERTIFICATE:
            method_type = GiftCertificatePM
        else:
            raise ValueError('Invalid payment method, got %r' % (enum,))

        return method_type.selectOne(connection=conn)

    def get_payment_number_by_group(self, payment_group):
        """
        @param payment_group: a L{APaymentGroup} subclass
        @returns:
        """
        return Payment.selectBy(
            groupID=payment_group.id,
            methodID=self.id,
            connection=self.get_connection()).count()

    @argcheck(PaymentAdaptToInPayment)
    def delete_inpayment(self, inpayment):
        """
        Deletes the inpayment and its associated payment.
        Missing a cascade argument in SQLObject ?
        @param inpayment:
        """
        conn = self.get_connection()
        payment = inpayment.get_adapted()
        table = Payment.getAdapterClass(IInPayment)
        table.delete(inpayment.id, connection=conn)
        Payment.delete(payment.id, connection=conn)

    @argcheck(AbstractPaymentGroup)
    def get_thirdparty(self, payment_group):
        """
        @param payment_group: a L{APaymentGroup} subclass
        @returns: the thirdparty associated with this payment method. If
        the method doesn't have it's own thirdparty the payment_group
        thirdparty will be returned.
        """
        return payment_group.get_thirdparty()

    def get_max_installments_number(self):
        raise NotImplementedError('This method must be implemented on child')

    def after_payment_created(self, payment):
        """
        This will be called after a payment has been created, it can be
        used by a subclass to create additional persistent objects
        @param payment: A L{PaymentAdaptToInPayment} or L{PaymentAdaptToOutPayment}
        """

class MoneyPM(APaymentMethod):

    # Money payment method must be always available
    active_editable = False
    description = _(u'Money')

    _inheritable = False

    #
    # Auxiliar method
    #

    def get_max_installments_number(self):
        # Money method supports only one payment
        return 1

class GiftCertificatePM(APaymentMethod):

    description = _(u'Gift Certificate')

    _inheritable = False

    def get_max_installments_number(self):
        # Gift Certificates support exactly one installment
        return 1


class _AbstractCheckBillMethodMixin(object):

    def get_max_installments_number(self):
        return self.max_installments_number

    def get_check_group_data(self, payment_group):
        return BillCheckGroupData.selectOneBy(
            groupID=payment_group.id,
            connection=self.get_connection())


class CheckPM(_AbstractCheckBillMethodMixin, APaymentMethod):

    description = _(u'Check')

    _inheritable = False
    max_installments_number = IntCol(default=12)


    #
    # APaymentMethod
    #

    def after_payment_created(self, payment):
        conn = self.get_connection()
        bank_data = BankAccount(connection=conn)
        # Every check must have a check data reference
        CheckData(connection=conn, bank_data=bank_data,
                  payment=payment.get_adapted())


    #
    # Public API
    #

    def get_check_data_by_payment(self, payment):
        """Get an existing CheckData instance from a payment object."""
        return CheckData.selectOneBy(payment=payment,
                                     connection=self.get_connection())

    @argcheck(PaymentAdaptToInPayment)
    def delete_inpayment(self, inpayment):
        """
        Deletes the inpayment, its associated payment and also the
        check_data object. Missing a cascade argument in SQLObject ?
        """
        conn = self.get_connection()
        payment = inpayment.get_adapted()
        check_data = self.get_check_data_by_payment(payment)
        bank_data = check_data.bank_data
        PaymentAdaptToInPayment.delete(inpayment.id, connection=conn)
        CheckData.delete(check_data.id, connection=conn)
        BankAccount.delete(bank_data.id, connection=conn)
        Payment.delete(payment.id, connection=conn)

class BillPM(_AbstractCheckBillMethodMixin, APaymentMethod):

    description = _(u'Bill')

    _inheritable = False
    max_installments_number = IntCol(default=12)

    def get_available_bill_accounts(self):
        raise NotImplementedError

class CardPM(APaymentMethod):

    description = _(u'Card')

    _inheritable = False

    def get_credit_card_providers(self):
        table = Person.getAdapterClass(ICreditProvider)
        conn = self.get_connection()
        return table.get_card_providers(conn)

    #
    # Auxiliar methods
    #

    def get_thirdparty(self):
        raise NotImplementedError('You should call get_thirdparty method '
                                  'of PaymentMethodDetails instance for '
                                  'this payment method')

    def get_max_installments_number(self):
        # FIXME:
        return 12

class FinancePM(APaymentMethod):

    description = _(u'Finance')

    _inheritable = False

    def get_thirdparty(self):
        raise NotImplementedError(self)

    def get_max_installments_number(self):
        # FIXME:
        return 12

    def get_finance_companies(self):
        table = Person.getAdapterClass(ICreditProvider)
        conn = self.get_connection()
        return table.get_finance_companies(conn)


#
# Payment method details
#


#
# Infrastructure for Payment method Details
#


class PaymentMethodDetails(InheritableModel):
    """.
    B{Important attributes}:
        - I{commission}: a percentage value. Note the percentages in Stoq
                         applications must follow the standard:
                         A discount of 5%    = 0,95.
                         A charge of 3%      = 1,03.
        - I{provider}: the credit provider which is the responsible to pay
                       this payment.
        - I{destination}: the suggested destination for the payment when it
                          is paid.
    """
    implements(IActive, IDescribable)

    payment_type_name = None
    method_type = None

    is_active = BoolCol(default=True)
    commission = DecimalCol(default=0)
    provider = ForeignKey('PersonAdaptToCreditProvider')
    destination = ForeignKey('PaymentDestination')

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This provider is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This provider is already active')
        self.active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable implementation
    #

    @classmethod
    def get_description(cls):
        return cls.description

    #
    # Auxiliar methods
    #

    def get_destination_name(self):
        return self.destination.description

    def get_thirdparty(self):
        return self.provider.get_adapted()

    def calculate_payment_duedate(self, first_duedate):
        if not hasattr(self, 'installment_settings'):
            return first_duedate + datetime.timedelta(self.receive_days)

        if (not (self.installment_settings and
                 self.installment_settings.calculate_payment_duedate)):
            raise ValueError('You must have a valid installment_settings '
                              'attribute set at this point')
        return self.installment_settings.calculate_payment_duedate(
            first_duedate)

    def get_max_installments_number(self):
        return self.max_installments_number

    def get_payment_method(self):
        method_type = self.method_type
        if not method_type:
            raise ValueError('Child must define a interface_method '
                             'attribute')
        method = method_type.selectOne(connection=self.get_connection())
        if method is None:
            raise TypeError('This object must implement interface '
                            '%s' % method_type)
        return method

class DebitCardDetails(PaymentMethodDetails):
    """Debit card payment method definition."""

    # Lowercases here is for PaymentMethodDetails
    # get_max_installments_number compatibility
    max_installments_number = 1
    description = payment_type_name = _(u'Debit Card')
    method_type = CardPM

    _inheritable = False
    receive_days = IntCol()


class CreditCardDetails(PaymentMethodDetails):
    """Credit card payment method definition.

    B{Important attributes}:
        - I{closing_day}: If the due_date.day is greater than closing_day
                          the month will be increased and the next due_date
                          will be the payment_day of the next month.
        - I{payment_day}: The day of the month which the credit provider
                          actually pay the payments.

    Note that closing_day should never be greater than payment_day.
    """

    # Lowercases here is for PaymentMethodDetails
    # get_max_installments_number compatibility
    max_installments_number = 1
    description = payment_type_name = _(u'Credit Card')
    method_type = CardPM

    _inheritable = False
    installment_settings = ForeignKey(u'CardInstallmentSettings')


class CardInstallmentsStoreDetails(PaymentMethodDetails):
    implements(IDescribable)

    payment_type_name = _(u'Installments Store')
    method_type = CardPM
    description = _(u'Credit Card')

    _inheritable = False
    max_installments_number = IntCol(default=1)
    installment_settings = ForeignKey('CardInstallmentSettings')

    #
    # IDescribable implementation
    #

    @classmethod
    def get_description(cls):
        return u'%s - %s' % (cls.description, cls.payment_type_name)


class CardInstallmentsProviderDetails(PaymentMethodDetails):
    implements(IDescribable)

    payment_type_name = _(u'Installments Provider')
    method_type = CardPM
    description = _(u'Credit Card')

    _inheritable = False
    max_installments_number = IntCol(default=12)
    installment_settings = ForeignKey('CardInstallmentSettings')

    #
    # IDescribable implementation
    #

    @classmethod
    def get_description(cls):
        return u'%s - %s' % (cls.description, cls.payment_type_name)


class FinanceDetails(PaymentMethodDetails):
    """finance payment method definition."""

    max_installments_number = 1
    payment_type_names = (_(u'Check'), _(u'Bill'))
    method_type = FinancePM
    description = _(u'Finance')

    _inheritable = False
    receive_days = IntCol(default=1)
