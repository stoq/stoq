# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
"""
lib/domain/person.py:

   Person domain classes for Stoq applications.
"""

from sqlobject import (DateTimeCol, StringCol, IntCol, FloatCol, 
                       ForeignKey, MultipleJoin, BoolCol)
from twisted.python.components import CannotAdapt
from stoqlib.exceptions import DatabaseInconsistency

from stoq.lib.runtime import get_connection
from stoq.domain.base_model import Domain, ModelAdapter
from stoq.domain.interfaces import (IIndividual, ICompany, IEmployee,
                                    IClient, ISupplier, IUser, IBranch,
                                    ISalesPerson)


__connection__ = get_connection()

    

# 
# Base Domain Classes 
#



class EmployeePosition(Domain):
    """ 
    Base class to store the employee positions 
    """

    name = StringCol(alternateID=True)
    

# WorkPermitData, MilitaryData, and VoterData are Brazil-specific information.
class WorkPermitData(Domain):
    """ 
    Work permit data for employees. pis_* is a reference to PIS ("Programa
    de Integração Social"), that is a Brazil-specific information.
    """

    number = StringCol(default=None)
    series_number = StringCol(default=None)
    pis_number = StringCol(default=None)
    pis_bank = StringCol(default=None)
    pis_registry_date = DateTimeCol(default=None)



class MilitaryData(Domain):
    """ 
    Military data for employees. This is Brazil-specific information.
    """

    number = StringCol(default=None)
    series_number = StringCol(default=None)
    category = StringCol(default=None)


class VoterData(Domain):
    """ 
    Voter data for employees. This is Brazil-specific information.
    """

    number = StringCol(default=None)
    section = StringCol(default=None)
    zone = StringCol(default=None)


class CityLocation(Domain):
    """ 
    Base class to store the locations. Used to store a person's address 
    or birth location 
    """
    
    country = StringCol(default=None)
    city = StringCol(default=None)
    state = StringCol(default=None)

    def is_valid_model(self):
        return self.country or self.city or self.state


class Address(Domain):
    """ 
    Class to store person's addresses 
    """

    street = StringCol(default='')
    number = IntCol(default=None)
    district = StringCol(default='')
    postal_code = StringCol(default='')
    complement = StringCol(default='')
    is_main_address = BoolCol(default=False)

    person = ForeignKey('Person')
    city_location = ForeignKey('CityLocation')
    
class Liaison(Domain):
    """ 
    Base class to store the person's contact informations.
    """
    
    name = StringCol(default='')
    phone_number = StringCol(default='')

    person = ForeignKey('Person')

