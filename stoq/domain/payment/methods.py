# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito     <evandro@async.com.br>
##
"""
stoq/domain/payment/methods.py:

   Payment method implementations.
"""

import gettext
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from kiwi.argcheck import argcheck
from stoqlib.exceptions import (PaymentError, DatabaseInconsistency,
                                PaymentMethodError)
from sqlobject.sqlbuilder import AND
from sqlobject import (IntCol, DateTimeCol, FloatCol, StringCol, 
                       ForeignKey, BoolCol)
from zope.interface import implements

from stoq.lib.defaults import calculate_interval
from stoq.lib.parameters import sysparam
from stoq.lib.validators import compare_float_numbers
from stoq.domain.account import BankAccount
from stoq.domain.person import Person
from stoq.domain.payment.base import (Payment, PaymentAdaptToInPayment,
                                      AbstractPaymentGroup)
from stoq.domain.base import (Domain, InheritableModel,
                              InheritableModelAdapter)
from stoq.domain.interfaces import (IInPayment, IMoneyPM, ICheckPM, 
                                    IBillPM, IFinancePM, ICardPM, 
                                    ICreditProvider, IActive, IOutPayment)

_ = gettext.gettext

#
# Domain Classes
# 

class CheckData(Domain):
    """Stores check informations and also a history of possible 
    devolutions.
    bank_data   = information about the bank account of this check
    payment   = the payment object
    """
    payment = ForeignKey('Payment')
    bank_data = ForeignKey('BankAccount')


class BillCheckGroupData(Domain):
    """Stores general information for payment groups which store checks. 
    interval_types =  a useful attribute when generating multiple payments.
                      callsites you ensure to use it properly sending valid
                      constants which define period types for payment
                      generation
    """
    installments_number = IntCol(default=1)
    first_duedate = DateTimeCol(default=datetime.now())
    interest = FloatCol(default=0.0)
    interval_type = IntCol(default=None)
    intervals = IntCol(default=1)
    group = ForeignKey('AbstractPaymentGroup')


class CreditProviderGroupData(Domain):
    """Stores general information for payment groups which store methods of
    credit provider such finance, credit card and debit card.
    """
    installments_number = IntCol(default=None)
    # Attribute payment_type is one of the TYPE_* constants defined in
    # BasePMProviderInfo
    payment_type = ForeignKey('PaymentMethodDetails')
    provider = ForeignKey('PersonAdaptToCreditProvider')
    group = ForeignKey('AbstractPaymentGroup')


class CardInstallmentSettings(Domain):
    """General settings for card payment method
    Notes:
        payment_day = which day in the month is the credit provider going to
                      pay the store? Usually they pay in the same day every
                      month.
        closing_day = which day the credit provider stoq counting sales to
                      pay in the payment_day? Sales after this day will be
                      paid only in the next month."""
    # Note that payment_day and closing_day can not have a value greater
    # than 28.
    MAX_DAY_NUMBER = 28
    payment_day = IntCol()
    closing_day = IntCol()

    #
    # SQLObject callbacks
    #

    def _set_payment_day(self, value):
        self._check_max_day_number(value)
        self._SO_set_payment_day(value)

    def _set_closing_day(self, value):
        self._check_max_day_number(value)
        self._SO_set_closing_day(value)

    #
    # Auxiliar methods
    # 

    def _check_max_day_number(self, value):
        if value > self.MAX_DAY_NUMBER:
                raise ValueError('This attribute can not be greater '
                                 'then %d' % self.MAX_DAY_NUMBER)

    def calculate_payment_duedate(self, first_duedate):
        if first_duedate.day > self.closing_day:
            first_duedate += relativedelta(month=+1)
        return first_duedate.replace(day=self.payment_day)


class PaymentMethod(Domain):
    """A base payment method with its description"""

    def get_total_by_client(self, client):
        raise NotImplementedError('This method must be implemented on child')

    def get_total_by_date(self, start_date=None, end_date=None):
        raise NotImplementedError('This method must be implemented on child')


#
# Adapters for PaymentMethod class
#


