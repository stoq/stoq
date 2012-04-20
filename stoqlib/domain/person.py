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

The Person domain classes in Stoqlib are special since the normal Person
class is very small and additional functionality is provided through
facets (adapters).

There are currently the following Person facets available:

  - Branch
  - Client
  - Company
  - CreditProvider
  - Employee
  - Individual
  - LoginUser
  - SalesPerson
  - Supplier
  - Transporter

To create a new person, just issue the following:

    >>> from stoqlib.database.runtime import new_transaction
    >>> trans = new_transaction()

    >>> person = Person(name="A new person", connection=trans)

"""

import datetime
import hashlib

from zope.interface import implements

from kiwi.datatypes import currency

from stoqlib.database.orm import PriceCol, PercentCol
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

    _inheritable = False
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

    name = UnicodeCol()
    phone_number = UnicodeCol(default='')
    mobile_number = UnicodeCol(default='')
    fax_number = UnicodeCol(default='')
    email = UnicodeCol(default='')
    notes = UnicodeCol(default='')
    liaisons = MultipleJoin('Liaison')
    addresses = MultipleJoin('Address')
    calls = MultipleJoin('Calls')

    @property
    def address(self):
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
        return Address.selectOneBy(personID=self.id, is_main_address=True,
                                   connection=self.get_connection())

    def get_total_addresses(self):
        return Address.selectBy(personID=self.id,
                                connection=self.get_connection()).count()

    def get_address_string(self):
        address = self.get_main_address()
        if not address:
            return u''
        return address.get_address_string()

    def get_phone_number_number(self):
        """Returns the phone number without any non-numeric characters
        :returns: the phone number as a number
        :rtype: integer
        """
        if not self.phone_number:
            return 0
        return int(''.join([c for c in self.phone_number
                                  if c in '1234567890']))

    def get_fax_number_number(self):
        """Returns the fax number without any non-numeric characters
        :returns: the fax number as a number
        :rtype: integer
        """
        if not self.fax_number:
            return 0
        return int(''.join([c for c in self.fax_number
                                  if c in '1234567890']))

    def get_formatted_phone_number(self):
        """Returns a dash-separated phone number or an empty string
        """
        if self.phone_number:
            return format_phone_number(self.phone_number)
        return ""

    def get_formatted_fax_number(self):
        """Returns a dash-separated fax number or an empty string
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
        return Branch.selectOneBy(person=self,
                                  connection=self.get_connection())

    @property
    def client(self):
        return Client.selectOneBy(person=self,
                                  connection=self.get_connection())

    @property
    def company(self):
        return Company.selectOneBy(person=self,
                                   connection=self.get_connection())

    @property
    def credit_provider(self):
        return CreditProvider.selectOneBy(person=self,
                                          connection=self.get_connection())

    @property
    def employee(self):
        return Employee.selectOneBy(person=self,
                                    connection=self.get_connection())

    @property
    def individual(self):
        return Individual.selectOneBy(person=self,
                                      connection=self.get_connection())

    @property
    def login_user(self):
        return LoginUser.selectOneBy(person=self,
                                     connection=self.get_connection())

    @property
    def salesperson(self):
        return SalesPerson.selectOneBy(person=self,
                                       connection=self.get_connection())

    @property
    def supplier(self):
        return Supplier.selectOneBy(person=self,
                                    connection=self.get_connection())

    @property
    def transporter(self):
        return Transporter.selectOneBy(person=self,
                                       connection=self.get_connection())


