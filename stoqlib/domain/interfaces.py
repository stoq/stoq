# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Interfaces definition for all domain classes """

from zope.interface import Attribute, Interface

# pylint: disable=E0102,E0211,E0213

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


class IORMObject(Interface):
    id = Attribute("Object ID")

    def delete(obj_id, connection):
        pass


class IStorable(IORMObject):
    """Storable documentation for a certain product or a sellable item.
    Each storable can have references to many concrete items which will
    be defined by IContainer routines."""

    def increase_stock(quantity, branch, cost=None):
        """When receiving a product, update the stock reference for this new
        item on a specific branch company.
        @param quantity: amount to increase
        @param branch: an object implement IBranch
        @param cost: optional parameter indicating the unit cost of the new
                     stock items
        """

    def decrease_stock(quantity, branch):
        """When receiving a product, update the stock reference for the sold item
        this on a specific branch company. Returns the stock item that was
        decreased.
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


class IPaymentFacet(IORMObject):
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

    def check_cpf_exists(cpf):
        """Returns True if we already have a Individual with the given CPF
        in the database.
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

    def check_cnpj_exists(cnpj):
        """Returns True if we already have a Company with the given CNPJ
        in the database.
        """


class IClient(IPersonFacet):
    """An individual or a company who pays for goods or services"""

    status = Attribute('ok, indebted, insolvent, inactive')
    days_late = Attribute('How many days is this client indebted')
    credit_limit = Attribute('How much the user can spend on store credit')

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

    def get_client_services():
        """Returns a list of services from SoldServicesView with services
        consumed by the client
        """

    def get_client_products():
        """Returns a list of products from SoldProductsView with products
        sold to the client
        """

    def get_client_payments():
        """Returns a list of payment from InPaymentView with client's payments
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

    def get_last_purchase_date():
        """Fetch the date of the last purchased item by this supplier.
        None is returned if there are no sales yet made by the client.

        @returns: the date of the last purchased item
        @rtype: datetime.date or None
        """

    def get_name():
        """
        @returns: the supplier's name
        """

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
    bank_account = Attribute('bank_account',
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

    def login():
        pass

    def logout():
        pass


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


class ICreditProvider(IPersonFacet):
    provider_type = Attribute('This attribute must be either'
                              'provider card or provider '
                              'finance')
    short_name = Attribute('A short description of this provider')
    provider_id = Attribute('An identification for this provider')
    open_contract_date = Attribute('The date when we start working with '
                                   'this provider')

    def get_card_providers(conn):
        """Return a list of credit card providers"""

    def get_fee_for_payment(provider, data):
        """Returns the fee value for the payment data provided"""


class ITransporter(IPersonFacet):
    """An individual or company engaged in the transportation"""

    open_contract_date = Attribute('The date when we start working with '
                                   'this transporter')
    freight_percentage = Attribute('The percentage amount of freight '
                                   'charged by this transporter')


class IInPayment(IPaymentFacet):
    """ Interface specification for InPayments. """


class IOutPayment(IPaymentFacet):
    """ Interface specification for OutPayments. """

    def pay():
        """ Confirm the payment."""


class IPaymentTransaction(Interface):
    """ Interface specification for PaymentGroups. """

    def confirm():
        """Transaction is confirmed.
        Payments might occur at this time, in case of money payment,
        others may happen later
        """

    def pay():
        """All payment for this transaction are paid.
        """

    def cancel():
        """Cancels the transaction before it's completed.
        """

    def return_(renegotiation):
        """Returns the goods purchased.
        This means that all paid payments are paid back and
        all pending onces are cancelled.
        Commissions may also reversed.
        @param renegotiation: renegotiation data
        """


class IDelivery(Interface):
    """ Specification of a Delivery interface for a sellable. """

    address = Attribute('The delivery address.')

    def get_item_by_sellable(sellable):
        """Gets all delivery items for a sellable

        @param sellable: a sellable
        @type sellable: Sellable
        @returns: a list of DeliveryItems
        """


class IReversal(Interface):
    """A financial entry which support reversal operations"""

    def reverse_entry(invoice_number):
        """Takes a financial entry and reverse it, creating a new instance
        with an oposite value
        """
