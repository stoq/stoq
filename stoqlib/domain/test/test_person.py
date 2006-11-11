# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Rudá Porto Filgueiras     <rudazz@gmail.com>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##            Lincoln Molica            <lincoln@async.com.br>
##
""" Test case for stoq/domain/person.py module.  """

import datetime

from kiwi.datatypes import currency
from sqlobject.main import SQLObjectMoreThanOneResultError

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.account import BankAccount, Bank
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.interfaces import (IIndividual, ICompany, IClient,
                                       ITransporter, ISupplier,
                                       ICreditProvider, IEmployee,
                                       IUser, IBranch, ISalesPerson,
                                       ISellable, IBankBranch)
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.person import (Person,
                                   EmployeeRole, WorkPermitData,
                                   MilitaryData, VoterData, Liaison, Calls,
                                   PersonAdaptToClient,
                                   PersonAdaptToBranch,
                                   PersonAdaptToSalesPerson,
                                   PersonAdaptToSupplier,
                                   PersonAdaptToEmployee,
                                   PersonAdaptToUser,
                                   EmployeeRoleHistory,
                                   PersonAdaptToBankBranch,
                                   PersonAdaptToCreditProvider,
                                   PersonAdaptToTransporter)
from stoqlib.domain.product import Product
from stoqlib.domain.profile import UserProfile
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.lib.translation import stoqlib_gettext

from stoqlib.domain.test.domaintest import BaseDomainTest, DomainTest


_ = stoqlib_gettext

PHONE_DATA_VALUES = ('7133524563','1633767277')
MOBILE_DATA_VALUES = ('7188152345', '1699786748')
FAX_DATA_VALUES = ('1681359875', '1633760125')


def get_existing_city_location(conn):
    items = CityLocation.select(connection=conn)
    assert items
    return items[0]

def get_empty_city_location(conn):
    return CityLocation(connection=conn)

def get_new_city_location(conn):
    return CityLocation(city='Birigui', state='MT', country='Paraguai',
                        connection=conn)
def get_person(conn):
    return Person(name='John', connection=conn)

def get_client(conn):
    person = Person(name='Laun', connection=conn)
    person.addFacet(IIndividual, connection=conn)
    return person.addFacet(IClient, connection=conn)

def get_employee(conn, role_name):
    person = Person(name='Denis', connection=conn)
    person.addFacet(IIndividual, connection=conn)
    role = EmployeeRole(connection=conn, name=role_name)
    workpermit_data = WorkPermitData(connection=conn)
    military_data = MilitaryData(connection=conn)
    voter_data = VoterData(connection=conn)
    bank_account = BankAccount(connection=conn)
    return person.addFacet(IEmployee, connection=conn, role=role,
                           workpermit_data=workpermit_data,
                           voter_data=voter_data, bank_account=bank_account)

def get_salesperson(conn, role_name):
    employee = get_employee(conn, role_name)
    person = employee.person
    return person.addFacet(ISalesPerson, connection=conn)


