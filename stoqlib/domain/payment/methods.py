# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
##
""" Payment method implementations. """

from decimal import Decimal
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from kiwi.argcheck import argcheck, percent
from kiwi.datatypes import currency
from sqlobject import IntCol, DateTimeCol, ForeignKey, BoolCol
from zope.interface import implements, implementedBy
from zope.interface.interface import InterfaceClass

from stoqlib.database.columns import DecimalCol
from stoqlib.database.runtime import get_connection
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.defaults import calculate_interval, get_all_methods_dict
from stoqlib.domain.sale import SaleAdaptToPaymentGroup
from stoqlib.domain.till import TillAdaptToPaymentGroup, Till
from stoqlib.domain.account import BankAccount
from stoqlib.domain.person import Person
from stoqlib.domain.payment.base import (Payment, PaymentAdaptToInPayment,
                                         AbstractPaymentGroup)
from stoqlib.domain.purchase import PurchaseOrderAdaptToPaymentGroup
from stoqlib.domain.base import (Domain, InheritableModel,
                                 InheritableModelAdapter)
from stoqlib.domain.interfaces import (IInPayment, IMoneyPM, ICheckPM,
                                       IBillPM, IFinancePM, ICardPM,
                                       ICreditProvider, IActive, IOutPayment,
                                       IDescribable, IGiftCertificatePM,
                                       IMultiplePM)
from stoqlib.exceptions import (PaymentError, DatabaseInconsistency,
                                PaymentMethodError)

