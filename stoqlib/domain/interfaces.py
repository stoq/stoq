# -*- Mode: Python; coding: iso-8859-1 -*-
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
""" Interfaces definition for all domain classes """

from zope.interface import Attribute

from stoqlib.domain.base import ConnInterface

#
# ConnInterfaces
#

class IContainer(ConnInterface):
    """An objects that holds other objects or items"""

    def add_item(item):
        """Add a persistent or non-persistent item associated with this
        model."""

    def get_items():
        """Get all the items in the container. The result value could be a
        simple python list or an instance which maps to SQL statement.  """

    def remove_items(item):
        """Remove from the list or database the item desired."""

class ISellable(ConnInterface):
    """ Represents the sellable information of a certain item such a product
    or a service. Note that sellable is not actually a concrete item but
    only its reference as a sellable. Concrete items are defined by
    IContainer routines.
    @itype status enum
    @itype price float
    @itype description string
    @itype markup float
    @itype cost float
    @itype mas_discount float
    @itype commission float
    @itype on_sale_price float
    """

    status = Attribute('status the sellable is in')
    price = Attribute('price of sellable')
    description = Attribute('full description of sallable')
    category = Attribute('a reference to category table')
    markup = Attribute('((cost/price)-1)*100')
    cost = Attribute('final cost of sellable')
    max_discount = Attribute('maximum discount allowed')
    commission = Attribute('commission to pay after selling this sellable')

    # If the sellable is on sale, here we have settings for that
    on_sale_price = Attribute('A special price used when we have a '
                              '"on sale" state')
    # Define here the period that this sellabe will be on sale
    on_sale_start_date = Attribute('datetime')
    on_sale_end_date = Attribute('datetime')

    def can_be_sold():
        pass

    def set_sold():
        pass

    def get_price():
        pass

    def add_sellable_item(sale, quantity, price):
        """Adds a new SellableItem instance for this sellable object"""

class IStorable(ConnInterface):
    """Storable documentation for a certain product or a sellable item.
    Each storable can have references to many concrete items which will
    be defined by IContainer routines."""

    def fill_stocks(conn):
        """Fill the stock references of the current product to point to
        stock correct information in all the branches"""

    def increase_stock(quantity, branch=None):
        """When receiving a product, update the stock reference for this new
        item. If no branch company is supplied, update all branches."""

    def increase_logic_stock(quantity, branch=None):
        """When receiving a product, update the stock logic quantity
        reference for this new item. If no branch company is supplied,
        update all branches."""

    def decrease_stock(quantity, branch=None):
        """When selling a product, update the stock reference for the sold
        item. If no branch company is supplied, update all branches."""

    def decrease_logic_stock(quantity, branch=None):
        """When selling a product, update the stock logic reference for the sold
        item. If no branch company is supplied, update all branches."""

    def get_full_balance(branch=None):
        """Return the stock balance for the current product. If a branch
        company is supplied, get the stock balance for this branch,
        otherwise, get the stock balance for all the branches.
        We get also the sum of logic_quantity attributes"""

    def get_logic_balance(branch=None):
        """Return the stock logic balance for the current product. If a branch
        company is supplied, get the stock balance for this branch,
        otherwise, get the stock balance for all the branches."""

    def get_average_stock_price():
        """Average stock price is: SUM(total_cost attribute, StockItem
        object) of all the branches DIVIDED BY SUM(quantity atribute,
        StockReference object)
        """
    def ensure_qty_requested(quantity, branch):
        """Check if the quantity requested in a sale is valid and update the
        stock of the sellable item"""

class IIndividual(ConnInterface):
    """Being or characteristic of a single person, concerning one
    person exclusively

    @itype cpf string
    @itype birth_location integer
    @itype occupation string
    @itype martial_status enum
    @itype spouse Individual
    @itype father_name string
    @itype mother_name string
    @itype rg_expedition_local string
    """

    cpf = Attribute('A Brazilian government register number which allow to '
                    'store credit informations')
    rg_number = Attribute('A Brazilian government register which identify an '
                          'individual')
    birth_location = Attribute('An object which has city, state and country')
    birth_date = Attribute('The date which this individual was born')
    occupation = Attribute('The current job of this individual')
    marital_status = Attribute('single, married, divorced, widowed')
    spouse = Attribute('An individual\'s partner in marriage - also a '
                       'reference to another individual')
    father_name = Attribute('The father of this individual')
    mother_name = Attribute('The mother of this individual')
    rg_expedition_date = Attribute('Expedition date for the Brazilian '
                                   'document')
    rg_expedition_local = Attribute('The local which the Brazilian was made')
    gender = Attribute('gender_male, gender_female')