class TestPerson(BaseDomainTest):
    """
    C{Person} TestCase
    """
    _table = Person

    def get_extra_field_values(self):
        return dict(phone_number=PHONE_DATA_VALUES,
                    mobile_number=MOBILE_DATA_VALUES,
                    fax_number=FAX_DATA_VALUES)

    def test_get_main_address(self):
        self.create_instance()
        assert not self._instance.get_main_address()
        ctlocs = CityLocation.select(connection=self.trans)
        assert ctlocs
        ctloc = ctlocs[0]
        address = Address(connection=self.trans, person=self._instance,
                          city_location=ctloc, is_main_address=True)
        assert self._instance.get_main_address() is not None

    def test_get_address_string(self):
        person = get_person(self.trans)
        ctloc = CityLocation(connection=self.trans)
        address = Address(connection=self.trans, person=person,
                          city_location=ctloc, street ='bla', number=2,
                          district='fed', is_main_address=True)
        self.assertEquals(person.get_address_string(), _(u'%s %s, %s') % (
            address.street, address.number, address.district))

    #This method is used by test_check_individual_or_company_facets() method
    def _check_has_individual_or_company_facets(self, person):
        try:
            person._check_individual_or_company_facets()
        # yuck.
        except TypeError, e:
            return False
        else:
            return True

    def test_check_individual_or_company_facets(self):
        #First Person testcase without facets
        person = get_person(self.trans)
        assert not self._check_has_individual_or_company_facets(person)

        #Second Person testcase with an individual facet
        person = get_person(self.trans)
        assert not self._check_has_individual_or_company_facets(person)
        person.addFacet(IIndividual, connection=self.trans)
        assert self._check_has_individual_or_company_facets(person)

        #Third Person testcase with 2 primordial facets
        person.addFacet(ICompany, connection=self.trans)
        assert self._check_has_individual_or_company_facets(person)

        #Fourth Person testcase with company facet
        company = get_person(self.trans)
        assert not self._check_has_individual_or_company_facets(company)
        company.addFacet(ICompany, connection=self.trans)
        assert self._check_has_individual_or_company_facets(company)

    def _check_create_facet_fails(self, person, iface, **kwargs):
        try:
            person.addFacet(iface, connection=self.trans, **kwargs)
        # yuck.
        except (TypeError, ValueError), e:
            # Ok, it should actually fail since we did not create an
            # individual or company facets
            return True
        else:
            return False

    def test_facet_IClient_add(self):
        person = get_person(self.trans)
        assert self._check_create_facet_fails(person, IClient)
        assert not self._check_create_facet_fails(person, IIndividual)
        assert not self._check_create_facet_fails(person, IClient)
        assert not self._check_create_facet_fails(person, ICompany)

    def test_facet_ITransporter_add(self):
        person = get_person(self.trans)
        assert self._check_create_facet_fails(person, ITransporter)
        assert not self._check_create_facet_fails(person, ICompany)
        assert not self._check_create_facet_fails(person, ITransporter)
        assert not self._check_create_facet_fails(person, IIndividual)

    def test_facet_ISupplier_add(self):
        person = get_person(self.trans)
        assert self._check_create_facet_fails(person, ISupplier)
        assert not self._check_create_facet_fails(person, IIndividual)
        assert not self._check_create_facet_fails(person, ISupplier)
        assert not self._check_create_facet_fails(person, ICompany)

    def test_facet_ICreditProvider_add(self):
        person = get_person(self.trans)
        short_name = 'Credicard'
        date = datetime.date(2006, 06, 01)
        assert self._check_create_facet_fails(person, ICreditProvider,
                                              short_name=short_name,
                                              open_contract_date=date)
        assert not self._check_create_facet_fails(person, ICompany)
        assert not self._check_create_facet_fails(person, ICreditProvider,
                                                  short_name=short_name,
                                                  open_contract_date=date)
        assert not self._check_create_facet_fails(person, IIndividual)

    def test_facet_IEmployee_add(self, **kwargs):
        person = get_person(self.trans)
        assert self._check_create_facet_fails(person, IEmployee)
        assert not self._check_create_facet_fails(person, IIndividual)
        role = EmployeeRole(connection=self.trans, name='Escriba')
        workpermit_data = WorkPermitData(connection=self.trans)
        military_data = MilitaryData(connection=self.trans)
        voter_data = VoterData(connection=self.trans)
        bank_account = BankAccount(connection=self.trans)
        assert not self._check_create_facet_fails(person, IEmployee,
                                                  role=role,
                                                  workpermit_data=workpermit_data,
                                                  military_data=military_data,
                                                  voter_data=voter_data,
                                                  bank_account=bank_account)
        assert not self._check_create_facet_fails(person, ICompany)

    def test_facet_IUser_add(self, **kwargs):
        person = get_person(self.trans)
        assert self._check_create_facet_fails(person, IUser)
        assert not self._check_create_facet_fails(person, IIndividual)
        profile = UserProfile(name='profile', connection=self.trans)
        assert not self._check_create_facet_fails(person, IUser,
                                                  username='User',
                                                  password='pass',
                                                  profile=profile)
        assert not self._check_create_facet_fails(person, ICompany)

    def test_facet_IBranch_add(self, **kwargs):
        person = get_person(self.trans)
        assert self._check_create_facet_fails(person, IBranch)
        assert not self._check_create_facet_fails(person, ICompany)
        assert not self._check_create_facet_fails(person, IBranch)
        assert not self._check_create_facet_fails(person, IIndividual)

    def test_facet_ISalesPerson_add(self, **kwargs):
        person = get_person(self.trans)
        assert self._check_create_facet_fails(person, ISalesPerson)
        assert not self._check_create_facet_fails(person, IIndividual)
        assert self._check_create_facet_fails(person, ISalesPerson)
        role = EmployeeRole(connection=self.trans, name='Escrivaum')
        workpermit_data = WorkPermitData(connection=self.trans)
        military_data = MilitaryData(connection=self.trans)
        voter_data = VoterData(connection=self.trans)
        bank_account = BankAccount(connection=self.trans)
        assert not self._check_create_facet_fails(person, IEmployee,
                                                  role=role,
                                                  workpermit_data=workpermit_data,
                                                  military_data=military_data,
                                                  voter_data=voter_data,
                                                  bank_account=bank_account)
        assert not self._check_create_facet_fails(person, ICompany)

