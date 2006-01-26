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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Ariqueli Tejada Fonseca     <aritf@async.com.br>
##              Bruno Rafael Garcia         <brg@async.com.br>
##
"""
stoq/domain/person.py:

   Person domain classes for Stoq applications.
"""

import gettext
import datetime

from sqlobject import (DateTimeCol, StringCol, IntCol, FloatCol,
                       ForeignKey, MultipleJoin, BoolCol)
from sqlobject.sqlbuilder import AND
from stoqlib.exceptions import DatabaseInconsistency
from zope.interface import implements

from stoq.lib.validators import raw_phone_number
from stoq.domain.base import CannotAdapt, Domain, ModelAdapter
from stoq.domain.interfaces import (IIndividual, ICompany, IEmployee,
                                    IClient, ISupplier, IUser, IBranch,
                                    ISalesPerson, IBankBranch, IActive,
                                    ICreditProvider, ITransporter,
                                    IDescribable)

_ = gettext.gettext


#
# Base Domain Classes
#


class EmployeeRole(Domain):
    """Base class to store the employee roles."""

    implements(IDescribable)

    name = StringCol(alternateID=True)

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.name


# WorkPermitData, MilitaryData, and VoterData are Brazil-specific information.
class WorkPermitData(Domain):
    """Work permit data for employees.

    B{Important Attributes}:
        - I{pis_*}: is a reference to PIS ("Programa de Integração Social"),
                    that is a Brazil-specific information.
    """

    number = StringCol(default=None)
    series_number = StringCol(default=None)
    pis_number = StringCol(default=None)
    pis_bank = StringCol(default=None)
    pis_registry_date = DateTimeCol(default=None)


class MilitaryData(Domain):
    """ Military data for employees. This is Brazil-specific
    information.
    """

    number = StringCol(default=None)
    series_number = StringCol(default=None)
    category = StringCol(default=None)


class VoterData(Domain):
    """Voter data for employees. This is Brazil-specific information."""

    number = StringCol(default=None)
    section = StringCol(default=None)
    zone = StringCol(default=None)


class CityLocation(Domain):
    """Base class to store the locations. Used to store a person's address
    or birth location.
    """

    country = StringCol(default=None)
    city = StringCol(default=None)
    state = StringCol(default=None)

    def is_valid_model(self):
        return self.country or self.city or self.state


class Address(Domain):
    """Class to store person's addresses.

    B{Important Attributes}:
       - I{is_main_address}: defines if this object stores information
                             for the main address

    """

    street = StringCol(default='')
    number = IntCol(default=None)
    district = StringCol(default='')
    postal_code = StringCol(default='')
    complement = StringCol(default='')
    is_main_address = BoolCol(default=False)
    person = ForeignKey('Person')
    city_location = ForeignKey('CityLocation')

    def is_valid_model(self):
        return (self.street and self.number and self.district
                and self.city_location.is_valid_model())

    def get_city(self):
        return self.city_location.city

    def get_country(self):
        return self.city_location.country

    def get_state(self):
        return self.city_location.state

    def get_address_string(self):
        if self.street and self.number and self.district:
            return '%s %s, %s' % (self.street, self.number, self.district)


class Liaison(Domain):
    """Base class to store the person's contact informations."""

    name = StringCol(default='')
    phone_number = StringCol(default='')
    person = ForeignKey('Person')


class Calls(Domain):
    """Person's calls information.

    Calls are information associated to a person(Clients, suppliers,
    employees, etc) that can be financial problems registries,
    collection letters information, some problems with a product
    delivered, etc.
    """

    date = DateTimeCol()
    message = StringCol()
    person = ForeignKey('Person')
    attendant = ForeignKey('PersonAdaptToUser')