class ICompany(ConnInterface):
    """An institution created to conduct business"""

    cnpj = Attribute('A Brazilian government register number for companies')
    fancy_name = Attribute('The secondary company name')
    state_registry = Attribute('A Brazilian register number associated with '
                               'a certain state')

class IClient(ConnInterface):
    """An individual or a company who pays for goods or services"""

    status = Attribute('ok, indebted, insolvent, inactive')
    days_late = Attribute('How many days is this client indebted')

class ISupplier(ConnInterface):
    """A company or an individual that produces, provides, or furnishes
    an item or service"""

    product_desc = Attribute('A short description telling which products '
                             'this supplier produces')
    status = Attribute('active, inactive, blocked')

class IEmployee(ConnInterface):
    """An individual who performs work for an employer under a verbal
    or written understanding where the employer gives direction as to
    what tasks are done"""

    admission_date = Attribute('admission_date',
                               'datetime')
    expire_vacation = Attribute('expire_vacation',
                                'datetime')
    salary = Attribute('salary',
                       'float')
    status = Attribute('normal, away, vacation, off')
    registry_number = Attribute('registry_number',
                                'str')
    education_level = Attribute('education_level',
                                'str')
    dependent_person_number = Attribute('dependent_person_number',
                                        'integer')

    # This is Brazil-specif information
    workpermit_data = Attribute('workpermit_data',
                                'WorkPermitData')
    military_data = Attribute('military_data',
                              'MilitaryData')
    voter_data = Attribute('voter_data',
                           'VoterData')
    bank_account  = Attribute('bank_account',
                              'BankAccount')
    role = Attribute('A reference to an employee role object')

class IUser(ConnInterface):
    """An employee which have access to one or more Stoq applications"""

    username = Attribute('Username')
    profile = Attribute('A profile represents a colection of information '
                        'which represents what this user can do in the '
                        'system')
    password = Attribute('Password')

class IBranch(ConnInterface):
    """An administrative division of some larger or more complex
    organization"""

    manager = Attribute('An employee which is in charge of this branch')

class ISalesPerson(ConnInterface):
    """An employee in charge of make sales"""

    commission = Attribute('The percentege of commission the company must pay '
                          'for this salesman')
    commission_type = Attribute('A rule used to calculate the amount of '
                               'commission. This is a reference to another '
                               'object')

class IInPayment(ConnInterface):
    """ ConnInterface specification for InPayments. """

    def receive(value=None, paid_date=None):
        """ Confirm the payment. """

class IOutPayment(ConnInterface):
    """ ConnInterface specification for OutPayments. """

    def pay(value=None, paid_date=None):
        """ Confirm the payment."""

class IPaymentGroup(ConnInterface):
    """ ConnInterface specification for PaymentGroups. """

    status = Attribute('The status of the payment group. ')
    open_date = Attribute('The open date of the payment group.')
    close_date = Attribute('The close date of the payment group.')
    notes = Attribute('Extra notes for the payment group.')
    payments = Attribute('A list of payments associated to this payment '
                         'group')
    thirdparty = Attribute('The thirdparty associated to this payment group.')

    def set_thirdparty(person):
        """Define a new thirdparty. Must of times this is a person adpter
        instance defined by IPaymentGroup adapters. Note that person also
        must implement a facet defined in each adapter"""

    def get_thirdparty():
        """Return the thirdparty attached to the payment group. It must be
        always a Person instance"""

    def get_group_description():
        """Returns a group description which will be used when building
        descriptions for payments"""

    def get_balance():
        """The total amount of all the payments this payment group holds"""

    def add_payment():
        """Add a new payment for this group"""

class IDelivery(ConnInterface):
    """ Specification of a Delivery interface for a sellable. """

    address = Attribute('The delivery address.')

class IMoneyPM(ConnInterface):
    """Defines a money payment method"""

    def get_change():
        """Return the difference between the total amount paid and the total
        sale value
        """

class ICheckPM(ConnInterface):
    """Defines a check payment method"""

    def get_check_data_by_payment(payment):
        """Return a CheckData instance for a certain payment"""

class IBillPM(ConnInterface):
    """Defines a bill payment method"""

    def get_available_bill_accounts():
        """Get all the available bill accounts for the current Bill type"""