class TestEmployeeRole(BaseDomainTest):
    """
    C{EmployeeRole} TestCase
    """
    _table = EmployeeRole

    def test_get_description(self):
        self.create_instance()
        name = 'manager'
        self._instance.name = name
        desc = self._instance.get_description()
        self.assertEquals(desc, name)


class TestWorkPermitData(BaseDomainTest):
    """
    C{WorkPermitData} TestCase
    """
    _table = WorkPermitData


class TestMilitaryData(BaseDomainTest):
    """
    C{MilitaryData} TestCase
    """
    _table = MilitaryData


class TestVoterData(BaseDomainTest):
    """
    C{VoterData} TestCase
    """
    _table = VoterData

class TestLiaison(BaseDomainTest):
    """
    C{Liaison} TestCase
    """
    _table = Liaison


class TestCalls(BaseDomainTest):
    """
    C{Calls} TestCase
    """
    _table = Calls


class TestIndividual(DomainTest):
    def testIndividual(self):
        person = self.create_person()
        individual = person.addFacet(IIndividual, connection=self.trans)

        statuses = individual.get_marital_statuses()
        self.assertEqual(type(statuses), list)
        self.failUnless(len(statuses) > 0)
        self.assertEqual(type(statuses[0]), tuple)
        self.assertEqual(type(statuses[0][0]), unicode)
        self.assertEqual(type(statuses[0][1]), int)

class TestCompany(DomainTest):
    def testCompany(self):
        person = self.create_person()
        company = person.addFacet(ICompany, connection=self.trans)
        self.assertEqual(company.get_description(), person.name)

