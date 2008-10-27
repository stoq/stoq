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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Ariqueli Tejada Fonseca     <aritf@async.com.br>
##              Bruno Rafael Garcia         <brg@async.com.br>
##
"""Person domain classes

The Person domain classes in Stoqlib are special since the normal Person
class is very small and additional functionality is provided through
facets (adapters).

There are currently the following Person facets available:

  - Branch
  - BankBranch
  - Client
  - Company
  - CreditProvider
  - Employee
  - Individual
  - SalesPerson
  - Supplier
  - Transporter
  - User

To create a new person, just issue the following:

    >>> from stoqlib.database.runtime import new_transaction
    >>> trans = new_transaction()

    >>> person = Person(name="A new person", connection=trans)

To assign a new role to a person, use addFacet method, for instance
to make a person into a company:

    >>> person.addFacet(ICompany, connection=trans)

The company facet provides additional persistent information related to
companies, see L{stoqlib.domain.interfaces.IClient} for more information

To access the facet, do:

    >>> company = ICompany(person)

See L{stoqlib.lib.component} for more information on adapters.

"""

import datetime

from zope.interface import implements

from stoqlib.database.orm import PriceCol, DecimalCol
from stoqlib.database.orm import (DateTimeCol, UnicodeCol, IntCol,
                                  ForeignKey, MultipleJoin, BoolCol)
from stoqlib.database.orm import const, AND, INNERJOINOn, LEFTJOINOn
from stoqlib.database.orm import Viewable
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.address import Address
from stoqlib.domain.interfaces import (IIndividual, ICompany, IEmployee,
                                       IClient, ISupplier, IUser, IBranch,
                                       ISalesPerson, IBankBranch, IActive,
                                       ICreditProvider, ITransporter,
                                       IDescribable, IPersonFacet)