class Individual(Domain):
    """Being or characteristic of a single person, concerning one
    person exclusively

    :ivar cpf: a number identifiyng the individual for tax reasons
    :type cpf: string
    :ivar rg_number: A Brazilian government register which identify an
      individual
    :ivar birth_location: where the individual was born
    :type birth_location: CityLocation
    :ivar occupation: The current job
    :type occupation: string
    :ivar martial_status: single, married, divored or widowed
    :type martial_status: enum
    :ivar spouse: An individual's partner in marriage - also a
       reference to another individual
    :type spouse: Individual
    :ivar father_name: Name of this individuals father
    :type father_name: string
    :ivar father_name: Name of this individuals mother
    :type mother_name: string
    :ivar rg_expedition_date: When the rg number was issued
    :type rg_expedition_date: datetime
    :ivar rg_expedition_date: Where the rg number was issued
    :type rg_expedition_local: string
    :ivar gender: male or female
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

    person = ForeignKey('Person')
    cpf = UnicodeCol(default='')
    rg_number = UnicodeCol(default='')
    birth_date = DateTimeCol(default=None)
    occupation = UnicodeCol(default='')
    marital_status = IntCol(default=STATUS_SINGLE)
    father_name = UnicodeCol(default='')
    mother_name = UnicodeCol(default='')
    rg_expedition_date = DateTimeCol(default=None)
    rg_expedition_local = UnicodeCol(default='')
    gender = IntCol(default=None)
    spouse_name = UnicodeCol(default='')
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
        :rtype: integer
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

    :ivar cnpj: a number identifing the company
    :ivar fancy_name:  The secondary company name
    :ivar state_registry: Brazilian register number associated with
       a certain state
    """

    implements(IActive, IDescribable)

    person = ForeignKey('Person')
    # Cnpj, state_registry and city registry are
    # Brazil-specific information.
    cnpj = UnicodeCol(default='')
    fancy_name = UnicodeCol(default='')
    state_registry = UnicodeCol(default='')
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

    def get_cnpj_number(self):
        """Returns the cnpj number without any non-numeric characters
        :returns: the cnpj number as a number
        :rtype: integer
        """
        # FIXME: We should return cnpj as strings, since it can begin with 0
        num = ''.join([c for c in self.cnpj if c in '1234567890'])
        if num:
            return int(num)
        return 0

    def get_state_registry_number(self):
        """Returns the state registry number without any non-numeric characters
        :returns: the state registry number as a number or zero if there is
                  no state registry.
        :rtype: integer
        """
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
    I contain a name
    :attribute name: category name
    """

    implements(IDescribable)

    name = UnicodeCol(unique=True)

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    def can_remove(self):
        """ Check if the client category is used in some product."""
        return not ClientCategoryPrice.selectBy(category=self,
                                            connection=self.get_connection())

    def remove(self):
        """Remove this client category from the database."""
        self.delete(self.id, self.get_connection())


class Client(Domain):
    """An individual or a company who pays for goods or services

    :ivar status: ok, indebted, insolvent, inactive
    :ivar days_late: How many days is this client indebted
    :ivar credit_limit: How much the user can spend on store credit
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

    person = ForeignKey('Person')
    status = IntCol(default=STATUS_SOLVENT)
    days_late = IntCol(default=0)
    credit_limit = PriceCol(default=0)
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
        """Returns a list of sales from a SaleView tied with the
        current client
        """
        from stoqlib.domain.sale import SaleView
        return SaleView.select(SaleView.q.client_id == self.id,
                               connection=self.get_connection(),
                               orderBy=SaleView.q.open_date)

    def get_client_services(self):
        """Returns a list of services from SoldServicesView with services
        consumed by the client
        """
        from stoqlib.domain.sale import SoldServicesView
        return SoldServicesView.select(SoldServicesView.q.client_id == self.id,
                               connection=self.get_connection(),
                               orderBy=SoldServicesView.q.estimated_fix_date)

    def get_client_products(self):
        """Returns a list of products from SoldProductsView with products
        sold to the client
        """
        from stoqlib.domain.sale import SoldProductsView
        return SoldProductsView.select(SoldProductsView.q.client_id == self.id,
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
        :rtype: datetime.date or None
        """
        max_date = self.get_client_sales().max('open_date')
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
             connection=self.get_connection()).sum('value') or currency('0.0')

        return currency(self.credit_limit - debit)


class Supplier(Domain):
    """A company or an individual that produces, provides, or furnishes
    an item or service

    :ivar product_desc: A short description telling which products
        this supplier produces')
    :ivar status: active/inactive/blocked
    :ivar product_desc: Basic description of the products of a supplier.
    """

    implements(IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE,
     STATUS_BLOCKED) = range(3)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive'),
                STATUS_BLOCKED: _(u'Blocked')}

    person = ForeignKey('Person')
    status = IntCol(default=STATUS_ACTIVE)
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
        if orders:
            # The get_client_sales method already returns a sorted list of
            # sales by open_date column
            return orders[-1].open_date.date()


class Employee(Domain):
    """An individual who performs work for an employer under a verbal
    or written understanding where the employer gives direction as to
    what tasks are done

    :ivar admission_date: admission_date
    :ivar expire_vacation: when the vaction expires for this
    :ivar salary: salary for this employee
    :ivar status: normal/away/vacation/off
    :ivar registry_number:
    :ivar education_level:
    :ivar dependent_person_number:

    -- This is Brazil-specific information
    :ivar workpermit_data:
    :ivar military_data:
    :ivar voter_data:
    :ivar bank_account:
    :ivar role: A reference to an employee role object
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

    person = ForeignKey('Person')
    admission_date = DateTimeCol(default=None)
    expire_vacation = DateTimeCol(default=None)
    salary = PriceCol(default=0)
    status = IntCol(default=STATUS_NORMAL)
    registry_number = UnicodeCol(default=None)
    education_level = UnicodeCol(default=None)
    dependent_person_number = IntCol(default=None)
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
    :param username: username
    :param pw_hash: a hash (md5) for the user password
    :param profile: A profile represents a colection of information
      which represents what this user can do in the system
    """

    implements(IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)
    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    person = ForeignKey('Person')
    username = UnicodeCol(alternateID=True)
    pw_hash = UnicodeCol()
    is_active = BoolCol(default=True)
    profile = ForeignKey('UserProfile')

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

    :attribute crt: Código de Regime Tributário
    :ivar manager: An employee which is in charge of this branch
    1 – Simples Nacional
    2 – Simples Nacional – excesso de sublimite da receita bruta
    3 – Regime Normal

    """

    implements(IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    person = ForeignKey('Person')
    manager = ForeignKey('Employee', default=None)
    is_active = BoolCol(default=True)
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
    :param provider_type: This attribute must be either
       provider card or provider finance
    :ivar short_name: A short description of this provider
    :ivar provider_id: An identification for this provider
    :ivar open_contract_date: The date when we start working with
      this provider
    :ivar monthly_fee: values charged monthly by the credit provider
    :ivar credit_fee: fee applied by the provider for each payment transaction,
                       depending on the transaction type
    :ivar credit_installments_providers_fee: see credit fee
    :ivar credit_installments_store_fee: see credit fee
    :ivar debit_fee: see credit fee
    :ivar debit_pre_dated_fee: see credit fee
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

    provider_types = {PROVIDER_CARD: _(u'Card Provider')}

    person = ForeignKey('Person')
    is_active = BoolCol(default=True)
    provider_type = IntCol(default=PROVIDER_CARD)
    short_name = UnicodeCol()
    provider_id = UnicodeCol(default='')
    open_contract_date = DateTimeCol()
    closing_day = IntCol(default=10)
    payment_day = IntCol(default=10)
    max_installments = IntCol(default=12)
    monthly_fee = PriceCol(default=0)
    credit_fee = PercentCol(default=0)
    credit_installments_store_fee = PercentCol(default=0)
    credit_installments_provider_fee = PercentCol(default=0)
    debit_fee = PercentCol(default=0)
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
    Available fields are::
       id                  - the id of the client table
       name                - the client name
       status              - the client financial status
       cpf                 - the brazil-specific cpf attribute
       rg_number           - the brazil-specific rg_number attribute
       phone_number        - the client phone_number
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