class PaymentMethodAdapter(InheritableModelAdapter):
    implements(IActive)

    description = None

    is_active = BoolCol(default=True)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This provider is already inactive')
        self.is_active = False

    #
    # Auxiliar methods
    #

    def _check_installments_number(self, installments_number, max=None):
        max = max or self.get_max_installments_number()
        if installments_number > max:
            raise ValueError('The number of installments argument can not '
                             'be greater than %d for method %s' %
                             (max, self.description))
        
    def get_payment_number_by_group(self, payment_group):
        q1 = Payment.q.groupID == payment_group.id
        q2 = Payment.q.methodID == self.id
        query = AND(q1, q2)
        conn = self.get_connection()
        count = Payment.select(query, connection=conn).count()
        return count

    def add_payment(self, payment_group, due_date, value,
                    method_details=None, description=None,
                    iface=IInPayment):
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
            description = '%s (1 of 1) from %s' % (self.description,
                                                   group_desc)
        payment = Payment(connection=conn, group=payment_group,
                          method=self, destination=destination,
                          method_details=method_details,
                          due_date=due_date, value=value,
                          description=description)
        return payment.addFacet(iface, connection=conn)

    def create_inpayment(self, payment_group, due_date, value,
                         method_details=None, description=None):
        return self.add_payment(payment_group, due_date, value,
                                method_details, description)

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


class PMAdaptToMoney(PaymentMethodAdapter):
    implements(IMoneyPM, IActive)

    description = _('Money')
    destination = ForeignKey('PaymentDestination')

    #
    # IMoneyPM implementation
    #
        
    def get_change(self):
        raise NotImplementedError

    #
    # Auxiliar method
    #

    def get_max_installments_number(self):
        # Money method supports only one payment
        return 1

    def _get_new_payment(self, total, group, installments_number):
        self._check_installments_number(installments_number)
        due_date = datetime.today()
        group_desc = group.get_group_description()
        description = '%s (1 of 1) from %s' % (self.description,
                                               group_desc)
        payment = group.add_payment(total, description, self, 
                                    self.destination, due_date)
        return payment

    def setup_outpayments(self, total, group, installments_number):
        total = abs(total) * -1
        payment = self._get_new_payment(total, group, installments_number)
        conn = self.get_connection()
        payment.addFacet(IOutPayment, connection=conn)

    def setup_inpayments(self, total, group, installments_number):
        payment = self._get_new_payment(total, group, installments_number)
        conn = self.get_connection()
        payment.addFacet(IInPayment, connection=conn)

PaymentMethod.registerFacet(PMAdaptToMoney)


class AbstractCheckBillAdapter(PaymentMethodAdapter):
    """Base payment method adapter class for for Check and Bill.
    
        monthly_interest = a percentage value for the monthly interest.
                           It must always be in the format:
                           0 <= monthly_interest <= 100
    """

    destination = ForeignKey('PaymentDestination')

    max_installments_number = IntCol(default=1)
    monthly_interest = FloatCol(default=0.0)
    daily_penalty = FloatCol(default=0.0)

    def _check_interest_value(self, interest):
        interest = interest or 0.0
        if not isinstance(interest, (float, int)):
            raise TypeError('interest argument must be integer '
                            'or float, got %s instead' % type(interest))
        conn = self.get_connection()
        if (sysparam(conn).MANDATORY_INTEREST_CHARGE and 
            not compare_float_numbers(interest, self.monthly_interest)):
            raise PaymentError('The interest charge is mandatory for '
                               'this establishment. Got %s of interest,'
                               'it should be %s' %(interest,
                                                   self.monthly_interest))
        if not (0 <= interest <= 100):
            raise ValueError("Argument interest must be between 0 and 100,"
                             "got %s" % interest)

    def calculate_payment_value(self, total_value, installments_number,
                                monthly_interest):
        if not isinstance(installments_number, int):
            raise TypeError('installments_number argument must be integer '
                            'got %s instead' % type(installments_number))
        if not installments_number:
            raise ValueError('The payment_qty argument must be greater '
                             'than zero')
        self._check_installments_number(installments_number)
        self._check_interest_value(monthly_interest)

        if not monthly_interest:
            return total_value/float(installments_number)

        # The interest value must be calculated per month
        interest = monthly_interest / 100.0

        # XXX Evaluate this code better
        rate = 1 - ((1.0 + interest) ** -installments_number)
        payment_value = total_value * interest / rate
        return payment_value

    # XXX Waiting for bug fix in kiwi
    # @argcheck(object, AbstractPaymentGroup, int, datetime, int, int, 
    #           float)
    def _setup_payments(self, payment_group, installments_number,
                        first_duedate, interval_type, intervals,
                        total_value, interest=None, iface=IInPayment):
        """Return a list of newly created inpayments or outpayments and its 
        total interest. The result value is a tuple where the first item 
        is the payment list and the second one is the interest total value
        
        payment_group       = a AbstractPaymentGroup instance
        installments_number = the number of installments for payment
                              generation
        first_duedate       = The duedate for the first payment created
        interval_type       = a constant which define the interval type used
                              to generate payments. See lib/defaults.py, 
                              INTERVALTYPE_*
        intervals           = number of intervals useful to calculate
                              payment duedates
        total_value         = the sum of all the payments. Note that payment
                              values are total_value divided by
                              installments_number
        interest            = a float value in the format 
                              0 <= interest <= 100
        """
        value = self.calculate_payment_value(total_value,
                                             installments_number,
                                             interest)
        if interest:
            interest_total = value * installments_number - total_value
        else:
            interest_total = 0.0
        conn = self.get_connection()
        payments = []
        calc_interval = calculate_interval(interval_type, intervals)
        group_desc = payment_group.get_group_description()
        for i in range(installments_number):
            due_date = first_duedate + timedelta((i * calc_interval))
            description = '%s (%s of %s) from %s' % (self.description,
                                                     i + 1, 
                                                     installments_number,
                                                     group_desc)
            payment = self.add_payment(payment_group, due_date, value,
                                       description=description, 
                                       iface=iface)
            payments.append(payment)
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
        conn = self.get_connection()
        check_group = BillCheckGroupData.selectBy(groupID=payment_group.id,
                                                  connection=conn)
        count = check_group.count()
        if count == 1:
            return check_group[0]
        elif count > 1:
            raise DatabaseInconsistency('You should have only one check '
                                        'group item, found %d items' %
                                        count)


