# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Person domain classes

The Person domain classes in Stoqlib are special since the :obj:`Person`
class is small and additional functionality is provided through
facets.

There are currently the following person facets available:

  * :obj:`Branch` - a physical location within a company
  * :obj:`Client` - when buying something from a branch
  * :obj:`Company` - a company, tax entitity
  * :obj:`CreditProvider` - provides credit credit, for example via a credit card
  * :obj:`Employee` - works for a branch
  * :obj:`Individual` - a physical person
  * :obj:`LoginUser` - can login and use the system
  * :obj:`SalesPerson` - can sell to clients
  * :obj:`Supplier` - provides product and services to a branch
  * :obj:`Transporter` - transports deliveries to/from a branch

To create a new person, just issue the following::

    >>> from stoqlib.database.runtime import new_transaction
    >>> trans = new_transaction()

    >>> person = Person(name="A new person", connection=trans)

Then to add a client, you can will do:

    >>> client = Client(person=person, connection=trans)

"""

import datetime
import hashlib

from zope.interface import implements

from kiwi.currency import currency

from stoqlib.database.orm import PriceCol, PercentCol, orm_name
from stoqlib.database.orm import (DateTimeCol, UnicodeCol, IntCol,
                                  ForeignKey, MultipleJoin, BoolCol)
from stoqlib.database.orm import const, OR, AND, INNERJOINOn, LEFTJOINOn, Alias
from stoqlib.database.orm import Viewable
from stoqlib.database.runtime import get_current_station
from stoqlib.domain.address import Address
from stoqlib.domain.base import Domain
from stoqlib.domain.event import Event
from stoqlib.domain.interfaces import IDescribable, IActive
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.method import CreditCardData
from stoqlib.domain.sellable import ClientCategoryPrice
from stoqlib.domain.station import BranchStation
from stoqlib.domain.system import TransactionEntry
from stoqlib.domain.profile import UserProfile
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.formatters import raw_phone_number, format_phone_number
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Base Domain Classes
#

class EmployeeRole(Domain):
    """Base class to store the employee roles."""

    implements(IDescribable)

    name = UnicodeCol(alternateID=True)

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def has_other_role(self, name):
        """Check if there is another role with the same name
        :param name: name of the role to check
        :returns: True if it exists, otherwise False
        """
        return self.check_unique_value_exists('name', name,
                                    case_sensitive=False)


# WorkPermitData, MilitaryData, and VoterData are Brazil-specific information.
class WorkPermitData(Domain):
    """Work permit data for employees.

    B{Important Attributes}:
        - I{pis_*}: is a reference to PIS ("Programa de Integracao Social"),
                    that is a Brazil-specific information.
    """

    number = UnicodeCol(default=None)
    series_number = UnicodeCol(default=None)
    pis_number = UnicodeCol(default=None)
    pis_bank = UnicodeCol(default=None)
    pis_registry_date = DateTimeCol(default=None)


class MilitaryData(Domain):
    """ Military data for employees. This is Brazil-specific
    information.
    """

    number = UnicodeCol(default=None)
    series_number = UnicodeCol(default=None)
    category = UnicodeCol(default=None)


class VoterData(Domain):
    """Voter data for employees. This is Brazil-specific information."""

    number = UnicodeCol(default=None)
    section = UnicodeCol(default=None)
    zone = UnicodeCol(default=None)


class Liaison(Domain):
    """Base class to store the person's contact informations."""

    implements(IDescribable)

    name = UnicodeCol(default='')
    phone_number = UnicodeCol(default='')

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    #
    # IDescribable
    #

    def get_description(self):
        return self.name


class Calls(Domain):
    """Person's calls information.

    Calls are information associated to a person(Clients, suppliers,
    employees, etc) that can be financial problems registries,
    collection letters information, some problems with a product
    delivered, etc.
    """

    implements(IDescribable)

    date = DateTimeCol()
    description = UnicodeCol()
    message = UnicodeCol()

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')
    attendant = ForeignKey('LoginUser')

    #
    # IDescribable
    #

    def get_description(self):
        return self.description


