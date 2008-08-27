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
##
##  Author(s):  Johan Dahlin                <jdahlin@async.com.br>
##
""" Interfaces definition for all domain classes """

from zope.interface import Attribute, Interface

#
# Interfaces
#

class IActive(Interface):
    """It defines if a certain object can be active or not"""

    is_active = Attribute('This attribute defines if the object is active')

    def inactivate():
        """Inactivate an active object"""

    def activate():
        """Activate an inactive object"""

    def get_status_string():
        """Active or Inactive in the specific locale"""

class IContainer(Interface):
    """An objects that holds other objects or items"""

    def add_item(item):
        """Add a persistent or non-persistent item associated with this
        model."""

    def get_items():
        """Get all the items in the container. The result value could be a
        simple python list or an instance which maps to SQL statement.  """

    def remove_item(item):
        """Remove from the list or database the item desired."""



class IDescribable(Interface):
    """It defines that a object can be described through get_description
    method.
    """
    def get_description():
        """ Returns a description that identifies the object """

class ISellable(Interface):
    """ Represents the sellable information of a certain item such a product
    or a service. Note that sellable is not actually a concrete item but
    only its reference as a sellable. Concrete items are created by
    IContainer routines.

    @type status: enum
    @type price: float
    @type description: string
    @type markup: float
    @type cost: float
    @type mas_discount: float
    @type commission: float
    @type on_sale_price: float
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
        """Whether the sellable is available and can be sold.
        @returns: if the item can be sold
        @rtype: boolean
        """

    def is_sold():
        """Whether the sellable is sold.
        @returns: if the item is sold
        @rtype: boolean
        """

    def sell():
        """Sell the sellable"""

    def cancel():
        """Cancel the sellable"""

    def can_sell():
        """Make the object sellable"""

    def get_code_str():
        """Fetches the current code represented as a string.
        @returns: code
        @rtype: string
        """

    def get_short_description():
        """Returns a short description of the current sale
        @returns: description
        @rtype: string
        """

    def get_suggested_markup():
        """Returns the suggested markup for the sellable
        @returns: suggested markup
        @rtype: decimal
        """

    # FIXME: This should be moved to Product as part of #2729
    def get_unit_description():
        """Undocumented"""

    def get_category_description():
        """Returns the sellable category description
        @returns: the category description or an empty string if no category
        was set.
        """

    def get_tax_constant():
        """Returns the tax constant for this sellable.
        If it's unset, return the constant from the category, if any
        @returns: the tax constant or None if unset
        """


class IProduct(Interface):
    """A Product, this is mainly used as a marker.
    """


class IService(Interface):
    """A Service, this is mainly used as a marker.
    """


class IGiftCertificate(Interface):
    """A GiftCertificate, this is mainly used as a marker.
    """


class IStorable(Interface):
    """Storable documentation for a certain product or a sellable item.
    Each storable can have references to many concrete items which will
    be defined by IContainer routines."""

    def increase_stock(quantity, branch):
        """When receiving a product, update the stock reference for this new
        item on a specific branch company.
        @param quantity: amount to increase
        @param branch: an object implement IBranch
        """

    def decrease_stock(quantity, branch):
        """When receiving a product, update the stock reference for the sold item
        this on a specific branch company.
        @param quantity: amount to decrease
        @param branch: an object implement IBranch
        """

    def increase_logic_stock(quantity, branch=None):
        """When receiving a product, update the stock logic quantity
        reference for this new item. If no branch company is supplied,
        update all branches."""

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

    def get_stock_item(branch):
        """Fetch a stock item for a specific branch
        @returns: a stock item
        """

    def get_stock_items():
        """Fetches the stock items available for all branches.
        @returns: a sequence of stock items
        """

    def has_stock_by_branch(branch):
        """Returns True if there is at least one item on stock for the
        given branch or False if not.
        This method also considers the logic stock
        """

class IPersonFacet(Interface):
    """A facet on a Person, the only thing it has is a named reference
    back to the person itself.
    """
    person = Attribute("a Person")

class IPaymentFacet(Interface):
    """A facet on a Payment, the only thing it has is a named reference
    back to the payment itself.
    """
    payment = Attribute("a Payment")

class IIndividual(IPersonFacet):
    """Being or characteristic of a single person, concerning one
    person exclusively

    @type cpf: string
    @type birth_location: integer
    @type occupation: string
    @type martial_status: enum
    @type spouse: Individual
    @type father_name: string
    @type mother_name: string
    @type rg_expedition_local: string
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

    def get_marital_statuses():
        """FIXME"""

    def get_cpf_number():
        """Returns the cpf number without any non-numeric characters
        @returns: the cpf number as a number
        @rtype: integer
        """

class ICompany(IPersonFacet):
    """An institution created to conduct business"""

    cnpj = Attribute('A Brazilian government register number for companies')
    fancy_name = Attribute('The secondary company name')
    state_registry = Attribute('A Brazilian register number associated with '
                               'a certain state')

    def get_cnpj_number():
        """Returns the cnpj number without any non-numeric characters
        @returns: the cnpj number as a number
        @rtype: integer
        """

    def get_state_registry_number():
        """Returns the state registry number without any non-numeric characters
        @returns: the state registry number as a number
        @rtype: integer
        """