class PMAdaptToCheck(AbstractCheckBillAdapter):
    implements(ICheckPM, IActive)

    description = _('Check')

    #
    # ICheckPM implementation
    #

    def get_check_data_by_payment(self, payment):
        """Get an existent CheckData instance from a payment object."""
        conn = self.get_connection()
        data = CheckData.selectBy(payment=payment, 
                                  connection=conn)
        count = data.count()
        if count == 1:
            return data[0]
        elif count > 1:
            msg = ('You should have only one CheckData object per payment, '
                   'got %d' % count)
            raise DatabaseInconsistency(msg)

    #
    # Auxiliar methods
    #

    def add_payment(self, payment_group, due_date, value,
                    method_details=None, description=None,
                    iface=IInPayment):
        # The method_details argument exists only for
        # AbstractCheckBillAdapter compatibility
        desc = description
        payment = AbstractCheckBillAdapter.add_payment(self, 
                                                       payment_group, 
                                                       due_date, value,
                                                       description=desc,
                                                       iface=iface)
        conn = self.get_connection()
        bank_data = BankAccount(connection=conn)
        adapted = payment.get_adapted()
        # Every check must have a check data reference
        CheckData(connection=conn, bank_data=bank_data,
                  payment=adapted)
        return payment

    @argcheck(PaymentAdaptToInPayment)
    def delete_inpayment(self, inpayment):
        """Deletes the inpayment, its associated payment and also the
        check_data object. Missing a cascade argument in SQLObject ?"""
        conn = self.get_connection()
        payment = inpayment.get_adapted()
        check_data = self.get_check_data_by_payment(payment)
        bank_data = check_data.bank_data
        PaymentAdaptToInPayment.delete(inpayment.id, connection=conn)
        CheckData.delete(check_data.id, connection=conn)
        BankAccount.delete(bank_data.id, connection=conn)
        Payment.delete(payment.id, connection=conn)

PaymentMethod.registerFacet(PMAdaptToCheck)


class PMAdaptToBill(AbstractCheckBillAdapter):
    implements(IBillPM, IActive)

    description = _('Bill')

    #
    # IBillPM implementation
    #

    def get_available_bill_accounts(self):
        raise NotImplementedError

PaymentMethod.registerFacet(PMAdaptToBill)


class PMAdaptToCard(PaymentMethodAdapter):
    implements(ICardPM, IActive)

    description = _('Card')

    #
    # ICardPM implementation
    #

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

PaymentMethod.registerFacet(PMAdaptToCard)


class PMAdaptToFinance(PaymentMethodAdapter):
    implements(IFinancePM, IActive)

    description = _('Finance')


    def get_thirdparty(self):
        raise NotImplementedError('You should call get_thirdparty method '
                                  'of PaymentMethodDetails instance for '
                                  'this payment method')

    def get_max_installments_number(self):
        raise NotImplementedError('This method mus be implemented in '
                                  'BasePMProviderInfo classes')
    #
    # IFinancePM implementation
    #

    def get_finance_companies(self):
        table = Person.getAdapterClass(ICreditProvider)
        conn = self.get_connection()
        return table.get_finance_companies(conn)

PaymentMethod.registerFacet(PMAdaptToFinance)


#
# Payment method details
#