class Person(Domain):
    """Base class to register persons in the system. This class should never
    be instantiated directly.
    """
    (ROLE_INDIVIDUAL,
     ROLE_COMPANY) = range(2)

    #: name of the person, depending on the facets, it can either
    #: be something like "John Doe" or "Microsoft Corporation"
    name = UnicodeCol()

    #: phone number for this person
    phone_number = UnicodeCol(default='')

    #: cell/mobile number for this person
    mobile_number = UnicodeCol(default='')

    #: fax number for this person
    fax_number = UnicodeCol(default='')

    #: email address
    email = UnicodeCol(default='')

    #: notes about the client
    notes = UnicodeCol(default='')

    #:
    liaisons = MultipleJoin('Liaison', 'person_id')

    #: list of :obj:`addresses <stoqlib.domain.address.Address>`
    addresses = MultipleJoin('Address', 'person_id')

    #:
    calls = MultipleJoin('Calls', 'person_id')

    @property
    def address(self):
        """The :obj:`address <stoqlib.domain.address.Address>` for this person
        """
        return self.get_main_address()

    #
    # ORMObject setters
    #

    def _set_phone_number(self, value):
        if value is None:
            value = u''
        value = raw_phone_number(value)
        self._SO_set_phone_number(value)

    def _set_fax_number(self, value):
        if value is None:
            value = u''
        value = raw_phone_number(value)
        self._SO_set_fax_number(value)

    def _set_mobile_number(self, value):
        if value is None:
            value = u''
        value = raw_phone_number(value)
        self._SO_set_mobile_number(value)

    #
    # Acessors
    #

    def get_main_address(self):
        """The primary :obj:`address <stoqlib.domain.address.Address>`
        for this person, it normally to be set when the person is entered into
        the system.
        """
        return Address.selectOneBy(personID=self.id, is_main_address=True,
                                   connection=self.get_connection())

    def get_total_addresses(self):
        """The total number of :obj:`addresses <stoqlib.domain.address.Address>`
        for this person

        :returns: the number of addresses
        """
        return Address.selectBy(personID=self.id,
                                connection=self.get_connection()).count()

    def get_address_string(self):
        """The primary :obj:`address <stoqlib.domain.address.Address>`
        for this person formatted as a string.

        :returns: the address
        """
        address = self.get_main_address()
        if not address:
            return u''
        return address.get_address_string()

    def get_phone_number_number(self):
        """Returns the phone number without any non-numeric characters

        :returns: the phone number as a number
        """
        if not self.phone_number:
            return 0
        return int(''.join([c for c in self.phone_number
                                  if c in '1234567890']))

    def get_fax_number_number(self):
        """Returns the fax number without any non-numeric characters

        :returns: the fax number as a number
        """
        if not self.fax_number:
            return 0
        return int(''.join([c for c in self.fax_number
                                  if c in '1234567890']))

    def get_formatted_phone_number(self):
        """
        :returns: a dash-separated phone number or an empty string
        """
        if self.phone_number:
            return format_phone_number(self.phone_number)
        return ""

    def get_formatted_fax_number(self):
        """
        :Returns: a dash-separated fax number or an empty string
        """
        if self.fax_number:
            return format_phone_number(self.fax_number)
        return ""

    #
    # Public API
    #

    def has_individual_or_company_facets(self):
        return self.individual or self.company

    @property
    def branch(self):
        """the :obj:`branch <Branch>` facet for this person"""
        return Branch.selectOneBy(person=self,
                                  connection=self.get_connection())

    @property
    def client(self):
        """the :obj:`client <Client>` facet for this person"""
        return Client.selectOneBy(person=self,
                                  connection=self.get_connection())

    @property
    def company(self):
        """the :obj:`company <Company>` facet for this person"""
        return Company.selectOneBy(person=self,
                                   connection=self.get_connection())

    @property
    def credit_provider(self):
        """the :obj:`credit provider <CreditProvider>` facet for this person"""
        return CreditProvider.selectOneBy(person=self,
                                          connection=self.get_connection())

    @property
    def employee(self):
        """the :obj:`employee <Employee>` facet for this person"""
        return Employee.selectOneBy(person=self,
                                    connection=self.get_connection())

    @property
    def individual(self):
        """the :obj:`individual <Individual>` facet for this person"""
        return Individual.selectOneBy(person=self,
                                      connection=self.get_connection())

    @property
    def login_user(self):
        """the :obj:`login user <LoginUser>` facet for this person"""
        return LoginUser.selectOneBy(person=self,
                                     connection=self.get_connection())

    @property
    def salesperson(self):
        """the :obj:`sales person <SalesPerson>` facet for this person"""
        return SalesPerson.selectOneBy(person=self,
                                       connection=self.get_connection())

    @property
    def supplier(self):
        """the :obj:`supplier <Supplier>` facet for this person"""
        return Supplier.selectOneBy(person=self,
                                    connection=self.get_connection())

    @property
    def transporter(self):
        """the :obj:`transporter <Transporter>` facet for this person"""
        return Transporter.selectOneBy(person=self,
                                       connection=self.get_connection())