class Person(Domain):
    """Base class to register persons in the system. This class should never
    be instantiated directly.
    """
    (ROLE_INDIVIDUAL,
     ROLE_COMPANY) = range(2)

    name = StringCol()
    phone_number = StringCol(default='')
    mobile_number = StringCol(default='')
    fax_number = StringCol(default='')
    email = StringCol(default='')
    notes = StringCol(default='')
    liaisons = MultipleJoin('Liaison')
    addresses = MultipleJoin('Address')
    calls = MultipleJoin('Calls')

    #
    # SQLObject callbacks
    #

    def _set_phone_number(self, value):
        if value is None:
            value = ''
        value = raw_phone_number(value)
        self._SO_set_phone_number(value)

    def _set_fax_number(self, value):
        if value is None:
            value = ''
        value = raw_phone_number(value)
        self._SO_set_fax_number(value)

    def _set_mobile_number(self, value):
        if value is None:
            value = ''
        value = raw_phone_number(value)
        self._SO_set_mobile_number(value)

    #
    # Acessors
    #

    def get_main_address(self):
        if not self.addresses:
            return
        address = [address for address in self.addresses
                              if address.is_main_address]
        if not address:
            msg = ('This person have addresses but none of them is a '
                   'main address')
            raise DatabaseInconsistency(msg)

        if len(address) > 1:
            msg = 'This person has more than 1 main address'
            raise DatabaseInconsistency, msg
        return address[0]

    #
    # Auxiliary methods
    #

    def check_individual_or_company_facets(self):
        individual = IIndividual(self)
        company = ICompany(self)
        if not (individual or company):
                msg = ('The person you want to adapt must have at '
                       'least an individual or a company facet')
                raise CannotAdapt(msg)

    #
    # Facet hooks
    #

    def facet_IClient_add(self, **kwargs):
        self.check_individual_or_company_facets()
        return PersonAdaptToClient(self, **kwargs)

    def facet_ITransporter_add(self, **kwargs):
        self.check_individual_or_company_facets()
        return PersonAdaptToTransporter(self, **kwargs)

    def facet_ISupplier_add(self, **kwargs):
        self.check_individual_or_company_facets()
        return PersonAdaptToSupplier(self, **kwargs)

    def facet_ICreditProvider_add(self, **kwargs):
        self.check_individual_or_company_facets()
        return PersonAdaptToCreditProvider(self, **kwargs)

    def facet_IEmployee_add(self, **kwargs):
        individual = IIndividual(self)
        if not individual:
                msg = ('The person you want to adapt must have '
                       'an individual facet')
                raise CannotAdapt(msg)
        return PersonAdaptToEmployee(self, **kwargs)

    def facet_IUser_add(self, **kwargs):
        self.check_individual_or_company_facets()
        return PersonAdaptToUser(self, **kwargs)

    def facet_IBranch_add(self, **kwargs):
        from stoq.domain.product import storables_set_branch
        company = ICompany(self)
        if not company:
                msg = ('The person you want to adapt must have '
                       'a company facet')
                raise CannotAdapt(msg)
        branch = PersonAdaptToBranch(self, **kwargs)
        # XXX I'm not sure yet if this is the right place to update stocks
        # probably a hook called inside commit could be better...
        storables_set_branch(self._connection, branch)
        return branch

    def facet_ISalesPerson_add(self, **kwargs):
        employee = IEmployee(self)
        if not employee:
                msg = ('The person you want to adapt must have '
                       'an employee facet')
                raise CannotAdapt(msg)
        return PersonAdaptToSalesPerson(self, **kwargs)

#
# Adapters
#

class PersonAdaptToIndividual(ModelAdapter):
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

    marital_statuses = {STATUS_SINGLE: _("Single"),
                        STATUS_MARRIED: _("Married"),
                        STATUS_DIVORCED: _("Divorced"),
                        STATUS_WIDOWED: _("Widowed"),
                        STATUS_SEPARATED: _('Separated'),
                        STATUS_COHABITATION: _('Cohabitation')}

    (GENDER_MALE,
     GENDER_FEMALE) = range(2)

    genders = {GENDER_MALE: _('Male'), GENDER_FEMALE: _('Female')}

    cpf  = StringCol(default='')
    rg_number = StringCol(default='')
    birth_date = DateTimeCol(default=None)
    occupation = StringCol(default='')
    marital_status = IntCol(default=STATUS_SINGLE)
    father_name = StringCol(default='')
    mother_name = StringCol(default='')
    rg_expedition_date = DateTimeCol(default=None)
    rg_expedition_local = StringCol(default='')
    gender = IntCol(default=None)
    spouse_name = StringCol(default='')
    birth_location = ForeignKey('CityLocation', default=None)

    #
    # Acessors
    #

    def get_marital_statuses(self):
        return [(self.marital_statuses[i], i)
                for i in self.marital_statuses.keys()]

Person.registerFacet(PersonAdaptToIndividual, IIndividual)