class PaymentMethodDetails(InheritableModel):
    """
    commission              =   a percentage value. Note the percentages in
                                Stoq applications must follow the standard:
                                A discount of 5%    = 0,95
                                A charge of 3%      = 1,03
    provider        = the credit provider which is the responsible to pay
                      this payment.
    destination     = the suggested destination for the payment when it is
                      paid.
    """
    implements(IActive)
                                
    payment_type_name = None
    interface_method = None

    is_active = BoolCol(default=True)
    commission = FloatCol(default=0.0)
    notes = StringCol(default='')
    provider = ForeignKey('PersonAdaptToCreditProvider')
    destination = ForeignKey('PaymentDestination')

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This provider is already inactive')
        self.is_active = False

    #
    # Auxiliar methods
    #

    def get_thirdparty(self):
        return self.provider.get_adapted()

    def _get_payment_method_by_interface(self, iface):
        conn = self.get_connection()
        method = sysparam(conn).BASE_PAYMENT_METHOD
        adapter = iface(method, connection=conn)
        if not adapter:
            raise TypeError('This object must implement interface '
                            '%s' % iface)
        return adapter

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
        iface = self.interface_method
        if not iface:
            raise ValueError('Child must define a interface_method '
                             'attribute')
        return self._get_payment_method_by_interface(iface)

    def create_inpayment(self, payment_group, due_date, value,
                         payment_method, description=None):
        return payment_method.create_inpayment(payment_group, due_date,
                                               value, self, description)

    @argcheck(AbstractPaymentGroup, int, datetime, float)
    def setup_inpayments(self, payment_group, installments_number,
                         first_duedate, total_value):
        """Return a list of newly created inpayments and its total
        payment list and the second one is the interest total value
        
        payment_group       = a AbstractPaymentGroup instance
        installments_number = the number of installments for payment
                              generation
        first_duedate       = The duedate for the first payment created
        total_value         = the sum of all the payments. Note that payment
                              values are total_value divided by
                              installments_number
        """
        conn = self.get_connection()
        method = self.get_payment_method()
        max = self.get_max_installments_number()
        method._check_installments_number(installments_number, max)

        total_value = total_value * self.commission
        payment_value = total_value / installments_number
        payment_precision = sysparam(conn).PAYMENT_PRECISION
        payment_value = round(payment_value, payment_precision)

        payments = []
        due_date = first_duedate
        group_desc = payment_group.get_group_description()
        for number in range(installments_number):
            due_date = self.calculate_payment_duedate(due_date)
            description = '%s (%s of %s) from %s' % (self.description,
                                                     number, 
                                                     installments_number,
                                                     group_desc)
            payment = self.create_inpayment(payment_group, due_date, 
                                            payment_value, method,
                                            description)
            payments.append(payment)
            due_date += relativedelta(month=+1)
        return payments


class DebitCardDetails(PaymentMethodDetails):
    """Debit card payment method definition."""

    # Lowercases here is for PaymentMethodDetails
    # get_max_installments_number compatibility
    max_installments_number = 1
    description = payment_type_name = _('Debit Card')
    interface_method = ICardPM

    receive_days = IntCol()


class CreditCardDetails(PaymentMethodDetails):
    """Credit card payment method definition.
    
    Information about some attributes:
        closing_day     =   If the due_date.day is greater than closing_day
                            the month will be increased and the next
                            due_date will be the payment_day of the next
                            month.
        payment_day     =   The day of the month which the credit provider
                            actually pay the payments.

        Note that closing_day should never be greater than payment_day.
    """

    # Lowercases here is for PaymentMethodDetails
    # get_max_installments_number compatibility
    max_installments_number = 1
    description = payment_type_name = _('Credit Card')
    interface_method = ICardPM

    installment_settings = ForeignKey('CardInstallmentSettings')


class CardInstallmentsStoreDetails(PaymentMethodDetails):
    payment_type_name = _('Installments Store')
    interface_method = ICardPM
    description = _('Credit Card')

    max_installments_number = IntCol(default=1)
    installment_settings = ForeignKey('CardInstallmentSettings')


class CardInstallmentsProviderDetails(PaymentMethodDetails):
    payment_type_name = _('Installments Provider')
    interface_method = ICardPM
    description = _('Credit Card')
    

    # Lowercases here is for PaymentMethodDetails
    # get_max_installments_number compatibility
    max_installments_number = 1
    installment_settings = ForeignKey('CardInstallmentSettings')


class FinanceDetails(PaymentMethodDetails):
    """finance payment method definition."""

    max_installments_number = 1
    payment_type_names = (_('Check'), _('Bill'))
    interface_method = IFinancePM
    description = _('Finance')

    receive_days = IntCol()