class Calls(Domain):
    """ 
    Person's calls information.

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
    """ 
    Base class to register persons in the system. This class should never 
    be instantiated directly. 
    """

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

    def get_main_address_string(self):
        address = self.get_main_address()
        address_str = "%s, %s, %s" % (address.street, address.number,
                                      address.district)
        return address_str
    

    
    #
    # Auxiliar methods
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

    def facet_ISupplier_add(self, **kwargs):
        self.check_individual_or_company_facets()
        return PersonAdaptToSupplier(self, **kwargs)
    
    def facet_IEmployee_add(self, **kwargs):
        individual = IIndividual(self)
        if not individual:
                msg = ('The person you want to adapt must have '
                       'an individual facet')
                raise CannotAdapt(msg)
        return PersonAdaptToEmployee(self, **kwargs)

    def facet_IUser_add(self, **kwargs):
        employee = IEmployee(self)
        if not employee:
                msg = ('The person you want to adapt must have '
                       'an employee facet')
                raise CannotAdapt(msg)
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
    """ An individual facet of a person. """
    
    __implements__ = IIndividual,

    (STATUS_SINGLE,
     STATUS_MARRIED,
     STATUS_DIVORCED,
     STATUS_WIDOWED) = range(4)

    marital_statuses = {STATUS_SINGLE: _("Single"),
                        STATUS_MARRIED: _("Married"),
                        STATUS_DIVORCED: _("Divorced"),
                        STATUS_WIDOWED: _("Widowed")}    
    
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

    spouse = ForeignKey('PersonAdaptToIndividual', default=None)
    birth_location = ForeignKey('CityLocation', default=None)


    #
    # Acessors
    #


    def get_marital_statuses(self):
        return [(self.marital_statuses[i], i) 
                for i in self.marital_statuses.keys()]
                    
Person.registerFacet(PersonAdaptToIndividual)

                    
class PersonAdaptToCompany(ModelAdapter):
    """ A company facet of a person. """
    
    __implements__ = ICompany,

    # Cnpj and state_registry are
    # Brazil-specific information.
    cnpj  = StringCol(default='')
    fancy_name = StringCol(default='')
    state_registry = StringCol(default='')
                    
Person.registerFacet(PersonAdaptToCompany)


class PersonAdaptToClient(ModelAdapter):
    """ A client facet of a person. """
    
    __implements__ = IClient, 

    (STATUS_OK, 
     STATUS_INDEBTED, 
     STATUS_INSOLVENT,
     STATUS_INACTIVE) = range(4)

    status = IntCol(default=STATUS_OK)
    days_late = IntCol(default=0)
                    
Person.registerFacet(PersonAdaptToClient)


class PersonAdaptToSupplier(ModelAdapter):
    """ A supplier facet of a person. """
    
    __implements__ = ISupplier, 

    (STATUS_ACTIVE, 
     STATUS_INACTIVE, 
     STATUS_BLOCKED) = range(3)
    
    status = IntCol(default=STATUS_ACTIVE)
    product_desc = StringCol(default='')
                    
Person.registerFacet(PersonAdaptToSupplier)


class PersonAdaptToEmployee(ModelAdapter):
    """ An employee facet of a person. """
    
    __implements__ = IEmployee,

    (STATUS_NORMAL, 
     STATUS_AWAY, 
     STATUS_VACATION, 
     STATUS_OFF) = range(4)      

    _statuses = {STATUS_NORMAL: _('Normal'),
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
    
    # This is Brazil-specific information
    workpermit_data = ForeignKey('WorkPermitData', default=None)
    military_data = ForeignKey('MilitaryData', default=None)
    voter_data = ForeignKey('VoterData', default=None)
    bank_account = ForeignKey('BankAccount', default=None)

    position = ForeignKey('EmployeePosition')

    def get_status_string(self):
        assert self.status in self._statuses
        return self._statuses[self.status]
    
                    
Person.registerFacet(PersonAdaptToEmployee)


class PersonAdaptToUser(ModelAdapter):
    """ An user facet of a person. """
    
    __implements__ = IUser, 

    username = StringCol(alternateID=True)
    password = StringCol()

# TODO To be implemented: see bug 2024
#   profile  = ForeignKey('UserProfile')
                    
Person.registerFacet(PersonAdaptToUser)


class PersonAdaptToBranch(ModelAdapter):
    """ A branch facet of a person. """
    
    __implements__ = IBranch, 

    manager = ForeignKey('Person', default=None)
                    
Person.registerFacet(PersonAdaptToBranch)


class PersonAdaptToSalesPerson(ModelAdapter):
    """ A sales person facet of a person. """
    
    __implements__ = ISalesPerson, 

    (COMISSION_GLOBAL, 
     COMISSION_BY_SALESPERSON, 
     COMISSION_BY_SELLABLE,
     COMISSION_BY_PAYMENT_METHOD, 
     COMISSION_BY_BASE_SELLABLE_CATEGORY, 
     COMISSION_BY_SELLABLE_CATEGORY, 
     COMISSION_BY_SALE_TOTAL) = range(7)

    comission = FloatCol(default=0.0)
    comission_type = IntCol(default=COMISSION_BY_SALESPERSON)
                    
Person.registerFacet(PersonAdaptToSalesPerson)