from stoqlib.domain.station import BranchStation
from stoqlib.domain.transaction import TransactionEntry
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.validators import raw_phone_number, format_phone_number
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
    # IDescribable implementation
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def has_other_role(self, name):
        """Check if there is another role with the same name
        @param name: name of the role to check
        @returns: True if it exists, otherwise False
        """
        conn = self.get_connection()
        results = EmployeeRole.select(
            AND(const.UPPER(EmployeeRole.q.name) == name.upper(),
                EmployeeRole.q.id != self.id),
            connection=conn)
        return results.count() > 0

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
    # IDescribable implementation
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

    date = DateTimeCol()
    message = UnicodeCol()
    person = ForeignKey('Person')
    attendant = ForeignKey('PersonAdaptToUser')

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

    # FIXME: This can be removed after we have killed NoneInterface:
    #        Then we can just do the IClient(self), IEmployee(self
    #        calls a TypeError will automatically be issued
    def _check_individual_or_company_facets(self):
        if not self.has_individual_or_company_facets():
            raise TypeError(
                'The person you want to adapt must have at '
                'least an individual or a company facet')

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

    def get_address_string(self):
        address = self.get_main_address()
        if not address:
            return u''
        return address.get_address_string()

    def get_phone_number_number(self):
        """Returns the phone number without any non-numeric characters
        @returns: the phone number as a number
        @rtype: integer
        """
        if not self.phone_number:
            return 0
        return int(''.join([c for c in self.phone_number
                                  if c in '1234567890']))
    def get_fax_number_number(self):
        """Returns the fax number without any non-numeric characters
        @returns: the fax number as a number
        @rtype: integer
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
        return (IIndividual(self, None) or ICompany(self, None))

    #
    # Facet hooks
    #

    def facet_IClient_add(self, **kwargs):
        self._check_individual_or_company_facets()
        adapter_klass = self.getAdapterClass(IClient)
        return adapter_klass(self, **kwargs)

    def facet_ITransporter_add(self, **kwargs):
        self._check_individual_or_company_facets()
        adapter_klass = self.getAdapterClass(ITransporter)
        return adapter_klass(self, **kwargs)

    def facet_ISupplier_add(self, **kwargs):
        self._check_individual_or_company_facets()
        adapter_klass = self.getAdapterClass(ISupplier)
        return adapter_klass(self, **kwargs)

    def facet_ICreditProvider_add(self, **kwargs):
        self._check_individual_or_company_facets()
        adapter_klass = self.getAdapterClass(ICreditProvider)
        return adapter_klass(self, **kwargs)

    def facet_IEmployee_add(self, **kwargs):
        IIndividual(self)
        adapter_klass = self.getAdapterClass(IEmployee)
        return adapter_klass(self, **kwargs)

    def facet_IUser_add(self, **kwargs):
        self._check_individual_or_company_facets()
        adapter_klass = self.getAdapterClass(IUser)
        return adapter_klass(self, **kwargs)

    def facet_IBranch_add(self, **kwargs):
        ICompany(self)
        adapter_klass = self.getAdapterClass(IBranch)
        branch = adapter_klass(self, **kwargs)
        return branch

    def facet_ISalesPerson_add(self, **kwargs):
        IEmployee(self)
        adapter_klass = self.getAdapterClass(ISalesPerson)
        return adapter_klass(self, **kwargs)

#
# Adapters
#

class PersonAdapter(ModelAdapter):
    implements(IActive, IDescribable, IPersonFacet)

    @property
    def person(self):
        return self.get_adapted()

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This person facet is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This personf facet is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    # IDescribable

    def get_description(self):
        return self.person.name


class PersonAdaptToIndividual(PersonAdapter):
    """An individual facet of a person.

    B{Important attributes}:
        - I{rg_*}: Is a reference to RG ("Registro Geral"), this is
                   Brazil-specific information.
        - I{cpf}: ("Cadastro de Pessoa Fisica"), this is a Brazil-specific
                  information.
    """

    implements(IIndividual)

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

    genders = {GENDER_MALE:     _(u'Male'),
               GENDER_FEMALE:   _(u'Female')}

    cpf  = UnicodeCol(default='')
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
    # Public API
    #

    def get_marital_statuses(self):
        return [(self.marital_statuses[i], i)
                for i in self.marital_statuses.keys()]

    def get_cpf_number(self):
        """Returns the cpf number without any non-numeric characters
        @returns: the cpf number as a number
        @rtype: integer
        """
        if not self.cpf:
            return 0
        return int(''.join([c for c in self.cpf if c in '1234567890']))

Person.registerFacet(PersonAdaptToIndividual, IIndividual)

class PersonAdaptToCompany(PersonAdapter):
    """A company facet of a person.

    B{Important attributes}:
        - I{cnpj}: ("Cadastro Nacional de Pessoa Juridica"), this is
                   Brazil-specific information.
        - I{fancy_name}: Represents the fancy name of a company.
    """
    implements(ICompany)

    # Cnpj and state_registry are
    # Brazil-specific information.
    cnpj  = UnicodeCol(default='')
    fancy_name = UnicodeCol(default='')
    state_registry = UnicodeCol(default='')
    is_active = BoolCol(default=True)

    def get_cnpj_number(self):
        """Returns the cnpj number without any non-numeric characters
        @returns: the cnpj number as a number
        @rtype: integer
        """
        num = ''.join([c for c in self.cnpj if c in '1234567890'])
        if num:
            return int(num)
        return 0

    def get_state_registry_number(self):
        """Returns the state registry number without any non-numeric characters
        @returns: the state registry number as a number
        @rtype: integer
        """
        if not self.state_registry:
            return 0
        return int(''.join([c for c in self.state_registry
                                  if c in '1234567890']))

Person.registerFacet(PersonAdaptToCompany, ICompany)

class PersonAdaptToClient(PersonAdapter):
    """A client facet of a person."""

    (STATUS_SOLVENT,
     STATUS_INDEBTED,
     STATUS_INSOLVENT,
     STATUS_INACTIVE) = range(4)

    implements(IClient)

    statuses = {STATUS_SOLVENT:     _(u'Solvent'),
                STATUS_INDEBTED:    _(u'Indebted'),
                STATUS_INSOLVENT:   _(u'Insolvent'),
                STATUS_INACTIVE:    _(u'Inactive')}

    status = IntCol(default=STATUS_SOLVENT)
    days_late = IntCol(default=0)

    #
    # IActive implementation
    #

    def get_status_string(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Invalid status for client, '
                                        'got %d' % self.status)
        return self.statuses[self.status]

    def inactivate(self):
        if self.status == PersonAdaptToClient.STATUS_INACTIVE:
            raise AssertionError('This client is already inactive')
        self.status = self.STATUS_INACTIVE

    def activate(self):
        if self.status == PersonAdaptToClient.STATUS_SOLVENT:
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
    # Auxiliar methods
    #

    def get_name(self):
        return self.person.name

    @classmethod
    def get_active_clients(cls, conn):
        """Return a list of active clients.
        An active client is a person who are authorized to make new sales
        """
        return cls.select(cls.q.status == cls.STATUS_SOLVENT, connection=conn)

    def get_client_sales(self):
        from stoqlib.domain.sale import SaleView
        return SaleView.select(SaleView.q.client_id == self.id,
                               connection=self.get_connection(),
                               orderBy=SaleView.q.open_date)

    def get_last_purchase_date(self):
        sales = self.get_client_sales()
        if sales:
            # The get_client_sales method already returns a sorted list of
            # sales by open_date column
            return sales[-1].open_date.date()

Person.registerFacet(PersonAdaptToClient, IClient)

class PersonAdaptToSupplier(PersonAdapter):
    """A supplier facet of a person.

    B{Notes}:
        - I{product_desc}: Basic description of the products of a supplier.
    """
    implements(ISupplier)

    (STATUS_ACTIVE,
     STATUS_INACTIVE,
     STATUS_BLOCKED) = range(3)

    statuses = {STATUS_ACTIVE:      _(u'Active'),
                STATUS_INACTIVE:    _(u'Inactive'),
                STATUS_BLOCKED:     _(u'Blocked')}

    status = IntCol(default=STATUS_ACTIVE)
    product_desc = UnicodeCol(default='')
    is_active = BoolCol(default=True)

    #
    # Auxiliar methods
    #

    @classmethod
    def get_active_suppliers(cls, conn):
        query = cls.q.status == cls.STATUS_ACTIVE
        return cls.select(query, connection=conn)

    def get_supplier_purchases(self):
        from stoqlib.domain.purchase import PurchaseOrderView
        return PurchaseOrderView.select(
            # FIXME: should of course use id, fix this
            #        when migrating PurchaseOrderView from views.sql
            PurchaseOrderView.q.supplier_name == self.person.name,
            connection=self.get_connection(),
            orderBy=PurchaseOrderView.q.open_date)

Person.registerFacet(PersonAdaptToSupplier, ISupplier)

class PersonAdaptToEmployee(PersonAdapter):
    """An employee facet of a person."""
    implements(IEmployee)

    (STATUS_NORMAL,
     STATUS_AWAY,
     STATUS_VACATION,
     STATUS_OFF) = range(4)

    statuses = {STATUS_NORMAL:      _(u'Normal'),
                STATUS_AWAY:        _(u'Away'),
                STATUS_VACATION:    _(u'Vacation'),
                STATUS_OFF:         _(u'Off')}

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

    def get_role_history(self):
        return EmployeeRoleHistory.selectBy(
            employee=self,
            connection=self.get_connection())

    def get_active_role_history(self):
        return EmployeeRoleHistory.selectOneBy(
            employee=self,
            is_active=True,
            connection=self.get_connection())

Person.registerFacet(PersonAdaptToEmployee, IEmployee)

class PersonAdaptToUser(PersonAdapter):
    """An user facet of a person."""
    implements(IUser)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)
    statuses = {STATUS_ACTIVE:      _(u'Active'),
                STATUS_INACTIVE:    _(u'Inactive')}

    username = UnicodeCol(alternateID=True)
    password = UnicodeCol()
    is_active = BoolCol(default=True)
    profile  = ForeignKey('UserProfile')

    @classmethod
    def check_password_for(cls, username, password, conn):
        user = cls.selectOneBy(username=username, password=password,
                               connection=conn)
        if user is None:
            return True
        return user.password == password

    @classmethod
    def get_status_str(self):
        """Returns the status description of a user"""
        if self.is_active:
            return self.statuses[self.STATUS_ACTIVE]
        return self.statuses[self.STATUS_INACTIVE]

Person.registerFacet(PersonAdaptToUser, IUser)

class PersonAdaptToBranch(PersonAdapter):
    """A branch facet of a person."""
    implements(IBranch)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE:      _(u'Active'),
                STATUS_INACTIVE:    _(u'Inactive')}

    manager = ForeignKey('PersonAdaptToEmployee', default=None)
    is_active = BoolCol(default=True)

    #
    # Branch Company methods
    #

    def get_active_stations(self):
        return self.select(
            AND(BranchStation.q.is_active == True,
                BranchStation.q.branchID == self.id),
            connection=self.get_connection())

    def fetchTIDs(self, table, timestamp, te_type, trans):
        if table == TransactionEntry:
            return

        return table.select(
            AND(self._fetchTIDs(table, timestamp, te_type),
                BranchStation.q.branchID == self.id),
            connection=trans)

    def fetchTIDsForOtherStations(self, table, timestamp, te_type, trans):
        if table == TransactionEntry:
            return

        return table.select(
            AND(self._fetchTIDs(table, timestamp, te_type),
                BranchStation.q.branchID != self.id),
            connection=trans)

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


Person.registerFacet(PersonAdaptToBranch, IBranch)

class PersonAdaptToBankBranch(PersonAdapter):
    """A bank branch facet of a person."""
    implements(IBankBranch)

    is_active = BoolCol(default=True)
    bank = ForeignKey('Bank')

Person.registerFacet(PersonAdaptToBankBranch, IBankBranch)

class PersonAdaptToCreditProvider(PersonAdapter):
    """A credit provider facet of a person."""
    implements(ICreditProvider)

    (PROVIDER_CARD,) = range(1)

    provider_types = {PROVIDER_CARD: _(u'Card Provider')}

    is_active = BoolCol(default=True)
    provider_type = IntCol(default=PROVIDER_CARD)
    short_name = UnicodeCol()
    provider_id = UnicodeCol(default='')
    open_contract_date = DateTimeCol()
    closing_day = IntCol(default=10)
    payment_day = IntCol(default=10)
    max_installments = IntCol(default=12)

    #
    # ICreditProvider implementation
    #

    @classmethod
    def get_provider_by_provider_id(cls, provider_id, conn):
        """Get a provider given a provider id string
        @param provider_id: a string representing the provider
        @param conn: a database connection
        """
        return cls.selectBy(is_active=True, provider_type=cls.PROVIDER_CARD,
                            provider_id=provider_id, connection=conn)

    @classmethod
    def get_card_providers(cls, conn):
        """Get a list of all credit card providers.
        @param conn: a database connection
        """
        return cls.selectBy(is_active=True, provider_type=cls.PROVIDER_CARD,
                            connection=conn)

    @classmethod
    def has_card_provider(cls, conn):
        """Find out if there is a card provider
        @param conn: a database connection
        @returns: if there is a card provider
        """
        return bool(cls.selectBy(is_active=True,
                                 provider_type=cls.PROVIDER_CARD,
                                 connection=conn).count())


Person.registerFacet(PersonAdaptToCreditProvider, ICreditProvider)

class PersonAdaptToSalesPerson(PersonAdapter):
    """A sales person facet of a person.

    B{Important attributes}:
        - I{commission_type}: specifies the type of commission to be used by
                             the salesman.
    """
    implements(ISalesPerson)

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

    comission = DecimalCol(default=0)
    comission_type = IntCol(default=COMMISSION_BY_SALESPERSON)
    is_active = BoolCol(default=True)

    #
    # Auxiliar methods
    #

    @classmethod
    def get_active_salespersons(cls, conn):
        """Get a list of all active salespersons"""
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)

Person.registerFacet(PersonAdaptToSalesPerson, ISalesPerson)

class PersonAdaptToTransporter(PersonAdapter):
    """A transporter facet of a person."""
    implements(ITransporter)

    is_active = BoolCol(default=True)
    open_contract_date = DateTimeCol(default=datetime.datetime.now)
    freight_percentage = DecimalCol(default=0)

    #
    # Auxiliar methods
    #

    @classmethod
    def get_active_transporters(cls, conn):
        """Get a list of all available transporters"""
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)

Person.registerFacet(PersonAdaptToTransporter, ITransporter)


class EmployeeRoleHistory(Domain):
    """Base class to store the employee role history."""

    began = DateTimeCol(default=datetime.datetime.now)
    ended = DateTimeCol(default=None)
    salary = PriceCol()
    role = ForeignKey('EmployeeRole')
    employee = ForeignKey('PersonAdaptToEmployee')
    is_active = BoolCol(default=True)

#
# Views
#

class ClientView(Viewable):
    """Stores information about clients.
    Available fields are::
       id                  - the id of the person table
       name                - the client name
       status              - the client financial status
       cpf                 - the brazil-specific cpf attribute
       rg_number           - the brazil-specific rg_number attribute
       phone_number        - the client phone_number
    """

    columns = dict(
        id=Person.q.id,
        client_id=PersonAdaptToClient.q.id,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        status=PersonAdaptToClient.q.status,
        cpf=PersonAdaptToIndividual.q.cpf,
        rg_number=PersonAdaptToIndividual.q.rg_number,
        )

    joins = [
        INNERJOINOn(None, PersonAdaptToClient,
                   Person.q.id == PersonAdaptToClient.q._originalID),
        LEFTJOINOn(None, PersonAdaptToIndividual,
                   Person.q.id == PersonAdaptToIndividual.q._originalID),
        ]

    @property
    def client(self):
        return PersonAdaptToClient.get(self.client_id,
                                       connection=self._connection)

    @classmethod
    def get_active_clients(cls, conn):
        """Return a list of active clients.
        An active client is a person who are authorized to make new sales
        """
        return cls.select(cls.q.status == PersonAdaptToClient.STATUS_SOLVENT,
                          connection=conn)


class EmployeeView(Viewable):
    columns = dict(
        id=Person.q.id,
        employee_id=PersonAdaptToEmployee.q.id,
        name=Person.q.name,
        role=EmployeeRole.q.name,
        status=PersonAdaptToEmployee.q.status,
        is_active=PersonAdaptToEmployee.q.is_active,
        registry_number=PersonAdaptToEmployee.q.registry_number,
        )

    joins = [
        INNERJOINOn(None, PersonAdaptToEmployee,
                   Person.q.id == PersonAdaptToEmployee.q._originalID),
        INNERJOINOn(None, EmployeeRole,
                   PersonAdaptToEmployee.q.roleID == EmployeeRole.q.id),
        ]

    def get_status_string(self):
        return PersonAdaptToEmployee.statuses[self.status]

    @property
    def employee(self):
        return PersonAdaptToEmployee.get(self.employee_id,
                                         connection=self.get_connection())

    @classmethod
    def get_active_employees(cls, conn):
        """Return a list of active employees."""
        return cls.select(
            AND(cls.q.status == PersonAdaptToEmployee.STATUS_NORMAL,
                cls.q.is_active == True),
                connection=conn)


class SupplierView(Viewable):
    columns = dict(
        id=Person.q.id,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        fancy_name=PersonAdaptToCompany.q.fancy_name,
        cnpj=PersonAdaptToCompany.q.cnpj,
        supplier_id=PersonAdaptToSupplier.q.id,
        status=PersonAdaptToSupplier.q.status,
        )

    joins = [
        INNERJOINOn(None, PersonAdaptToSupplier,
                   Person.q.id == PersonAdaptToSupplier.q._originalID),
        LEFTJOINOn(None, PersonAdaptToCompany,
                   Person.q.id == PersonAdaptToCompany.q._originalID),
        ]

    def get_status_string(self):
        return PersonAdaptToSupplier.statuses[self.status]

    @property
    def supplier(self):
        return PersonAdaptToSupplier.get(self.supplier_id,
                                         connection=self.get_connection())

class TransporterView(Viewable):
    """
    Stores information about transporters

    @cvar id: the id of person table
    @cvar name: the transporter name
    @cvar phone_number: the transporter phone number
    @cvar transporter_id: the id of person_adapt_to_transporter table
    @cvar status: the current status of the transporter
    @cvar freight_percentage: the freight percentage charged
    """
    columns = dict(
        id=Person.q.id,
        name=Person.q.name,
        phone_number=Person.q.phone_number,
        transporter_id=PersonAdaptToTransporter.q.id,
        freight_percentage=PersonAdaptToTransporter.q.freight_percentage,
        is_active=PersonAdaptToTransporter.q.is_active,
        )

    joins = [
        INNERJOINOn(None, PersonAdaptToTransporter,
                   Person.q.id == PersonAdaptToTransporter.q._originalID),
        ]

    @property
    def transporter(self):
        return PersonAdaptToTransporter.get(self.transporter_id,
                                            connection=self.get_connection())


class BranchView(Viewable):
    columns = dict(
        id=Person.q.id,
        name=Person.q.name,
        branch_id=PersonAdaptToBranch.q.id,
        phone_number=Person.q.phone_number,
        )

    joins = [
        INNERJOINOn(None, PersonAdaptToBranch,
                   Person.q.id == PersonAdaptToBranch.q._originalID),
        ]

    @property
    def branch(self):
        return PersonAdaptToBranch.get(self.branch_id,
                                       connection=self.get_connection())


class CreditProviderView(Viewable):
    columns = dict(
        id=Person.q.id,
        name=Person.q.name,
        provider_id=PersonAdaptToCreditProvider.q.id,
        phone_number=Person.q.phone_number,
        short_name=PersonAdaptToCreditProvider.q.short_name,
        is_active=PersonAdaptToCreditProvider.q.is_active,
        )

    joins = [
        INNERJOINOn(None, PersonAdaptToCreditProvider,
                   Person.q.id == PersonAdaptToCreditProvider.q._originalID),
        ]

    @property
    def provider(self):
        return PersonAdaptToCreditProvider.get(self.provider_id,
                                               connection=self.get_connection())