class IClient(IPersonFacet):
    """An individual or a company who pays for goods or services"""

    status = Attribute('ok, indebted, insolvent, inactive')
    days_late = Attribute('How many days is this client indebted')

    def get_last_purchase_date():
        """Fetch the date of the last purchased item by this client.
        None is returned if there are no sales yet made by the client

        @returns: the date of the last purchased item
        @rtype: datetime.date or None
        """

    def get_client_sales():
        """Returns a list of sales from a SaleView tied with the
        current client
        """

    def get_name():
        """Name of the client
        """

class ISupplier(IPersonFacet):
    """A company or an individual that produces, provides, or furnishes
    an item or service"""

    product_desc = Attribute('A short description telling which products '
                             'this supplier produces')
    status = Attribute('active, inactive, blocked')

    def get_supplier_purchases():
        """
        Gets a list of PurchaseOrderViews representing all purchases done from
        this supplier.
        @returns: a list of PurchaseOrderViews.
        """


class IEmployee(IPersonFacet):
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

    def get_role_history():
        """FIXME"""

    def get_active_role_history():
        """FIXME"""

class IUser(IPersonFacet):
    """An employee which have access to one or more Stoq applications"""

    username = Attribute('Username')
    profile = Attribute('A profile represents a colection of information '
                        'which represents what this user can do in the '
                        'system')
    password = Attribute('Password')

class IBranch(IPersonFacet):
    """An administrative division of some larger or more complex
    organization"""

    manager = Attribute('An employee which is in charge of this branch')

    def get_active_stations():
        """FIXME"""

    def fetchTIDs(table, timestamp, te_type, trans):
        """Fetches the transaction entries (TIDs) for a specific table which
        were created using this station.

        @param table: table to get objects in
        @param timestamp: since when?
        @param te_type: CREATED or MODIFIED
        @param trans: a transaction
        """

    def fetchTIDsForOtherStations(table, timestamp, te_type, trans):
        """Fetches the transaction entries (TIDs) for a specific table which
        were created using any station except the specified one.

        @param table: table to get objects in
        @param timestamp: since when?
        @param te_type: CREATED or MODIFIED
        @param trans: a transaction
        """

class ISalesPerson(IPersonFacet):
    """An employee in charge of make sales"""

    commission = Attribute('The percentege of commission the company must pay '
                          'for this salesman')
    commission_type = Attribute('A rule used to calculate the amount of '
                               'commission. This is a reference to another '
                               'object')

class IBankBranch(IPersonFacet):
    branch = Attribute('A bank branch definition')

class ICreditProvider(IPersonFacet):
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

class ITransporter(IPersonFacet):
    """An individual or company engaged in the transportation"""

    open_contract_date = Attribute('The date when we start working with '
                                   'this transporter')
    freight_percentage = Attribute('The percentage amount of freight '
                                   'charged by this transporter')

class IInPayment(IPaymentFacet):
    """ Interface specification for InPayments. """

    def receive():
        """ Confirm the payment. """

class IOutPayment(IPaymentFacet):
    """ Interface specification for OutPayments. """

    def pay():
        """ Confirm the payment."""

class IPaymentGroup(Interface):
    """ Interface specification for PaymentGroups. """

    status = Attribute('The status of the payment group. ')
    open_date = Attribute('The open date of the payment group.')
    close_date = Attribute('The close date of the payment group.')
    notes = Attribute('Extra notes for the payment group.')
    payments = Attribute('A list of payments associated to this payment '
                         'group')
    thirdparty = Attribute('The thirdparty associated to this payment group.')


    def get_thirdparty():
        """Return the thirdparty attached to the payment group. It must be
        always a Person instance"""

    def update_thirdparty_status():
        """Verifies if we still have payments in late to be paid and update
        the thirdparty financial status
        """

    def get_group_description():
        """Returns a group description which will be used when building
        descriptions for payments"""

    def get_balance():
        """The total amount of all the payments this payment group holds"""

    def add_payment(value, description, method, destination=None,
                    due_date=None):
        """Add a new payment for this group"""

    def get_total_received():
        """Return the total amount paid by the client (sale total)
        deducted of payment method commissions"""

    def get_default_payment_method():
        """FIXME"""

    def confirm():
        """Validate the current payment group, create payments."""

    def cancel(renegotiation):
        pass

    def can_cancel():
        pass

    def pay(payment):
        """This is an optional hook on the PaymentGroup which is called
        when you pay a payment.
        @param payment: the payment which was paid
        """

class IDelivery(Interface):
    """ Specification of a Delivery interface for a sellable. """

    address = Attribute('The delivery address.')

    def get_item_by_sellable(sellable):
        """Gets all delivery items for a sellable

        @param sellable: a sellable
        @type sellable: ASellable
        @returns: a list of DeliveryItems
        """


class IPaymentDevolution(Interface):
    """A devolution payment operation"""

    def get_devolution_date():
        """Get the day when the payment was returned"""

class IPaymentDeposit(Interface):
    """A deposit payment operation"""

    def get_deposit_date():
        """Get the day when the payment was paid"""

class IReversal(Interface):
    """A financial entry which support reversal operations"""

    def reverse_entry(invoice_number):
        """Takes a financial entry and reverse it, creating a new instance
        with an oposite value
        """