_ = stoqlib_gettext


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
    interface_method = None

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

    def _get_payment_method_by_interface(self, iface):
        conn = self.get_connection()
        method = sysparam(conn).BASE_PAYMENT_METHOD
        adapter = iface(method, None)
        if adapter is None:
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
                         payment_method, description=None,
                         base_value=None):
        return payment_method.create_inpayment(payment_group, due_date,
                                               value, self, description,
                                               base_value=base_value)

    @argcheck(AbstractPaymentGroup, int, datetime, Decimal)
    def setup_inpayments(self, payment_group, installments_number,
                         first_duedate, total_value):
        """Return a list of newly created inpayments and its total
        payment list.

        payment_group       = a AbstractPaymentGroup instance
        installments_number = the number of installments for payment
                              generation
        first_duedate       = The duedate for the first payment created
        total_value         = the sum of all the payments. Note that payment
                              values are total_value divided by
                              installments_number
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
        - I{monthly_interest}: a percentage that represents the
                               monthly_interest. This value
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
    monthly_interest = DecimalCol(default=0)
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


class PaymentMethod(Domain):
    """A base payment method with its description."""

    def get_total_by_client(self, client):
        raise NotImplementedError('This method must be implemented on child')

    def get_total_by_date(self, start_date=None, end_date=None):
        raise NotImplementedError('This method must be implemented on child')

#
# Adapters for PaymentMethod class
#


# FIXME: Remove Adapter from class name
class AbstractPaymentMethodAdapter(InheritableModelAdapter):
    implements(IActive, IDescribable)

    description = None

    active_editable = True
    is_active = BoolCol(default=True)

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
              PaymentMethodDetails, basestring, InterfaceClass,
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


class PMAdaptToMoneyPM(AbstractPaymentMethodAdapter):
    implements(IMoneyPM, IActive)

    # Money payment method must be always available
    active_editable = False

    description = _(u'Money')
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

    def _create_till_entry(self, total, group):
        from stoqlib.domain.till import TillEntry
        if isinstance(group, SaleAdaptToPaymentGroup):
            till = group.get_adapted().till
        elif isinstance(group, TillAdaptToPaymentGroup):
            till = group.get_adapted()
        elif isinstance(group, PurchaseOrderAdaptToPaymentGroup):
            # Johan 2006-09-28: HACK: No idea if this is correct
            return
        else:
            raise StoqlibError(
                "Invalid Payment group, got %s" % group)

        description = _(u'1/1 %s for %s') % (
            self.description, group.get_group_description())

        TillEntry(description=description,
                  value=total,
                  till=till,
                  payment_group=group,
                  connection=self.get_connection())

    # FIXME: This is absolutely horrible (**kwargs issues)

    def setup_outpayments(self, total, group, *args, **kwargs):
        self._create_till_entry(-abs(total), group)

    def setup_inpayments(self, total, group, *args, **kwargs):
        self._create_till_entry(total, group)

PaymentMethod.registerFacet(PMAdaptToMoneyPM, IMoneyPM)


class PMAdaptToGiftCertificatePM(AbstractPaymentMethodAdapter):
    implements(IGiftCertificatePM, IActive)

    description = _(u'Gift Certificate')

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

PaymentMethod.registerFacet(PMAdaptToGiftCertificatePM, IGiftCertificatePM)


class AbstractCheckBillAdapter(AbstractPaymentMethodAdapter):
    """Base payment method adapter class for for Check and Bill.

    B{Importante attributes}:
        - I{monthly_interest}: a percentage value for the monthly interest.
                               It must always be in the format:
                               0 <= monthly_interest <= 100
    """

    destination = ForeignKey('PaymentDestination')

    max_installments_number = IntCol(default=1)
    monthly_interest = DecimalCol(default=0)
    daily_penalty = DecimalCol(default=0)


    #
    # SQLObject callbacks
    #

    def _set_daily_penalty(self, value):
        percent.value_check("daily_penalty", value)
        self._SO_set_daily_penalty(value)

    def _set_monthly_interest(self, value):
        percent.value_check("monthly_interest", value)
        self._SO_set_monthly_interest(value)

    #
    # General methods
    #

    def _check_interest_value(self, monthly_interest):
        monthly_interest = monthly_interest or Decimal(0)
        if not isinstance(monthly_interest, (int, Decimal)):
            raise TypeError('monthly_interest argument must be integer '
                            'or Decimal, got %s instead'
                            % type(monthly_interest))
        conn = self.get_connection()
        if (sysparam(conn).MANDATORY_INTEREST_CHARGE and
            not monthly_interest == self.monthly_interest):
            raise PaymentError('The monthly_interest charge is mandatory '
                               'for this establishment. Got %s of '
                               'monthly_interest, it should be %s'
                               % (monthly_interest, self.monthly_interest))
        if not (0 <= monthly_interest <= 100):
            raise ValueError("Argument monthly_interest must be "
                             "between 0 and 100, got %s"
                             % monthly_interest)

    @argcheck(Decimal, int, Decimal)
    def _calculate_payment_value(self, total_value, installments_number,
                                monthly_interest=None):
        if not installments_number:
            raise ValueError('The payment_qty argument must be greater '
                             'than zero')
        self._check_installments_number(installments_number)
        self._check_interest_value(monthly_interest)

        if not monthly_interest:
            return total_value / installments_number

        interest_rate = monthly_interest / 100 + 1
        return (total_value / installments_number) * interest_rate

    @argcheck(AbstractPaymentGroup, int, datetime, int, int,
              Decimal, Decimal, InterfaceClass)
    def _setup_payments(self, payment_group, installments_number,
                        first_duedate, interval_type, intervals,
                        total_value, monthly_interest=None,
                        iface=IInPayment):
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
        monthly_interest            = a Decimal instance in the format
                              0 <= monthly_interest <= 100
        """
        value = self._calculate_payment_value(total_value,
                                              installments_number,
                                              monthly_interest)

        if monthly_interest:
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
                          total_value, monthly_interest=None):
        return self._setup_payments(payment_group, installments_number,
                                    first_duedate, interval_type,
                                    intervals, total_value, monthly_interest)

    def setup_outpayments(self, payment_group, installments_number,
                         first_duedate, interval_type, intervals,
                         total_value, monthly_interest=None):
        return self._setup_payments(payment_group, installments_number,
                                    first_duedate, interval_type,
                                    intervals, total_value, monthly_interest,
                                    IOutPayment)

    def get_max_installments_number(self):
        return self.max_installments_number

    def get_check_group_data(self, payment_group):
        return BillCheckGroupData.selectOneBy(
            groupID=payment_group.id,
            connection=self.get_connection())