class PersonAdaptToCompany(ModelAdapter):
    """A company facet of a person.

    B{Important attributes}:
        - I{cnpj}: ("Cadastro Nacional de Pessoa Juridica"), this is
                   Brazil-specific information.
        - I{fancy_name}: Represents the fancy name of a company.
    """

    implements(ICompany, IDescribable)

    # Cnpj and state_registry are
    # Brazil-specific information.
    cnpj  = StringCol(default='')
    fancy_name = StringCol(default='')
    state_registry = StringCol(default='')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.get_adapted().name


Person.registerFacet(PersonAdaptToCompany, ICompany)


class PersonAdaptToClient(ModelAdapter):
    """A client facet of a person."""

    implements(IClient, IActive)

    (STATUS_SOLVENT,
     STATUS_INDEBTED,
     STATUS_INSOLVENT,
     STATUS_INACTIVE) = range(4)

    statuses = {STATUS_SOLVENT:     _('Solvent'),
                STATUS_INDEBTED:    _('Indebted'),
                STATUS_INSOLVENT:   _('Insolvent'),
                STATUS_INACTIVE:    _('Inactive')}

    status = IntCol(default=STATUS_SOLVENT)
    days_late = IntCol(default=0)

    #
    # IActive implementation
    #

    @property
    def is_active(self):
        return self.status == self.STATUS_SOLVENT

    def inactivate(self):
        assert self.is_active, ('This client is already inactive')
        self.status = self.STATUS_INACTIVE

    def activate(self):
        assert not self.is_active, ('This client is already active')
        self.status = self.STATUS_SOLVENT

    #
    # Auxiliar methods
    #

    def get_name(self):
        return self.get_adapted().name

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

Person.registerFacet(PersonAdaptToClient, IClient)


class PersonAdaptToSupplier(ModelAdapter):
    """A supplier facet of a person.

    B{Notes}:
        - I{product_desc}: Basic description of the products of a supplier.
    """

    implements(ISupplier, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE,
     STATUS_BLOCKED) = range(3)

    statuses = {STATUS_ACTIVE:      _('Active'),
                STATUS_INACTIVE:    _('Inactive'),
                STATUS_BLOCKED:     _('Blocked')}

    status = IntCol(default=STATUS_ACTIVE)
    product_desc = StringCol(default='')

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
        return self.get_adapted().name


Person.registerFacet(PersonAdaptToSupplier, ISupplier)


class PersonAdaptToEmployee(ModelAdapter):
    """An employee facet of a person."""

    implements(IEmployee)

    (STATUS_NORMAL,
     STATUS_AWAY,
     STATUS_VACATION,
     STATUS_OFF) = range(4)

    statuses = {STATUS_NORMAL: _('Normal'),
                STATUS_AWAY: _('Away'),
                STATUS_VACATION: _('Vacation'),
                STATUS_OFF: _('Off')}

    admission_date = DateTimeCol(default=None)
    expire_vacation = DateTimeCol(default=None)
    salary = FloatCol(default=0.0)
    status = IntCol(default=STATUS_NORMAL)
    registry_number = StringCol(default=None)
    education_level = StringCol(default=None)
    dependent_person_number = IntCol(default=None)
    role = ForeignKey('EmployeeRole')

    # This is Brazil-specific information
    workpermit_data = ForeignKey('WorkPermitData', default=None)
    military_data = ForeignKey('MilitaryData', default=None)
    voter_data = ForeignKey('VoterData', default=None)
    bank_account = ForeignKey('BankAccount', default=None)

    def get_role_history(self):
        conn = self.get_connection()
        return EmployeeRoleHistory.selectBy(employee=self, connection=conn)

    def get_active_role_history(self):
        active = [history for history in self.get_role_history()
                    if history.is_active]
        qty = len(active)
        if qty != 1:
            raise DatabaseInconsistency('You should have only one active '
                                        'role history, got %d' % qty)
        return active[0]

    def get_status_string(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Invalid status for employee, '
                                        'got %d' % self.status)
        return self.statuses[self.status]

Person.registerFacet(PersonAdaptToEmployee, IEmployee)