class Individual(Domain):
    """Being or characteristic of a single person, concerning one
    person exclusively

    :type birth_location: CityLocation
    :type spouse: Individual
    """

    implements(IActive, IDescribable)

    (STATUS_SINGLE,
     STATUS_MARRIED,
     STATUS_DIVORCED,
     STATUS_WIDOWED,
     STATUS_SEPARATED,
     STATUS_COHABITATION) = range(6)

    marital_statuses = {STATUS_SINGLE: _(u"Single"),
                        STATUS_MARRIED: _(u"Married"),
                        STATUS_DIVORCED: _(u"Divorced"),
                        STATUS_WIDOWED: _(u"Widowed"),
                        STATUS_SEPARATED: _(u'Separated'),
                        STATUS_COHABITATION: _(u'Cohabitation')}

    (GENDER_MALE,
     GENDER_FEMALE) = range(2)

    genders = {GENDER_MALE: _(u'Male'),
               GENDER_FEMALE: _(u'Female')}

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    # FIXME: rename to "document"
    #: the national document used to identify this person.
    cpf = UnicodeCol(default='')

    #: A Brazilian government register which identify an individual
    rg_number = UnicodeCol(default='')

    #: when this individual was born
    birth_date = DateTimeCol(default=None)

    #: current job
    occupation = UnicodeCol(default='')

    #: martial status, single, married, widow etc
    marital_status = IntCol(default=STATUS_SINGLE)

    #: Name of this individuals father
    father_name = UnicodeCol(default='')

    #: Name of this individuals mother
    mother_name = UnicodeCol(default='')

    #: When the rg number was issued
    rg_expedition_date = DateTimeCol(default=None)

    #: Where the rg number was issued
    rg_expedition_local = UnicodeCol(default='')

    #: male or female
    gender = IntCol(default=None)

    #: the name of the spouse individual's partner in marriage
    spouse_name = UnicodeCol(default='')

    #: the :obj:`location <stoqlib.domain.address.CityLocation>` where
    #: individual was born
    birth_location = ForeignKey('CityLocation', default=None)

    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This individual is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This individual is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def get_marital_statuses(self):
        return [(self.marital_statuses[i], i)
                for i in self.marital_statuses.keys()]

    def get_cpf_number(self):
        """Returns the cpf number without any non-numeric characters

        :returns: the cpf number as a number
        """
        if not self.cpf:
            return 0
        return int(''.join([c for c in self.cpf if c in '1234567890']))

    def check_cpf_exists(self, cpf):
        """Returns True if we already have a Individual with the given CPF
        in the database.
        """
        return self.check_unique_value_exists('cpf', cpf)


class Company(Domain):
    """An institution created to conduct business
    """

    implements(IActive, IDescribable)

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    # FIXME: rename to document
    #: a number identifing the company
    cnpj = UnicodeCol(default='')

    #: Doing business as (dba) name for this company, a secondary, non-legal
    #: name of the company.
    fancy_name = UnicodeCol(default='')

    #: Brazilian register number associated with a certain state
    state_registry = UnicodeCol(default='')

    #: Brazilian register number associated with a certain city
    city_registry = UnicodeCol(default='')

    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This company is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This company is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def get_cnpj_number(self):
        """Returns the cnpj number without any non-numeric characters

        :returns: the cnpj number as a number
        """
        if not self.cnpj:
            return 0

        # FIXME: We should return cnpj as strings, since it can begin with 0
        num = ''.join([c for c in self.cnpj if c in '1234567890'])
        if num:
            return int(num)
        return 0

    def get_state_registry_number(self):
        """Returns the state registry number without any non-numeric characters

        :returns: the state registry number as a number or zero if there is
          no state registry.
        """
        if not self.state_registry:
            return 0

        numbers = ''.join([c for c in self.state_registry
                                    if c in '1234567890'])
        return int(numbers or 0)

    def check_cnpj_exists(self, cnpj):
        """Returns True if we already have a Company with the given CNPJ
        in the database.
        """
        return self.check_unique_value_exists('cnpj', cnpj)


class ClientCategory(Domain):
    """I am a client category.
    """

    implements(IDescribable)

    #: name of the category
    name = UnicodeCol(unique=True)

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def can_remove(self):
        """ Check if the client category is used in some product."""
        return not ClientCategoryPrice.selectBy(category=self,
                                            connection=self.get_connection())

    def remove(self):
        """Remove this client category from the database."""
        self.delete(self.id, self.get_connection())