class TestClient(BaseDomainTest):
    """
    C{PersonAdaptToClient} TestCase
    """
    _table = PersonAdaptToClient

    def get_adapter(self):
        person = get_person(self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        return person.addFacet(IClient, connection=self.trans)

    def test_is_active(self):
        client = get_client(self.trans)
        client.status = PersonAdaptToClient.STATUS_INDEBTED
        assert not client.is_active()

    def test_inactivate(self):
        client = get_client(self.trans)
        client.status = PersonAdaptToClient.STATUS_SOLVENT
        client.inactivate()
        assert not client.is_active()

    def test_activate(self):
        client = get_client(self.trans)
        client.status = PersonAdaptToClient.STATUS_INACTIVE
        client.activate()
        assert client.is_active()

    def test_get_name(self):
        client = get_client(self.trans)
        self.assertEquals(client.get_name(), u'Laun')

    def test_get_status_string(self):
        client = get_client(self.trans)
        status = client.status
        status = client.statuses[status]
        self.assertEquals(client.get_status_string(), status)

    def test_get_active_clients(self):
         table = PersonAdaptToClient
         active_clients = table.get_active_clients(self.trans).count()
         client = get_client(self.trans)
         client.status = table.STATUS_SOLVENT
         one_more_active_client = table.get_active_clients(self.trans).count()
         self.assertEquals(active_clients + 1, one_more_active_client)

    def test_get_client_sales(self):
        client = PersonAdaptToClient.select(connection=self.trans)
        assert client
        client = client[0]
        cfop = CfopData(code='123', description='bla', connection=self.trans)
        branches = PersonAdaptToBranch.select(connection=self.trans)
        assert branches
        branch = branches[0]
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        people = PersonAdaptToSalesPerson.select(connection=self.trans)
        assert people
        salesperson = people[0]
        count_sales = client.get_client_sales().count()
        date = datetime.date(2006, 11, 11)
        new_sale = Sale(coupon_id=123, client=client, cfop=cfop,
                        till=till, salesperson=salesperson,
                        connection=self.trans,
                        open_date=date)
        new_sale.set_valid()
        products = Product.select(connection=self.trans)
        assert products
        product = products[0]
        sellable_product = ISellable(product)
        sellable_product.add_sellable_item(sale=new_sale)
        one_more_sale = client.get_client_sales().count()
        self.assertEquals(count_sales + 1, one_more_sale)
        last_purchase_date = client.get_last_purchase_date()

        #Testing get_last_purchase_date method bellow
        self.assertEquals(client.get_last_purchase_date(), date)

class TestSupplier(BaseDomainTest):
    """
    C{PersonAdaptToSupplier} TestCase
    """
    _table = PersonAdaptToSupplier

    def get_adapter(self):
        person = get_person(self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        return person.addFacet(ISupplier, connection=self.trans)

    def test_get_active_suppliers(self):
        table = PersonAdaptToSupplier
        active_suppliers = table.get_active_suppliers(self.trans)
        for supplier in active_suppliers:
            self.assertEquals(supplier.status, table.STATUS_ACTIVE)

    def test_get_description(self):
        person = get_person(self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        supplier = person.addFacet(ISupplier, connection=self.trans)
        self.assertEquals(supplier.get_description(), person.name)


class TestEmployee(BaseDomainTest):
    """
    C{PersonAdaptToEmployee} TestCase
    """
    _table = PersonAdaptToEmployee

    def get_adapter(self):
        role_name = 'idiot'
        return get_employee(self.trans, role_name)

    def test_role_history(self):
        #this test depends bug 2457
        role_name = 'crazypaper'
        employee = get_employee(self.trans, role_name)
        history = EmployeeRoleHistory(role=employee.role,
                                      employee=employee,
                                      connection=self.trans,
                                      salary=currency(500),
                                      is_active=False)
        old_count = employee.get_role_history().count()
        history = EmployeeRoleHistory(role=employee.role,
                                      employee=employee,
                                      connection=self.trans,
                                      salary=currency(900))
        new_count = employee.get_role_history().count()
        self.assertEquals(old_count + 1, new_count)

    def test_get_active_role_history(self):
        role_name = 'boss'
        employee = get_employee(self.trans, role_name)

        #creating 2 active role history, asserting it fails
        history = EmployeeRoleHistory(role=employee.role,
                                      employee=employee,
                                      connection=self.trans,
                                      salary=currency(230))
        history2 = EmployeeRoleHistory(role=employee.role,
                                      employee=employee,
                                      connection=self.trans,
                                      salary=currency(320))
        history_validated = False
        try:
            employee.get_active_role_history()
        except SQLObjectMoreThanOneResultError, e:
            history_validated = True
        assert history_validated

        #now with one employeerolehistory
        #FIXME: this breaks in buildbot, figure out why.
        #history2.is_active = False
        #assert employee.get_role_history()

class TestUser(BaseDomainTest):
    """
    C{PersonAdaptToUser} TestCase
    """
    _table = PersonAdaptToUser

    def get_adapter(self):
        person = get_person(self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        profile = UserProfile(name='vai', connection=self.trans)
        return person.addFacet(IUser, connection=self.trans, username='bla',
                               password='ble', profile=profile)

    def test_inactivate(self):
        users = PersonAdaptToUser.select(connection=self.trans)
        assert users
        user = users[0]
        user.is_active = True
        user.inactivate()
        assert user.is_active is False

    def test_activate(self):
        users = PersonAdaptToUser.select(connection=self.trans)
        assert users
        user = users[0]
        user.is_active = False
        user.activate()
        assert user.is_active is True

    def test_get_status_str(self):
        users = PersonAdaptToUser.select(connection=self.trans)
        assert users
        user = users[0]
        user.is_active = False
        string = user.get_status_string()
        self.assertEquals(string, _(u'Inactive'))


class TestBranch(BaseDomainTest):
    """
    C{PersonAdaptToBranch} TestCase
    """
    _table = PersonAdaptToBranch

    def get_adapter(self):
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        return person.addFacet(IBranch, connection=self.trans,
                                 manager=person)

    def test_inactivate(self):
        branches = PersonAdaptToBranch.select(connection=self.trans)
        assert branches
        branch = branches[0]
        branch.is_active = True
        branch.inactivate()
        self.assertEquals(branch.is_active, False)

    def test_activate(self):
        branches = PersonAdaptToBranch.select(connection=self.trans)
        assert branches
        branch = branches[0]
        branch.is_active = False
        branch.activate()
        assert branch.is_active is True

    def test_get_status_str(self):
        branches = PersonAdaptToBranch.select(connection=self.trans)
        assert branches
        branch = branches[0]
        branch.is_active = False
        string = branch.get_status_string()
        self.assertEquals(string, _(u'Inactive'))

    def test_get_description(self):
        person = Person(name='Winston', connection=self.trans)
        person.addFacet(ICompany, connection=self.trans)
        branch = person.addFacet(IBranch, connection=self.trans,
                                 manager=person)
        self.failUnless(branch.get_description(), person.name)

    def test_get_active_branches(self):
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        count = PersonAdaptToBranch.get_active_branches(self.trans).count()
        branch = person.addFacet(IBranch, connection=self.trans,
                                 manager=person, is_active=True)
        assert branch.get_active_branches(self.trans).count() == count + 1


class TestBankBranch(BaseDomainTest):
    """
    C{PersonAdaptToBankBranch} TestCase
    """
    _table = PersonAdaptToBankBranch

    def setUp(self):
        BaseDomainTest.setUp(self)
        person = get_person(self.trans)
        bank = Bank(connection=self.trans, name='Boston', short_name='short',
                    compensation_code='1234')
        person.addFacet(ICompany, connection=self.trans)
        self._adapter = person.addFacet(IBankBranch, connection=self.trans,
                                        bank=bank)
    def get_adapter(self):
        return self._adapter

    def test_inactivate(self):
        bankbranches = PersonAdaptToBankBranch.select(connection=self.trans)
        assert bankbranches
        bankbranch = bankbranches[0]
        bankbranch.is_active = True
        bankbranch.inactivate()
        assert bankbranch.is_active == False

    def test_activate(self):
        bankbranches = PersonAdaptToBankBranch.select(connection=self.trans)
        assert bankbranches
        bankbranch = bankbranches[0]
        bankbranch.is_active = False
        bankbranch.activate()
        assert bankbranch.is_active is True


class TestCreditProvider(BaseDomainTest):
    """
    C{PersonAdaptToCreditProvider} TestCase
    """
    _table = PersonAdaptToCreditProvider

    def get_adapter(self):
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        return  person.addFacet(ICreditProvider,
                                connection=self.trans,
                                short_name='Velec',
                                open_contract_date=datetime.date(2006, 01, 01))


    def test_get_card_providers(self):
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        count = PersonAdaptToCreditProvider.get_card_providers(self.trans).count()
        credit_provider = person.addFacet(ICreditProvider, connection=self.trans,
                                          short_name='Plus',
                                          open_contract_date=datetime.date(2006, 02, 02),
                                          provider_type=0)
        assert credit_provider.get_card_providers(self.trans).count() == count + 1

    def test_get_card_providers(self):
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        count = PersonAdaptToCreditProvider.get_finance_companies(self.trans).count()
        credit_provider = person.addFacet(ICreditProvider, connection=self.trans,
                                          short_name='Cards',
                                          open_contract_date=datetime.date(2006, 02, 02),
                                          provider_type=1)
        assert credit_provider.get_finance_companies(self.trans).count() == count + 1

    def test_inactivate(self):
        cproviders = PersonAdaptToCreditProvider.select(connection=self.trans)
        assert cproviders
        cprovider = cproviders[0]
        cprovider.is_active = True
        cprovider.inactivate()
        assert cprovider.is_active is False

    def test_activate(self):
        table = PersonAdaptToCreditProvider
        credit_providers = table.select(connection=self.trans)
        assert credit_providers
        credit_provider = credit_providers[0]
        credit_provider.is_active = False
        credit_provider.activate()
        assert credit_provider.is_active is True

class TestSalesPerson(BaseDomainTest):
    """
    C{PersonAdaptToSalesPerson} TestCase
    """
    _table = PersonAdaptToSalesPerson

    def get_adapter(self):
        return get_salesperson(self.trans, 'vigia')

    def test_inactivate(self):
        people = PersonAdaptToSalesPerson.select(connection=self.trans)
        assert people
        salesperson = people[0]
        salesperson.is_active = True
        salesperson.inactivate()
        assert salesperson.is_active is False

    def test_activate(self):
        people = PersonAdaptToSalesPerson.select(connection=self.trans)
        assert people
        salesperson = people[0]
        salesperson.is_active = False
        salesperson.activate()
        assert salesperson.is_active is True

    def test_get_active_salespersons(self):
        table = PersonAdaptToSalesPerson
        count = table.get_active_salespersons(self.trans).count()
        salesperson = get_salesperson(self.trans, 'vendedor')
        one_more = salesperson.get_active_salespersons(self.trans).count()
        assert count + 1 == one_more

    def test_get_status_string(self):
        salesperson = get_salesperson(self.trans, 'entregador')
        string = salesperson.get_status_string()
        self.assertEquals(string, _(u'Active'))


class TestTransporter(BaseDomainTest):
    """
    C{PersonAdaptToTransporter} TestCase
    """
    _table = PersonAdaptToTransporter

    def get_adapter(self):
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        return person.addFacet(ITransporter, connection=self.trans)

    def test_inactivate(self):
        transporters = PersonAdaptToTransporter.select(connection=self.trans)
        assert transporters
        transporter = transporters[0]
        transporter.is_active = True
        transporter.inactivate()
        assert not transporter.is_active

    def test_activate(self):
        transporters = PersonAdaptToTransporter.select(connection=self.trans)
        assert transporters
        transporter = transporters[0]
        transporter.is_active = False
        transporter.activate()
        assert transporter.is_active

    def test_get_status_string(self):
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        transporter = person.addFacet(ITransporter, connection=self.trans)
        string = transporter.get_status_string()
        self.assertEquals(string, _(u'Active'))

    def test_get_active_transporters(self):
        table = PersonAdaptToTransporter
        count = table.get_active_transporters(self.trans).count()
        person = get_person(self.trans)
        person.addFacet(ICompany, connection=self.trans)
        transporter = person.addFacet(ITransporter, connection=self.trans)
        one_more = transporter.get_active_transporters(self.trans).count()
        assert count + 1 == one_more


class TestEmployeeRoleHistory(DomainTest):
     def testCreate(self):
          EmployeeRole(connection=self.trans, name='ajudante')

     def testHasRole(self):
          role = EmployeeRole(connection=self.trans, name='role')
          self.failIf(role.has_other_role('Role'))
          role = EmployeeRole(connection=self.trans, name='Role')
          self.failUnless(role.has_other_role('role'))