class PersonAdaptToUser(ModelAdapter):
    """An user facet of a person."""

    implements(IUser, IActive)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)
    statuses = {STATUS_ACTIVE:      _('Active'),
                STATUS_INACTIVE:    _('Inactive')}

    username = StringCol(alternateID=True)
    password = StringCol()
    is_active= BoolCol(default=True)
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

    def get_status_str(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

Person.registerFacet(PersonAdaptToUser, IUser)


class PersonAdaptToBranch(ModelAdapter):
    """A branch facet of a person."""

    implements(IBranch, IActive, IDescribable)

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)
    statuses = {STATUS_ACTIVE:      _('Active'),
                STATUS_INACTIVE:    _('Inactive')}

    manager = ForeignKey('Person', default=None)
    is_active= BoolCol(default=True)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This user is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This user is already active')
        self.is_active = True

    def get_status_str(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.get_adapted().name

    #
    # Auxiliar methods
    #

    @classmethod
    def get_active_branches(cls, conn):
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)

Person.registerFacet(PersonAdaptToBranch, IBranch)


class PersonAdaptToBankBranch(ModelAdapter):
    """A bank branch facet of a person."""

    implements(IBankBranch, IActive)

    is_active= BoolCol(default=True)
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

Person.registerFacet(PersonAdaptToBankBranch, IBankBranch)


class PersonAdaptToCreditProvider(ModelAdapter):
    """A credit provider facet of a person."""

    implements(ICreditProvider, IActive)

    (PROVIDER_CARD,
     PROVIDER_FINANCE) = range(2)

    provider_types = {PROVIDER_CARD:        _('Card Provider'),
                      PROVIDER_FINANCE:     _('Finance Provider')}

    is_active = BoolCol(default=True)
    provider_type = IntCol(default=PROVIDER_CARD)
    short_name = StringCol()
    provider_id = StringCol(default='')
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

    #
    # Auxiliar methods
    #

    def get_provider_type_str(self):
        try:
            return self.provider_types[self.provider_type]
        except KeyError:
            raise DatabaseInconsistency('Invalid provider_type, got %s' %
                                        self.provider_type)

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


class PersonAdaptToSalesPerson(ModelAdapter):
    """A sales person facet of a person.

    B{Important attributes}:
        - I{commission_type}: specifies the type of commission to be used by
                             the salesman.
    """

    implements(ISalesPerson, IActive)

    (COMMISSION_GLOBAL,
     COMMISSION_BY_SALESPERSON,
     COMMISSION_BY_SELLABLE,
     COMMISSION_BY_PAYMENT_METHOD,
     COMMISSION_BY_BASE_SELLABLE_CATEGORY,
     COMMISSION_BY_SELLABLE_CATEGORY,
     COMMISSION_BY_SALE_TOTAL) = range(7)

    comission_types = {COMMISSION_GLOBAL: _('Globally'),
                       COMMISSION_BY_SALESPERSON: _('By Salesperson'),
                       COMMISSION_BY_SELLABLE: _('By Sellable'),
                       COMMISSION_BY_PAYMENT_METHOD: _('By Payment Method'),
                       COMMISSION_BY_BASE_SELLABLE_CATEGORY: _('By Base '
                                                              'Sellable '
                                                              'Category'),
                       COMMISSION_BY_SELLABLE_CATEGORY: _('By Sellable '
                                                         'Category'),
                       COMMISSION_BY_SALE_TOTAL: _('By Sale Total')}

    comission = FloatCol(default=0.0)
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
    # Auxiliar methods
    #

    @classmethod
    def get_active_salespersons(cls, conn):
        """Get a list of all active salespersons"""
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

Person.registerFacet(PersonAdaptToSalesPerson, ISalesPerson)


class PersonAdaptToTransporter(ModelAdapter):
    """A transporter facet of a person."""

    implements(ITransporter, IActive)

    is_active = BoolCol(default=True)
    open_contract_date = DateTimeCol(default=datetime.datetime.now)
    freight_percentage = FloatCol(default=None)

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
            return _('Active')
        return _('Inactive')

    #
    # Auxiliar methods
    #

    @classmethod
    def get_active_transporters(cls, conn):
        """Get a list of all available transporters"""
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)

Person.registerFacet(PersonAdaptToTransporter, ITransporter)

class LoginInfo:
    """ This class is used by password editor only for validation of the
        fields.
    """

    PASSWORD_LEN = 6

    current_password = None
    new_password = None
    confirm_password = None

class EmployeeRoleHistory(Domain):
    """Base class to store the employee role history."""

    began = DateTimeCol(default=datetime.datetime.now)
    ended = DateTimeCol(default=None)
    salary = FloatCol()
    role = ForeignKey('EmployeeRole')
    employee = ForeignKey('PersonAdaptToEmployee')
    is_active = BoolCol(default=True)