class Client(Domain):
    """An individual or a company who pays for goods or services

    """

    implements(IActive, IDescribable)

    (STATUS_SOLVENT,
     STATUS_INDEBTED,
     STATUS_INSOLVENT,
     STATUS_INACTIVE) = range(4)

    statuses = {STATUS_SOLVENT: _(u'Solvent'),
                STATUS_INDEBTED: _(u'Indebted'),
                STATUS_INSOLVENT: _(u'Insolvent'),
                STATUS_INACTIVE: _(u'Inactive')}

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    #: ok, indebted, insolvent, inactive
    status = IntCol(default=STATUS_SOLVENT)

    #: How many days is this client indebted
    days_late = IntCol(default=0)

    #: How much the user can spend on store credit
    credit_limit = PriceCol(default=0)

    #: the :obj:`client category <ClientCategory>` for this client
    category = ForeignKey('ClientCategory', default=None)

    #
    # IActive
    #

    def get_status_string(self):
        if not self.status in self.statuses:
            raise DatabaseInconsistency('Invalid status for client, '
                                        'got %d' % self.status)
        return self.statuses[self.status]

    def inactivate(self):
        if self.status == Client.STATUS_INACTIVE:
            raise AssertionError('This client is already inactive')
        self.status = self.STATUS_INACTIVE

    def activate(self):
        if self.status == Client.STATUS_SOLVENT:
            raise AssertionError('This client is already active')
        self.status = self.STATUS_SOLVENT

    def _get_is_active(self):
        return self.status == self.STATUS_SOLVENT

    def _set_is_active(self, value):
        if value:
            self.activate()
        else:
            self.inactivate()
    is_active = property(_get_is_active, _set_is_active)

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def get_name(self):
        """Name of the client
        """
        return self.person.name

    @classmethod
    def get_active_clients(cls, conn):
        """Return a list of active clients.
        An active client is a person who are authorized to make new sales
        """
        return cls.select(cls.q.status == cls.STATUS_SOLVENT, connection=conn)

    def get_client_sales(self):
        """Returns a list of :obj:`sale views <stoqlib.domain.sale.SaleView>`
        tied with the current client
        """
        from stoqlib.domain.sale import SaleView
        return SaleView.select(SaleView.q.client_id == self.id,
                               connection=self.get_connection(),
                               orderBy=SaleView.q.open_date)

    def get_client_services(self):
        """Returns a list of sold
        :obj:`service views stoqlib.domain.sale.SoldServicesView>` with
        services consumed by this client
        """
        from stoqlib.domain.sale import SoldServicesView
        return SoldServicesView.select(
            SoldServicesView.q.client_id == self.id,
            connection=self.get_connection(),
            orderBy=SoldServicesView.q.estimated_fix_date)

    def get_client_products(self):
        """Returns a list of products from SoldProductsView with products
        sold to the client
        """
        from stoqlib.domain.sale import SoldProductsView
        return SoldProductsView.select(
            SoldProductsView.q.client_id == self.id,
            connection=self.get_connection(),)

    def get_client_payments(self):
        """Returns a list of payment from InPaymentView with client's payments
        """
        from stoqlib.domain.payment.views import InPaymentView
        return InPaymentView.select(
            InPaymentView.q.person_id == self.personID,
            connection=self.get_connection(),
            orderBy=InPaymentView.q.due_date)

    def get_last_purchase_date(self):
        """Fetch the date of the last purchased item by this client.
        None is returned if there are no sales yet made by the client

        :returns: the date of the last purchased item
        """
        from stoqlib.domain.sale import Sale
        max_date = self.get_client_sales().max(Sale.q.open_date)
        if max_date:
            return max_date.date()

    @property
    def remaining_store_credit(self):
        from stoqlib.domain.payment.views import InPaymentView
        status_query = OR(InPaymentView.q.status == Payment.STATUS_PENDING,
                          InPaymentView.q.status == Payment.STATUS_CONFIRMED)
        query = AND(InPaymentView.q.person_id == self.person.id,
                    status_query,
                    InPaymentView.q.method_name == 'store_credit')

        debit = InPaymentView.select(query,
             connection=self.get_connection()).sum(InPaymentView.q.value) or currency('0.0')

        return currency(self.credit_limit - debit)


class Supplier(Domain):
    """A company or an individual that produces, provides, or furnishes
    an item or service

    """

    implements(IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE,
     STATUS_BLOCKED) = range(3)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive'),
                STATUS_BLOCKED: _(u'Blocked')}

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    #: active/inactive/blocked
    status = IntCol(default=STATUS_ACTIVE)

    #: A short description telling which products this supplier produces
    product_desc = UnicodeCol(default='')

    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This supplier is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This supplier is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def get_name(self):
        """
        :returns: the supplier's name
        """
        return self.person.name

    @classmethod
    def get_active_suppliers(cls, conn):
        query = AND(cls.q.status == cls.STATUS_ACTIVE,
                    cls.q.personID == Person.q.id)
        return cls.select(query, connection=conn, orderBy=Person.q.name)

    def get_supplier_purchases(self):
        """
        Gets a list of PurchaseOrderViews representing all purchases done from
        this supplier.
        :returns: a list of PurchaseOrderViews.
        """
        from stoqlib.domain.purchase import PurchaseOrderView
        return PurchaseOrderView.select(
            # FIXME: should of course use id, fix this
            #        when migrating PurchaseOrderView from views.sql
            PurchaseOrderView.q.supplier_name == self.person.name,
            connection=self.get_connection(),
            orderBy=PurchaseOrderView.q.open_date)

    def get_last_purchase_date(self):
        """Fetch the date of the last purchased item by this supplier.
        None is returned if there are no sales yet made by the client.

        :returns: the date of the last purchased item
        :rtype: datetime.date or None
        """
        orders = self.get_supplier_purchases()
        if orders.count():
            # The get_client_sales method already returns a sorted list of
            # sales by open_date column
            if orm_name == 'storm':
                # pylint: disable=E1101
                return orders.last().open_date.date()
                # pylint: enable=E1101
            else:
                return orders[-1].open_date.date()


