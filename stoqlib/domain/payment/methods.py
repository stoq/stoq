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
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from sqlobject import IntCol, DateTimeCol, ForeignKey, BoolCol
from zope.interface import implements
from zope.interface.interface import InterfaceClass

from stoqlib.database.columns import DecimalCol
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.defaults import calculate_interval, get_all_methods_dict
from stoqlib.domain.till import Till
from stoqlib.domain.account import BankAccount
from stoqlib.domain.person import Person
from stoqlib.domain.payment.payment import (Payment, PaymentAdaptToInPayment,
                                            AbstractPaymentGroup)
from stoqlib.domain.base import (Domain, InheritableModel)
from stoqlib.domain.interfaces import (IInPayment, ICreditProvider,
                                       IActive, IOutPayment,
                                       IDescribable)
from stoqlib.exceptions import (PaymentError, DatabaseInconsistency,
                                PaymentMethodError)

_ = stoqlib_gettext


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
    first_duedate = DateTimeCol(default=datetime.now)
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
    """

    implements(IActive, IDescribable)

    description = None

    active_editable = True
    is_active = BoolCol(default=True)
    daily_penalty = DecimalCol(default=0)
    interest = DecimalCol(default=0)

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
    # Auxiliar methods
    #

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

    def _check_installments_number(self, installments_number, max=None):
        if max is None:
            max = self.get_max_installments_number()
        if installments_number > max:
            raise ValueError(
                'The number of installments can not be greater than %d '
                'for payment method %r' % (max, self))

    def get_payment_number_by_group(self, payment_group):
        return Payment.selectBy(
            groupID=payment_group.id,
            methodID=self.id,
            connection=self.get_connection()).count()

    @argcheck(AbstractPaymentGroup, datetime, Decimal,
              object, basestring, InterfaceClass,
              Decimal)
    def add_payment(self, payment_group, due_date, value,
                    method_details=None, description=None,
                    iface=IInPayment, base_value=None):
        conn = self.get_connection()
        created_number = self.get_payment_number_by_group(payment_group)
        if method_details:
            max = method_details.get_max_installments_number()
            destination = method_details.destination
        else:
            destination = self.destination
            max = self.get_max_installments_number()
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
            group_desc = payment_group.get_group_description()
            description = _(u'1/1 %s for %s') % (self.description,
                                                 group_desc)
        payment = Payment(connection=conn, group=payment_group,
                          method=self, destination=destination,
                          method_details=method_details,
                          due_date=due_date, value=value,
                          base_value=base_value,
                          till=Till.get_current(conn),
                          description=description)
        return payment.addFacet(iface, connection=conn)

    def create_inpayment(self, payment_group, due_date, value,
                         method_details=None, description=None,
                         base_value=None):
        return self.add_payment(payment_group, due_date, value,
                                method_details, description,
                                base_value=base_value)

    def create_outpayment(self, payment_group, due_date, value,
                          method_details=None, description=None):
        return self.add_payment(payment_group, due_date, value,
                                method_details, description,
                                IOutPayment)

    @argcheck(PaymentAdaptToInPayment)
    def delete_inpayment(self, inpayment):
        """Deletes the inpayment and its associated payment.
        Missing a cascade argument in SQLObject ?"""
        conn = self.get_connection()
        payment = inpayment.get_adapted()
        table = Payment.getAdapterClass(IInPayment)
        table.delete(inpayment.id, connection=conn)
        Payment.delete(payment.id, connection=conn)

    def get_max_installments_number(self):
        raise NotImplementedError('This method must be implemented on child')

    def setup_inpayments(self, total, group, installments_number):
        raise NotImplementedError('This method must be implemented on child')

    def setup_outpayments(self, total, group, installments_number):
        raise NotImplementedError('This method must be implemented on child')

    @argcheck(AbstractPaymentGroup)
    def get_thirdparty(self, payment_group):
        """Returns the thirdparty associated with this payment method. If
        the method doesn't have it's own thirdparty the payment_group
        thirdparty will be returned.
        """
        return payment_group.get_thirdparty()


class MoneyPM(APaymentMethod):
    implements(IActive)

    _inheritable = False

    # Money payment method must be always available
    active_editable = False

    destination = ForeignKey('PaymentDestination')

    #
    # Auxiliar method
    #

    def get_max_installments_number(self):
        # Money method supports only one payment
        return 1

    def _setup_payment(self, total, group):
        description = _(u'1/1 %s for %s') % (
            _(u'Money'), group.get_group_description())

        group.add_payment(total, description, self)

    # FIXME: This is absolutely horrible (**kwargs issues)

    def setup_outpayments(self, total, group, *args, **kwargs):
        self._setup_payment(total, group)

    def setup_inpayments(self, total, group, *args, **kwargs):
        self._setup_payment(total, group)

class GiftCertificatePM(APaymentMethod):
    implements(IActive)

    description = _(u'Gift Certificate')

    _inheritable = False

    #
    # General methods
    #

    def _get_new_payment(self, total, group, installments_number):
        self._check_installments_number(installments_number)
        due_date = datetime.today()
        group_desc = group.get_group_description()
        description = _(u'1/1 %s for %s') % (self.description,
                                             group_desc)
        conn = self.get_connection()
        destination = sysparam(conn).DEFAULT_PAYMENT_DESTINATION
        return group.add_payment(total, description, self, destination,
                                 due_date)

    def setup_outpayments(self, total, group, installments_number=None):
        raise NotImplementedError("Not supported by gift certificates")

    def setup_inpayments(self, total, group, installments_number=None):
        installments_number = (installments_number or
                               self.get_max_installments_number())
        payment = self._get_new_payment(total, group, installments_number)
        payment.addFacet(IInPayment, connection=self.get_connection())
        return payment

    def add_payment(self, payment_group, due_date, value,
                    method_details=None, description=None,
                    iface=IInPayment, base_value=None):
        raise NotImplementedError("Not supported by gift certificates")

    def create_inpayment(self, payment_group, due_date, value,
                         method_details=None, description=None,
                         iface=IInPayment, base_value=None):
        raise NotImplementedError("Not supported by gift certificates")

    def create_outpayment(self, payment_group, due_date, value,
                          method_details=None, description=None,
                          iface=IInPayment, base_value=None):
        raise NotImplementedError("Not supported by gift certificates")

    def get_max_installments_number(self):
        # Gift Certificates support exactly one installment
        return 1


class _AbstractCheckBillMethodMixin(object):

    #
    # General methods
    #

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

    @argcheck(Decimal, int, Decimal)
    def _calculate_payment_value(self, total_value, installments_number,
                                interest=None):
        if not installments_number:
            raise ValueError('The payment_qty argument must be greater '
                             'than zero')
        self._check_installments_number(installments_number)
        self._check_interest_value(interest)

        if not interest:
            return total_value / installments_number

        interest_rate = interest / 100 + 1
        return (total_value / installments_number) * interest_rate

    @argcheck(AbstractPaymentGroup, int, datetime, int, int,
              Decimal, Decimal, InterfaceClass)
    def _setup_payments(self, payment_group, installments_number,
                        first_duedate, interval_type, intervals,
                        total_value, interest=None,
                        iface=IInPayment):
        """Return a list of newly created inpayments or outpayments and its
        total interest. The result value is a tuple where the first item
        is the payment list and the second one is the interest total value

        @param payment_group: a AbstractPaymentGroup instance
        @param installments_number: the number of installments for payment
           generation
        @param first_duedate: The duedate for the first payment created
        @param interval_type: a constant which define the interval type used
           to generate payments. See lib/defaults.py, INTERVALTYPE_*
        @param intervals: number of intervals useful to calculate
           payment due dates
        @param total_value: the sum of all the payments. Note that payment
           values are total_value divided by installments_number
        @param interest: a Decimal instance in the format 0 <= interest <= 100
        """
        value = self._calculate_payment_value(total_value,
                                              installments_number,
                                              interest)

        if interest:
            interest_total = value * installments_number - total_value
        else:
            interest_total = Decimal(0)
        payments = []
        calc_interval = calculate_interval(interval_type, intervals)
        group_desc = payment_group.get_group_description()
        for i in range(installments_number):
            due_date = first_duedate + timedelta((i * calc_interval))
            description = _(u'%s/%s %s for %s') % (i + 1,
                                                   installments_number,
                                                   self.description,
                                                   group_desc)
            payment = self.add_payment(payment_group, due_date, value,
                                       description=description,
                                       iface=iface)
            payments.append(payment)

        payments_total = sum([p.get_adapted().value for p in payments],
                             currency(0))
        difference = -(payments_total - interest_total - total_value)
        if difference:
            adapted = payment.get_adapted()
            adapted.value += difference
            adapted.base_value += difference
        return payments, interest_total

    def setup_inpayments(self, payment_group, installments_number,
                          first_duedate, interval_type, intervals,
                          total_value, interest=None):
        return self._setup_payments(payment_group, installments_number,
                                    first_duedate, interval_type,
                                    intervals, total_value, interest)

    def setup_outpayments(self, payment_group, installments_number,
                         first_duedate, interval_type, intervals,
                         total_value, interest=None):
        return self._setup_payments(payment_group, installments_number,
                                    first_duedate, interval_type,
                                    intervals, total_value, interest,
                                    IOutPayment)

    def get_max_installments_number(self):
        return self.max_installments_number

    def get_check_group_data(self, payment_group):
        return BillCheckGroupData.selectOneBy(
            groupID=payment_group.id,
            connection=self.get_connection())


class CheckPM(_AbstractCheckBillMethodMixin, APaymentMethod):
    implements(IActive)

    description = _(u'Check')

    _inheritable = False
    destination = ForeignKey('PaymentDestination')
    max_installments_number = IntCol(default=12)


    def get_check_data_by_payment(self, payment):
        """Get an existing CheckData instance from a payment object."""
        return CheckData.selectOneBy(payment=payment,
                                     connection=self.get_connection())

    #
    # Auxiliar methods
    #

    @argcheck(AbstractPaymentGroup, datetime, Decimal,
              object, basestring, InterfaceClass,
              Decimal)
    def add_payment(self, payment_group, due_date, value,
                    method_details=None, description=None,
                    iface=IInPayment, base_value=None):
        payment = super(CheckPM, self).add_payment(payment_group,
                                                   due_date, value,
                                                   description=description,
                                                   iface=iface,
                                                   base_value=base_value)
        conn = self.get_connection()
        bank_data = BankAccount(connection=conn)
        adapted = payment.get_adapted()
        # Every check must have a check data reference
        CheckData(connection=conn, bank_data=bank_data,
                  payment=adapted)
        return payment

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
    implements(IActive)

    description = _(u'Bill')

    _inheritable = False
    destination = ForeignKey('PaymentDestination')
    max_installments_number = IntCol(default=12)

    def get_available_bill_accounts(self):
        raise NotImplementedError


class CardPM(APaymentMethod):
    implements(IActive)

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
        raise NotImplementedError('This method must be implemented in '
                                  'BasePMProviderInfo classes')


class FinancePM(APaymentMethod):
    implements(IActive)

    description = _(u'Finance')

    _inheritable = False

    def get_thirdparty(self):
        raise NotImplementedError('You should call get_thirdparty method '
                                  'of PaymentMethodDetails instance for '
                                  'this payment method')

    def get_max_installments_number(self):
        raise NotImplementedError('This method mus be implemented in '
                                  'BasePMProviderInfo classes')

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
            return first_duedate + timedelta(self.receive_days)

        if (not (self.installment_settings and
                 self.installment_settings.calculate_payment_duedate)):
            raise ValueError('You must have a valid installment_settings '
                              'attribute set at this point')
        func = self.installment_settings.calculate_payment_duedate
        return func(first_duedate)

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

    def create_inpayment(self, payment_group, due_date, value,
                         payment_method, description=None,
                         base_value=None):
        return payment_method.create_inpayment(payment_group, due_date,
                                               value, self, description,
                                               base_value=base_value)

    @argcheck(AbstractPaymentGroup, int, datetime, Decimal)
    def setup_inpayments(self, payment_group, installments_number,
                         first_duedate, total_value):
        """
        Return a list of newly created inpayments and its total payment list.

        @param payment_group: AbstractPaymentGroup instance
        @param installments_number: the number of installments for payment
           generation
        @param first_duedate: The duedate for the first payment created
        @param total_value: the sum of all the payments. Note that payment
           values are total_value divided by installments_number
        """
        method = self.get_payment_method()
        max = self.get_max_installments_number()
        method._check_installments_number(installments_number, max)

        base_value = total_value / installments_number
        updated_value = total_value * self.commission
        payment_value = updated_value / installments_number

        payments = []
        due_date = first_duedate
        group_desc = payment_group.get_group_description()
        for number in range(installments_number):
            due_date = self.calculate_payment_duedate(due_date)
            description = _(u'%s/%s %s for %s') % (number + 1,
                                                   installments_number,
                                                   self.description,
                                                   group_desc)
            payment = self.create_inpayment(payment_group, due_date,
                                            payment_value, method,
                                            description,
                                            base_value=base_value)
            payments.append(payment)
            due_date += relativedelta(month=+1)
        return payments


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
