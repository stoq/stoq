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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Ariqueli Tejada Fonseca     <aritf@async.com.br>
##              Bruno Rafael Garcia         <brg@async.com.br>
##
""" Person domain classes for Stoq applications """

import datetime

from sqlobject import (DateTimeCol, UnicodeCol, IntCol,
                       ForeignKey, MultipleJoin, BoolCol, SQLObject)
from sqlobject.sqlbuilder import func, AND
from zope.interface import implements

from stoqlib.database.columns import PriceCol, DecimalCol, AutoIncCol
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import raw_phone_number
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.base import Domain, ModelAdapter, BaseSQLView
from stoqlib.domain.address import Address
from stoqlib.domain.interfaces import (IIndividual, ICompany, IEmployee,
                                       IClient, ISupplier, IUser, IBranch,
                                       ISalesPerson, IBankBranch, IActive,
                                       ICreditProvider, ITransporter,
                                       IDescribable, IPersonFacet)
from stoqlib.domain.station import BranchStation

_ = stoqlib_gettext


#
# Base Domain Classes
#

class EmployeeRole(Domain):
    """Base class to store the employee roles."""

    implements(IDescribable)

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
        """
        Check if there is another role with the same name
        @param name: name of the role to check
        @returns: True if it exists, otherwise False
        """
        conn = self.get_connection()
        results = EmployeeRole.select(
            AND(func.UPPER(EmployeeRole.q.name) == name.upper(),
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

    name = UnicodeCol(default='')
    phone_number = UnicodeCol(default='')
    person = ForeignKey('Person')

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

    #
    # SQLObject setters
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
        individual = IIndividual(self, None)
        if not individual:
            raise TypeError(
                'The person you want to adapt must have '
                'an individual facet')
        adapter_klass = self.getAdapterClass(IEmployee)
        return adapter_klass(self, **kwargs)

    def facet_IUser_add(self, **kwargs):
        self._check_individual_or_company_facets()
        adapter_klass = self.getAdapterClass(IUser)
        return adapter_klass(self, **kwargs)

    def facet_IBranch_add(self, **kwargs):
        from stoqlib.domain.product import storables_set_branch
        company = ICompany(self, None)
        if not company:
            raise TypeError(
                'The person you want to adapt must have '
                'a company facet')
        adapter_klass = self.getAdapterClass(IBranch)
        branch = adapter_klass(self, **kwargs)
        # XXX I'm not sure yet if this is the right place to update stocks
        # probably a hook called inside commit could be better...
        storables_set_branch(self._connection, branch)
        return branch

    def facet_ISalesPerson_add(self, **kwargs):
        employee = IEmployee(self, None)
        if not employee:
            raise TypeError(
                'The person you want to adapt must have '
                'an employee facet')
        adapter_klass = self.getAdapterClass(ISalesPerson)
        return adapter_klass(self, **kwargs)

#
# Adapters
#

class _PersonAdapter(ModelAdapter):
    implements(IPersonFacet)

    @property
    def person(self):
        return self.get_adapted()

class _PersonAdaptToIndividual(_PersonAdapter):
    """An individual facet of a person.

    B{Important attributes}:
        - I{rg_*}: Is a reference to RG ("Registro Geral"), this is
                   Brazil-specific information.
        - I{cpf}: ("Cadastro de Pessoa Fisica"), this is a Brazil-specific
                  information.
    """

    class sqlmeta:
        table = 'person_adapt_to_individual'
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

    #
    # Acessors
    #

    def get_marital_statuses(self):
        return [(self.marital_statuses[i], i)
                for i in self.marital_statuses.keys()]

Person.registerFacet(_PersonAdaptToIndividual, IIndividual)

class _PersonAdaptToCompany(_PersonAdapter):
    """A company facet of a person.

    B{Important attributes}:
        - I{cnpj}: ("Cadastro Nacional de Pessoa Juridica"), this is
                   Brazil-specific information.
        - I{fancy_name}: Represents the fancy name of a company.
    """
    implements(ICompany, IDescribable)

    class sqlmeta:
        table = 'person_adapt_to_company'

    # Cnpj and state_registry are
    # Brazil-specific information.
    cnpj  = UnicodeCol(default='')
    fancy_name = UnicodeCol(default='')
    state_registry = UnicodeCol(default='')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.person.name

Person.registerFacet(_PersonAdaptToCompany, ICompany)

class PersonAdaptToClient(_PersonAdapter):
    """A client facet of a person."""

    implements(IClient, IActive)

    (STATUS_SOLVENT,
     STATUS_INDEBTED,
     STATUS_INSOLVENT,
     STATUS_INACTIVE) = range(4)

    statuses = {STATUS_SOLVENT:     _(u'Solvent'),
                STATUS_INDEBTED:    _(u'Indebted'),
                STATUS_INSOLVENT:   _(u'Insolvent'),
                STATUS_INACTIVE:    _(u'Inactive')}

    status = IntCol(default=STATUS_SOLVENT)
    days_late = IntCol(default=0)

    #
    # IActive implementation
    #

    def is_active(self):
        return self.status == self.STATUS_SOLVENT

    def inactivate(self):
        assert self.is_active(), ('This client is already inactive')
        self.status = self.STATUS_INACTIVE

    def activate(self):
        assert not self.is_active(), ('This client is already active')
        self.status = self.STATUS_SOLVENT

    #
    # Auxiliar methods
    #

    def get_name(self):
        return self.person.name

    def get_status_string(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Invalid status for client, '
                                        'got %d' % self.status)
        return self.statuses[self.status]

    @classmethod
    def get_active_clients(cls, conn, extra_query=None):
        """Return a list of active clients.
        An active client is a person who are authorized to make new sales
        """
        query = cls.q.status == cls.STATUS_SOLVENT
        if extra_query:
            query = AND(query, extra_query)
        return cls.select(query, connection=conn)

    def get_client_sales(self):
        """Returns a list of sales from a SaleView tied with the
        current client
        """
        from stoqlib.domain.sale import SaleView
        conn = self.get_connection()
        query = SaleView.q.client_id == self.id
        return SaleView.select(query, connection=conn,
                               orderBy=SaleView.q.open_date)

    def get_last_purchase_date(self):
        sales = self.get_client_sales()
        if sales:
            # The get_client_sales method already returns a sorted list of
            # sales by open_date column
            return sales[-1].open_date


Person.registerFacet(PersonAdaptToClient, IClient)

class PersonAdaptToSupplier(_PersonAdapter):
    """A supplier facet of a person.

    B{Notes}:
        - I{product_desc}: Basic description of the products of a supplier.
    """
    implements(ISupplier, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE,
     STATUS_BLOCKED) = range(3)

    statuses = {STATUS_ACTIVE:      _(u'Active'),
                STATUS_INACTIVE:    _(u'Inactive'),
                STATUS_BLOCKED:     _(u'Blocked')}

    status = IntCol(default=STATUS_ACTIVE)
    product_desc = UnicodeCol(default='')

    #
    # Auxiliar methods
    #

    @classmethod
    def get_active_suppliers(cls, conn):
        query = cls.q.status == cls.STATUS_ACTIVE
        return cls.select(query, connection=conn)

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.person.name

Person.registerFacet(PersonAdaptToSupplier, ISupplier)

class PersonAdaptToEmployee(_PersonAdapter):
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

class PersonAdaptToUser(_PersonAdapter):
    """An user facet of a person."""
    implements(IUser, IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)
    statuses = {STATUS_ACTIVE:      _(u'Active'),
                STATUS_INACTIVE:    _(u'Inactive')}

    username = UnicodeCol(alternateID=True)
    password = UnicodeCol()
    is_active = BoolCol(default=True)
    profile  = ForeignKey('UserProfile')

    #
    # IActive implementation
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
    # IDescribable implementation
    #

    def get_description(self):
        return self.person.name

    @classmethod
    def check_password_for(cls, username, password, conn):
        user = cls.selectOneBy(username=username, password=password,
                               connection=conn)
        if user is None:
            return True
        return user.password == password

Person.registerFacet(PersonAdaptToUser, IUser)

class PersonAdaptToBranch(_PersonAdapter):
    """A branch facet of a person."""
    implements(IBranch, IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE:      _(u'Active'),
                STATUS_INACTIVE:    _(u'Inactive')}

    identifier = AutoIncCol('stoqlib_branch_identifier_seq')
    manager = ForeignKey('Person', default=None)
    is_active = BoolCol(default=True)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This user is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This user is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.person.name

    #
    # Branch Company methods
    #

    def get_active_stations(self):
        return self.select(
            AND(BranchStation.q.is_active == True,
                BranchStation.q.branchID == self.id),
            connection=self.get_connection())

    @classmethod
    def get_active_branches(cls, conn):
        return cls.select(cls.q.is_active == True, connection=conn)

Person.registerFacet(PersonAdaptToBranch, IBranch)

class PersonAdaptToBankBranch(_PersonAdapter):
    """A bank branch facet of a person."""
    implements(IBankBranch, IActive, IDescribable)

    is_active = BoolCol(default=True)
    bank = ForeignKey('Bank')

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This bank branch is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This bank branch is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    # IDescribable

    def get_description(self):
        return self.person.name

Person.registerFacet(PersonAdaptToBankBranch, IBankBranch)

class PersonAdaptToCreditProvider(_PersonAdapter):
    """A credit provider facet of a person."""
    implements(ICreditProvider, IActive)

    (PROVIDER_CARD,
     PROVIDER_FINANCE) = range(2)

    provider_types = {PROVIDER_CARD:    _(u'Card Provider'),
                      PROVIDER_FINANCE: _(u'Finance Provider')}

    is_active = BoolCol(default=True)
    provider_type = IntCol(default=PROVIDER_CARD)
    short_name = UnicodeCol()
    provider_id = UnicodeCol(default='')
    open_contract_date = DateTimeCol()

    #
    # ICreditProvider implementation
    #

    @classmethod
    def get_card_providers(cls, conn):
        return cls._get_providers(conn, cls.PROVIDER_CARD)

    @classmethod
    def get_finance_companies(cls, conn):
        return cls._get_providers(conn, cls.PROVIDER_FINANCE)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This provider is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This bank branch is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    @classmethod
    def _get_providers(cls, conn, provider_type=None):
        """Get a list of all credit providers.
        If provider_type is provided, we will only search for this type.
        Available types are these constants: PROVIDER_CARD and
                                             PROVIDER_FINANCE.
        """
        q1 = cls.q.is_active == True
        if provider_type is not None:
            q2 = cls.q.provider_type == provider_type
            query = AND(q1, q2)
        else:
            query = q1
        return cls.select(query, connection=conn)

Person.registerFacet(PersonAdaptToCreditProvider, ICreditProvider)

class PersonAdaptToSalesPerson(_PersonAdapter):
    """A sales person facet of a person.

    B{Important attributes}:
        - I{commission_type}: specifies the type of commission to be used by
                             the salesman.
    """
    implements(ISalesPerson, IActive, IDescribable)

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
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This salesperson is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This salesperson is already active')
        self.is_active = True

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.person.name

    #
    # Auxiliar methods
    #

    @classmethod
    def get_active_salespersons(cls, conn):
        """Get a list of all active salespersons"""
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

Person.registerFacet(PersonAdaptToSalesPerson, ISalesPerson)

class PersonAdaptToTransporter(_PersonAdapter):
    """A transporter facet of a person."""
    implements(ITransporter, IActive, IDescribable)

    is_active = BoolCol(default=True)
    open_contract_date = DateTimeCol(default=datetime.datetime.now)
    freight_percentage = DecimalCol(default=None)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This transporter is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This transporter is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.person.name

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

class ClientView(SQLObject, BaseSQLView):
    name = UnicodeCol()
    status = IntCol()
    client_id = IntCol()
    cpf = UnicodeCol()
    rg_number = UnicodeCol()
    phone_number = UnicodeCol()