class Employee(Domain):
    """An individual who performs work for an employer under a verbal
    or written understanding where the employer gives direction as to
    what tasks are done

    :ivar registry_number:
    :ivar education_level:
    :ivar dependent_person_number:

    :ivar workpermit_data:
    :ivar military_data:
    :ivar voter_data:
    :ivar bank_account:
    """

    implements(IActive, IDescribable)

    (STATUS_NORMAL,
     STATUS_AWAY,
     STATUS_VACATION,
     STATUS_OFF) = range(4)

    statuses = {STATUS_NORMAL: _(u'Normal'),
                STATUS_AWAY: _(u'Away'),
                STATUS_VACATION: _(u'Vacation'),
                STATUS_OFF: _(u'Off')}

    #: normal/away/vacation/off
    status = IntCol(default=STATUS_NORMAL)

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    #: salary for this employee
    salary = PriceCol(default=0)

    #: when this employeer started working for the branch
    admission_date = DateTimeCol(default=None)

    #: when the vaction expires for this employee
    expire_vacation = DateTimeCol(default=None)

    registry_number = UnicodeCol(default=None)
    education_level = UnicodeCol(default=None)
    dependent_person_number = IntCol(default=None)

    #: A reference to an employee role object
    role = ForeignKey('EmployeeRole')
    is_active = BoolCol(default=True)

    # This is Brazil-specific information
    workpermit_data = ForeignKey('WorkPermitData', default=None)
    military_data = ForeignKey('MilitaryData', default=None)
    voter_data = ForeignKey('VoterData', default=None)
    bank_account = ForeignKey('BankAccount', default=None)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This employee is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This employee is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def get_role_history(self):
        return EmployeeRoleHistory.selectBy(
            employee=self,
            connection=self.get_connection())

    def get_active_role_history(self):
        return EmployeeRoleHistory.selectOneBy(
            employee=self,
            is_active=True,
            connection=self.get_connection())

    @classmethod
    def get_active_employees(cls, conn):
        """Return a list of active employees."""
        return cls.select(
            AND(cls.q.status == cls.STATUS_NORMAL,
                cls.q.is_active == True),
                connection=conn)