class PMAdaptToCheckPM(AbstractCheckBillAdapter):
    implements(ICheckPM, IActive)

    description = _(u'Check')

    #
    # ICheckPM implementation
    #

    def get_check_data_by_payment(self, payment):
        """Get an existing CheckData instance from a payment object."""
        return CheckData.selectOneBy(payment=payment,
                                     connection=self.get_connection())

    #
    # Auxiliar methods
    #

    @argcheck(AbstractPaymentGroup, datetime, Decimal,
              PaymentMethodDetails, basestring, InterfaceClass,
              Decimal)
    def add_payment(self, payment_group, due_date, value,
                    method_details=None, description=None,
                    iface=IInPayment, base_value=None):
        # The method_details argument exists only for
        # AbstractCheckBillAdapter compatibility
        desc = description
        payment = AbstractCheckBillAdapter.add_payment(self,
                                                       payment_group,
                                                       due_date, value,
                                                       description=desc,
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

PaymentMethod.registerFacet(PMAdaptToCheckPM, ICheckPM)


class PMAdaptToBillPM(AbstractCheckBillAdapter):
    implements(IBillPM, IActive)

    description = _(u'Bill')

    #
    # IBillPM implementation
    #

    def get_available_bill_accounts(self):
        raise NotImplementedError

PaymentMethod.registerFacet(PMAdaptToBillPM, IBillPM)


class PMAdaptToCardPM(AbstractPaymentMethodAdapter):
    implements(ICardPM, IActive)

    description = _(u'Card')

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

PaymentMethod.registerFacet(PMAdaptToCardPM, ICardPM)


class PMAdaptToFinancePM(AbstractPaymentMethodAdapter):
    implements(IFinancePM, IActive)

    description = _(u'Finance')


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

PaymentMethod.registerFacet(PMAdaptToFinancePM, IFinancePM)


#
# Payment method details
#


class DebitCardDetails(PaymentMethodDetails):
    """Debit card payment method definition."""

    # Lowercases here is for PaymentMethodDetails
    # get_max_installments_number compatibility
    max_installments_number = 1
    description = payment_type_name = _(u'Debit Card')
    interface_method = ICardPM

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
    interface_method = ICardPM

    installment_settings = ForeignKey(u'CardInstallmentSettings')


class CardInstallmentsStoreDetails(PaymentMethodDetails):
    implements(IDescribable)

    payment_type_name = _(u'Installments Store')
    interface_method = ICardPM
    description = _(u'Credit Card')

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
    interface_method = ICardPM
    description = _(u'Credit Card')


    # Lowercases here is for PaymentMethodDetails
    # get_max_installments_number compatibility
    max_installments_number = 1
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
    interface_method = IFinancePM
    description = _(u'Finance')

    receive_days = IntCol(default=1)


#
# General methods
#


def get_active_pm_ifaces():
    """returns a list of payment method interfaces tied with the
    active payment methods
    """
    conn = get_connection()
    methods = AbstractPaymentMethodAdapter.selectBy(is_active=True,
                                                    connection=conn)
    qty = methods.count()
    if not qty:
        raise DatabaseInconsistency("You should have at least one active "
                                    "payment method, got nothing. ")

    all_ifaces = get_all_methods_dict().values()
    all_ifaces.remove(IMultiplePM)
    if qty > len(all_ifaces):
        raise DatabaseInconsistency("You can not have more payment methods "
                                    "them the maximum allowed, which is %d, "
                                    "found %d payment methods"
                                    % (len(all_ifaces), qty))

    ifaces = []
    for pm in methods:
        for iface in implementedBy(type(pm)):
            if not iface in all_ifaces:
                continue
            ifaces.append(iface)
    if not IMoneyPM in ifaces:
        raise DatabaseInconsistency("Money payment method must be"
                                    "always active.")
    return ifaces