class IFinancePM(ConnInterface):
    """Defines a finance payment method"""

    def get_finance_companies():
        """Get all the finance companies for a certain method"""

class ICardPM(ConnInterface):
    """Defines a card payment method"""

    def get_credit_card_providers():
        """Get all the credit providers for a certain method"""

class ITillOperation(ConnInterface):
    """Basic payment operation like adding a credit and a debit"""

    def add_debit(value, reason, category, date=None):
        """Add a payment which represents a debit"""

    def add_credit(value, reason, category, date=None):
        """Add a payment which represents a credit"""

    def add_complement(value, reason, category, date=None):
        """Add a cash value which is a till complement"""

    def get_cash_advance(value, reason, category, employee, date=None):
        """Get the total amount of cash advance"""

    def cancel_payment(payment, reason, date=None):
        """Cancel a payment in the current till"""

class IRenegotiationGiftCertificate(ConnInterface):
    """ A renegotiation information between a sale and a gift certificate.
    When paying a sale through gift certificates it's possible to have
    overpaid values. In this case we have to create a new gift
    certificate with it's value and store here a general information about
    this process.

    @itype status enum
    @itype new_gift_certificate_number string
    @itype overpaid_value float
    """
    new_gift_certificate_number = Attribute('Stores the number of the new '
                                            'gift certificate that will be'
                                            'created')
    overpaid_value = Attribute('The value of the new gift certificate and '
                               'which also represents the overpaid value in '
                               'the sale.')
    status = Attribute('status of the object is in')

    def confirm():
        """Confirm this object means conclude the renegotiation
        process and create a new gift certification with the overpaid value.
        """

class IRenegotiationSaleReturnMoney(ConnInterface):
    """ A renegotiation information between a sale and a gift certificate.
    When paying a sale through gift certificates it's possible to have
    overpaid values. In this case we have to create a new outpayment related
    to the return value and store here a general information about this
    process.

    @itype status enum
    @itype overpaid_value float
    """

    overpaid_value = Attribute('The value of the new outpayment and '
                               'which also represents the overpaid value in '
                               'the sale.')
    status = Attribute('status of the object is in')

    def confirm(payment_group):
        """Confirm this object means conclude the renegotiation
        process and create a new outpayment for the return value.
        """

class IRenegotiationOutstandingValue(ConnInterface):
    """When using gift certificates as a payment method in a sale it's
    possible to have an outstanding value remaining to be paid.
    In this case, objects which implement this interface store information
    about this process.

    @itype status enum
    @itype outstanding_value float
    @itype payment_method int
    """

    outstanding_value = Attribute('The value of the new inpayment and '
                                  'which also represents the outstanding '
                                  'value in the sale.')
    status = Attribute('status of the object is in')
    payment_method = Attribute('The payment method of this renegotiation')

    def confirm(payment_group):
        """Confirm this object means conclude the renegotiation
        process and create a new inpayment.
        """

class IPaymentDevolution(ConnInterface):
    """A devolution payment operation"""

    def get_devolution_date():
        """Get the day when the payment was returned"""

class IPaymentDeposit(ConnInterface):
    """A deposit payment operation"""

    def get_deposit_date():
        """Get the day when the payment was paid"""

class IBankBranch(ConnInterface):
    branch = Attribute('A bank branch definition')

class ICreditProvider(ConnInterface):
    provider_type = Attribute('This attribute must be either'
                              'provider card or provider '
                              'finance')
    short_name  = Attribute('A short description of this provider')
    provider_id = Attribute('An identification for this provider')
    open_contract_date = Attribute('The date when we start working with '
                                   'this provider')

    def get_card_providers(conn):
        """Return a list of credit card providers"""

    def get_finance_companies(conn):
        """Return a list of finance companies"""

class IActive(ConnInterface):
    """It defines if a certain object can be active or not"""

    is_active = Attribute('This attribute defines if the object is active')

    def inactivate():
        """Inactivate an active object"""

    def activate():
        """Activate an inactive object"""

class ITransporter(ConnInterface):
    """An individual or company engaged in the transportation"""

    open_contract_date = Attribute('The date when we start working with '
                                   'this transporter')
    freight_percentage = Attribute('The percentage amount of freight '
                                   'charged by this transporter')

class IDescribable(ConnInterface):
    """It defines that a object can be described through get_description
    method.
    """
    def get_description():
        """ Returns a description that identifies the object """