class LoginUser(Domain):
    """A user that us able to login to the system
    """

    implements(IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    #: username, used to login it to the system
    username = UnicodeCol(alternateID=True)

    #: a hash (md5) for the user password
    pw_hash = UnicodeCol()

    #: A profile represents a colection of information
    #: which represents what this user can do in the system
    profile = ForeignKey('UserProfile')

    is_active = BoolCol(default=True)

    def _create(self, id, **kw):
        if 'password' in kw:
            kw['pw_hash'] = hashlib.md5(kw['password'] or '').hexdigest()
            del kw['password']
        Domain._create(self, id, **kw)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This user is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This user is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    @classmethod
    def get_status_str(self):
        """Returns the status description of a user"""
        if self.is_active:
            return self.statuses[self.STATUS_ACTIVE]
        return self.statuses[self.STATUS_INACTIVE]

    def set_password(self, password):
        """Changes the user password.
        """
        self.pw_hash = hashlib.md5(password or '').hexdigest()

    def login(self):
        station = get_current_station(self.get_connection())
        if station:
            Event.log(Event.TYPE_USER,
                _("User '%s' logged in on '%s'") % (self.username,
                                                    station.name))
        else:
            Event.log(Event.TYPE_USER,
                _("User '%s' logged in") % (self.username, ))

    def logout(self):
        station = get_current_station(self.get_connection())
        if station:
            Event.log(Event.TYPE_USER,
                _("User '%s' logged out from '%s'") % (self.username,
                                                       station.name))
        else:
            Event.log(Event.TYPE_USER,
                _("User '%s' logged out") % (self.username, ))


class Branch(Domain):
    """An administrative division of some larger or more complex
    organization
    """

    implements(IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')

    #: An employee which is in charge of this branch
    manager = ForeignKey('Employee', default=None)
    is_active = BoolCol(default=True)

    #: Brazil specific, "Código de Regime Tributário", one of:
    #:
    #: * Simples Nacional
    #: * Simples Nacional – excesso de sublimite da receita bruta
    #: * Regime Normal
    crt = IntCol(default=1)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This branch is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This branch is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        person = self.person
        return person.company.fancy_name or person.name

    #
    # Public API
    #

    def get_active_stations(self):
        return self.select(
            AND(BranchStation.q.is_active == True,
                BranchStation.q.branchID == self.id),
            connection=self.get_connection())

    def fetchTIDs(self, table, timestamp, te_type, trans):
        """Fetches the transaction entries (TIDs) for a specific table which
        were created using this station.

        :param table: table to get objects in
        :param timestamp: since when?
        :param te_type: CREATED or MODIFIED
        :param trans: a transaction
        """
        if table == TransactionEntry:
            return

        return table.select(
            AND(self._fetchTIDs(table, timestamp, te_type),
                BranchStation.q.branchID == self.id),
            connection=trans)

    def fetchTIDsForOtherStations(self, table, timestamp, te_type, trans):
        """Fetches the transaction entries (TIDs) for a specific table which
        were created using any station except the specified one.

        :param table: table to get objects in
        :param timestamp: since when?
        :param te_type: CREATED or MODIFIED
        :param trans: a transaction
        """
        if table == TransactionEntry:
            return

        return table.select(
            AND(self._fetchTIDs(table, timestamp, te_type),
                BranchStation.q.branchID != self.id),
            connection=trans)

    # Event

    def on_create(self):
        Event.log(Event.TYPE_SYSTEM,
                  _("Created branch '%s'" % (self.person.name, )))

    # Private

    def _fetchTIDs(self, table, timestamp, te_type):
        if te_type == TransactionEntry.CREATED:
            te_id = table.q.te_createdID,
        elif te_type == TransactionEntry.MODIFIED:
            te_id = table.q.te_modifiedID
        else:
            raise TypeError("te_type must be CREATED or MODIFIED")

        return AND(TransactionEntry.q.id == te_id,
                   TransactionEntry.q.station_id == BranchStation.q.id,
                   TransactionEntry.q.te_time > timestamp)

    # Classmethods

    @classmethod
    def get_active_branches(cls, conn):
        return cls.select(cls.q.is_active == True, connection=conn)


class CreditProvider(Domain):
    """A credit provider
     """

    implements(IActive, IDescribable)

    (PROVIDER_CARD, ) = range(1)

    cards_type = {
        CreditCardData.TYPE_CREDIT: 'credit_fee',
        CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE:
                                                'credit_installments_store_fee',
        CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER:
                                             'credit_installments_provider_fee',
        CreditCardData.TYPE_DEBIT: 'debit_fee',
        CreditCardData.TYPE_DEBIT_PRE_DATED: 'debit_pre_dated_fee'
    }

    #: This attribute must be either provider card or provider finance
    provider_types = {PROVIDER_CARD: _(u'Card Provider')}

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')
    is_active = BoolCol(default=True)
    provider_type = IntCol(default=PROVIDER_CARD)

    #: A short description of this provider
    short_name = UnicodeCol()

    #: An identification for this provider
    provider_id = UnicodeCol(default='')

    #: The date when we start working with this provider
    open_contract_date = DateTimeCol()
    closing_day = IntCol(default=10)
    payment_day = IntCol(default=10)
    max_installments = IntCol(default=12)

    #: values charged monthly by the credit provider
    monthly_fee = PriceCol(default=0)

    #: fee applied by the provider for each payment transaction,
    #: depending on the transaction type
    credit_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    credit_installments_store_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    credit_installments_provider_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    debit_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    debit_pre_dated_fee = PercentCol(default=0)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This credit provider is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This credit provider is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    @classmethod
    def get_provider_by_provider_id(cls, provider_id, conn):
        """Get a provider given a provider id string
        :param provider_id: a string representing the provider
        :param conn: a database connection
        """
        return cls.selectBy(is_active=True, provider_type=cls.PROVIDER_CARD,
                            provider_id=provider_id, connection=conn)

    @classmethod
    def get_card_providers(cls, conn):
        """Get a list of all credit card providers.
        :param conn: a database connection
        """
        return cls.selectBy(is_active=True, provider_type=cls.PROVIDER_CARD,
                            connection=conn)

    @classmethod
    def has_card_provider(cls, conn):
        """Find out if there is a card provider
        :param conn: a database connection
        :returns: if there is a card provider
        """
        return bool(cls.selectBy(is_active=True,
                                 provider_type=cls.PROVIDER_CARD,
                                 connection=conn).count())

    @classmethod
    def get_active_providers(cls, conn):
        return cls.select(cls.q.is_active == True, connection=conn)

    def get_fee_for_payment(self, provider, data):
        return getattr(self, provider.cards_type[data.card_type])


class SalesPerson(Domain):
    """An employee in charge of making sales

    :ivar commission: The percentege of commission the company must pay
        for this salesman
    :ivar commission_type: A rule used to calculate the amount of
        commission. This is a reference to another object
    """

    implements(IActive, IDescribable)

    # Not really used right now
    (COMMISSION_GLOBAL,
     COMMISSION_BY_SALESPERSON,
     COMMISSION_BY_SELLABLE,
     COMMISSION_BY_PAYMENT_METHOD,
     COMMISSION_BY_BASE_SELLABLE_CATEGORY,
     COMMISSION_BY_SELLABLE_CATEGORY,
     COMMISSION_BY_SALE_TOTAL) = range(7)

    comission_types = {COMMISSION_GLOBAL: _(u'Globally'),
                       COMMISSION_BY_SALESPERSON: _(u'By Salesperson'),
                       COMMISSION_BY_SELLABLE: _(u'By Sellable'),
                       COMMISSION_BY_PAYMENT_METHOD: _(u'By Payment Method'),
                       COMMISSION_BY_BASE_SELLABLE_CATEGORY: _(u'By Base '
                                                              u'Sellable '
                                                              u'Category'),
                       COMMISSION_BY_SELLABLE_CATEGORY: _(u'By Sellable '
                                                         u'Category'),
                       COMMISSION_BY_SALE_TOTAL: _(u'By Sale Total')}

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')
    comission = PercentCol(default=0)
    comission_type = IntCol(default=COMMISSION_BY_SALESPERSON)
    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This sales person is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This sales person is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    @classmethod
    def get_active_salespersons(cls, conn):
        """Get a list of all active salespersons"""
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)


class Transporter(Domain):
    """An individual or company engaged in the transportation

    :ivar open_contract_date: The date when we start working with
      this transporter
    :ivar freight_percentage: The percentage amount of freight
      charged by this transporter
    """

    implements(IActive, IDescribable)

    #: the :obj:`person <Person>`
    person = ForeignKey('Person')
    is_active = BoolCol(default=True)
    open_contract_date = DateTimeCol(default=datetime.datetime.now)
    #FIXME: not used in purchases.
    freight_percentage = PercentCol(default=0)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This transporter is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This transporter is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    @classmethod
    def get_active_transporters(cls, conn):
        """Get a list of all available transporters"""
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)


class EmployeeRoleHistory(Domain):
    """Base class to store the employee role history."""

    began = DateTimeCol(default=datetime.datetime.now)
    ended = DateTimeCol(default=None)
    salary = PriceCol()
    role = ForeignKey('EmployeeRole')
    employee = ForeignKey('Employee')
    is_active = BoolCol(default=True)

#
# Views
#


class ClientView(Viewable):
    """Stores information about clients.

    Available fields are:
    :attribute id: id of the client table
    :attribute name: client name
    :attribute status: client financial status
    :attribute cpf: brazil-specific cpf attribute
    :attribute rg: brazil-specific rg_number attribute
    :attribute phone_number: client phone_number
    """

    implements(IDescribable)

    columns = dict(
        id=Client.q.id,
        person_id=Person.q.id,
        fancy_name=Company.q.fancy_name,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        status=Client.q.status,
        cnpj=Company.q.cnpj,
        cpf=Individual.q.cpf,
        rg_number=Individual.q.rg_number,
        client_category=ClientCategory.q.name
        )

    joins = [
        INNERJOINOn(None, Person,
                   Person.q.id == Client.q.personID),
        LEFTJOINOn(None, Individual,
                   Person.q.id == Individual.q.personID),
        LEFTJOINOn(None, Company,
                   Person.q.id == Company.q.personID),
        LEFTJOINOn(None, ClientCategory,
                   Client.q.categoryID == ClientCategory.q.id),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name + (self.fancy_name
                            and " (%s)" % self.fancy_name or "")

    #
    # Public API
    #

    @property
    def client(self):
        return Client.get(self.id,
                          connection=self._connection)

    @property
    def cnpj_or_cpf(self):
        return self.cnpj or self.cpf

    @classmethod
    def get_active_clients(cls, conn):
        """Return a list of active clients.
        An active client is a person who are authorized to make new sales
        """
        return cls.select(cls.q.status == Client.STATUS_SOLVENT,
                          connection=conn).orderBy('name')


class EmployeeView(Viewable):

    implements(IDescribable)

    columns = dict(
        id=Employee.q.id,
        person_id=Person.q.id,
        name=Person.q.name,
        role=EmployeeRole.q.name,
        status=Employee.q.status,
        is_active=Employee.q.is_active,
        registry_number=Employee.q.registry_number,
        )

    joins = [
        INNERJOINOn(None, Person,
                   Person.q.id == Employee.q.personID),
        INNERJOINOn(None, EmployeeRole,
                   Employee.q.roleID == EmployeeRole.q.id),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def get_status_string(self):
        return Employee.statuses[self.status]

    @property
    def employee(self):
        return Employee.get(self.id,
                            connection=self.get_connection())

    @classmethod
    def get_active_employees(cls, conn):
        """Return a list of active employees."""
        return cls.select(
            AND(cls.q.status == Employee.STATUS_NORMAL,
                cls.q.is_active == True),
                connection=conn)


class SupplierView(Viewable):

    implements(IDescribable)

    columns = dict(
        id=Supplier.q.id,
        person_id=Person.q.id,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        fancy_name=Company.q.fancy_name,
        cnpj=Company.q.cnpj,
        status=Supplier.q.status,
        )

    joins = [
        INNERJOINOn(None, Person,
                   Person.q.id == Supplier.q.personID),
        LEFTJOINOn(None, Company,
                   Person.q.id == Company.q.personID),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def get_status_string(self):
        return Supplier.statuses[self.status]

    @property
    def supplier(self):
        return Supplier.get(self.id,
                            connection=self.get_connection())


class TransporterView(Viewable):
    """
    Stores information about transporters

    :cvar id: the id of transporter table
    :cvar name: the transporter name
    :cvar phone_number: the transporter phone number
    :cvar person_id: the id of person table
    :cvar status: the current status of the transporter
    :cvar freight_percentage: the freight percentage charged
    """

    implements(IDescribable)

    columns = dict(
        id=Transporter.q.id,
        person_id=Person.q.id,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        freight_percentage=Transporter.q.freight_percentage,
        is_active=Transporter.q.is_active,
        )

    joins = [
        INNERJOINOn(None, Person,
                   Person.q.id == Transporter.q.personID),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    @property
    def transporter(self):
        return Transporter.get(self.id,
                               connection=self.get_connection())


class BranchView(Viewable):
    implements(IDescribable)

    Manager_Person = Alias(Person, 'person_manager')

    columns = dict(
        id=Branch.q.id,
        person_id=Person.q.id,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        is_active=Branch.q.is_active,
        manager_name=Manager_Person.q.name
        )

    joins = [
        INNERJOINOn(None, Person,
                   Person.q.id == Branch.q.personID),
        LEFTJOINOn(None, Employee,
               Branch.q.managerID == Employee.q.id),
        LEFTJOINOn(None, Manager_Person,
               Employee.q.personID == Manager_Person.q.id),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    @property
    def branch(self):
        return Branch.get(self.id,
                          connection=self.get_connection())

    def get_status_str(self):
        if self.is_active:
            return _('Active')

        return _('Inactive')


class UserView(Viewable):
    """
    Retrieves information about user in the system.

    :cvar id: the id of user table
    :cvar name: the user full name
    :cvar is_active: the current status of the transporter
    :cvar username: the username (login)
    :cvar person_id: the id of person table
    :cvar profile_id: the id of the user profile
    :cvar profile_name: the name of the user profile (eg: Salesperson)
    """

    implements(IDescribable)

    columns = dict(
        id=LoginUser.q.id,
        person_id=Person.q.id,
        name=Person.q.name,
        is_active=LoginUser.q.is_active,
        username=LoginUser.q.username,
        profile_id=LoginUser.q.profileID,
        profile_name=UserProfile.q.name,
        )

    joins = [
        INNERJOINOn(None, Person,
                   Person.q.id == LoginUser.q.personID),
        LEFTJOINOn(None, UserProfile,
               LoginUser.q.profileID == UserProfile.q.id),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    @property
    def user(self):
        return LoginUser.get(self.id,
                             connection=self.get_connection())

    def get_status_str(self):
        if self.is_active:
            return _('Active')

        return _('Inactive')


class CreditProviderView(Viewable):

    implements(IDescribable)

    columns = dict(
        id=CreditProvider.q.id,
        person_id=Person.q.id,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        short_name=CreditProvider.q.short_name,
        is_active=CreditProvider.q.is_active,
        credit_fee=CreditProvider.q.credit_fee,
        debit_fee=CreditProvider.q.debit_fee,
        credit_installments_store_fee=CreditProvider.q.credit_installments_store_fee,
        credit_installments_provider_fee=CreditProvider.q.credit_installments_provider_fee,
        debit_pre_dated_fee=CreditProvider.q.debit_pre_dated_fee,
        monthly_fee=CreditProvider.q.monthly_fee
        )

    joins = [
        INNERJOINOn(None, Person,
                   Person.q.id == CreditProvider.q.personID),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    @property
    def provider(self):
        return CreditProvider.get(self.id,
                                  connection=self.get_connection())


class CallsView(Viewable):
    """Store information about the realized calls to client.
    """

    implements(IDescribable)

    Attendant_Person = Alias(Person, 'attendant_person')
    columns = dict(
        id=Calls.q.id,
        person_id=Person.q.id,
        name=Person.q.name,
        date=Calls.q.date,
        description=Calls.q.description,
        message=Calls.q.message,
        attendant=Attendant_Person.q.name,
        )

    joins = [
        LEFTJOINOn(None, Person,
                   Person.q.id == Calls.q.personID),
        LEFTJOINOn(None, LoginUser,
                   LoginUser.q.id == Calls.q.attendantID),
        LEFTJOINOn(None, Attendant_Person,
                   LoginUser.q.personID == Attendant_Person.q.id),
        ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.description

    #
    # Public API
    #

    @property
    def call(self):
        return Calls.get(self.id, connection=self.get_connection())

    @property
    def person(self):
        return Person.get(self.person_id, connection=self.get_connection())

    @classmethod
    def select_by_client_date(cls, query, client, date,
                              having=None, connection=None):
        if client:
            client_query = Calls.q.personID == client.id
            if query:
                query = AND(query, client_query)
            else:
                query = client_query

        if date:
            if isinstance(date, tuple):
                date_query = AND(const.DATE(Calls.q.date) >= date[0],
                                 const.DATE(Calls.q.date) <= date[1])
            else:
                date_query = const.DATE(Calls.q.date) == date

            if query:
                query = AND(query, date_query)
            else:
                query = date_query

        return cls.select(query, having=having, connection=connection)

    @classmethod
    def select_by_date(cls, date, connection):
        return cls.select_by_client_date(None, None, date,
                                         connection=connection)


class ClientCallsView(CallsView):
    joins = CallsView.joins[:]
    joins.append(
        INNERJOINOn(None, Client,
                    Client.q.personID == Person.q.id))
