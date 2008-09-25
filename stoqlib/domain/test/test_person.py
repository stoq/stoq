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
from sqlobject.sqlbuilder import AND

from stoqlib.domain.account import BankAccount
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.exampledata import ExampleCreator
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.interfaces import (IIndividual, ICompany, IClient,
                                       ITransporter, ISupplier,
                                       ICreditProvider, IEmployee,
                                       IUser, IBranch, ISalesPerson,
                                       ISellable)
from stoqlib.domain.person import (Person,
                                   EmployeeRole, WorkPermitData,
                                   MilitaryData, VoterData,
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
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class TestEmployeeRoleHistory(DomainTest):
    def testCreate(self):
         EmployeeRole(connection=self.trans, name='ajudante')

    def testHasRole(self):
         role = EmployeeRole(connection=self.trans, name='role')
         self.failIf(role.has_other_role('Role'))
         role = EmployeeRole(connection=self.trans, name='Role')
         self.failUnless(role.has_other_role('role'))


class TestEmployeeRole(DomainTest):
    def test_get_description(self):
        role = self.create_employee_role()
        role.name =  'manager'
        self.assertEquals(role.name, role.get_description())


class TestPerson(DomainTest):

    def testGetMainAddress(self):
        person = self.create_person()
        assert not person.get_main_address()
        ctlocs = CityLocation.select(connection=self.trans)
        assert ctlocs
        ctloc = ctlocs[0]
        address = Address(connection=self.trans, person=person,
                          city_location=ctloc, is_main_address=True)
        assert person.get_main_address() is not None

    def test_get_address_string(self):
        person = self.create_person()
        ctloc = CityLocation(connection=self.trans)
        address = Address(connection=self.trans, person=person,
                          city_location=ctloc, street ='bla', streetnumber=2,
                          district='fed', is_main_address=True)
        self.assertEquals(person.get_address_string(), _(u'%s %s, %s') % (
            address.street, address.streetnumber, address.district))

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
        person = self.create_person()
        assert not self._check_has_individual_or_company_facets(person)

        #Second Person testcase with an individual facet
        person = self.create_person()
        assert not self._check_has_individual_or_company_facets(person)
        person.addFacet(IIndividual, connection=self.trans)
        assert self._check_has_individual_or_company_facets(person)

        #Third Person testcase with 2 primordial facets
        person.addFacet(ICompany, connection=self.trans)
        assert self._check_has_individual_or_company_facets(person)

        #Fourth Person testcase with company facet
        company = self.create_person()
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
        person = self.create_person()
        assert self._check_create_facet_fails(person, IClient)
        assert not self._check_create_facet_fails(person, IIndividual)
        assert not self._check_create_facet_fails(person, IClient)
        assert not self._check_create_facet_fails(person, ICompany)

    def test_facet_ITransporter_add(self):
        person = self.create_person()
        assert self._check_create_facet_fails(person, ITransporter)
        assert not self._check_create_facet_fails(person, ICompany)
        assert not self._check_create_facet_fails(person, ITransporter)
        assert not self._check_create_facet_fails(person, IIndividual)

    def test_facet_ISupplier_add(self):
        person = self.create_person()
        assert self._check_create_facet_fails(person, ISupplier)
        assert not self._check_create_facet_fails(person, IIndividual)
        assert not self._check_create_facet_fails(person, ISupplier)
        assert not self._check_create_facet_fails(person, ICompany)

    def test_facet_ICreditProvider_add(self):
        person = self.create_person()
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
        person = self.create_person()
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
        person = self.create_person()
        assert self._check_create_facet_fails(person, IUser)
        assert not self._check_create_facet_fails(person, IIndividual)
        profile = UserProfile(name='profile', connection=self.trans)
        assert not self._check_create_facet_fails(person, IUser,
                                                  username='User',
                                                  password='pass',
                                                  profile=profile)
        assert not self._check_create_facet_fails(person, ICompany)

    def test_facet_IBranch_add(self, **kwargs):
        person = self.create_person()
        assert self._check_create_facet_fails(person, IBranch)
        assert not self._check_create_facet_fails(person, ICompany)
        assert not self._check_create_facet_fails(person, IBranch)
        assert not self._check_create_facet_fails(person, IIndividual)

    def test_facet_ISalesPerson_add(self, **kwargs):
        person = self.create_person()
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

    def testGetPhoneNumberNumber(self):
        person = self.create_person()
        person.phone_number = '0321-12345'
        self.assertEquals(person.get_phone_number_number(), 32112345)

        person.phone_number = None
        self.assertEquals(person.get_phone_number_number(), 0)

    def testGetFaxNumberNumber(self):
        person = self.create_person()
        person.fax_number = '0321-12345'
        self.assertEquals(person.get_fax_number_number(), 32112345)

        person.fax_number = None
        self.assertEquals(person.get_fax_number_number(), 0)

    def testGetFormattedPhoneNumber(self):
        person = self.create_person()
        self.assertEquals(person.get_formatted_phone_number(), "")
        phone = '0321-1234'
        person.phone_number = phone
        self.assertEquals(person.get_formatted_phone_number(),
                          phone)

    def testGetFormattedFaxNumber(self):
        person = self.create_person()
        self.assertEquals(person.get_formatted_fax_number(), "")
        fax = '0321-1234'
        person.fax_number = fax
        self.assertEquals(person.get_formatted_fax_number(),
                          fax)

class _PersonFacetTest(object):
    facet = None

    def _create_person_facet(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type(self.facet.__name__)

    def testInactivate(self):
        facet = self._create_person_facet()
        if not facet.is_active:
            facet.is_active = True
        facet.inactivate()
        self.failIf(facet.is_active)
        self.assertRaises(AssertionError, facet.inactivate)

    def testActivate(self):
        facet = self._create_person_facet()
        facet.is_active = False
        facet.activate()
        self.failUnless(facet.is_active)
        self.assertRaises(AssertionError, facet.activate)

    def testGetDescription(self):
        facet = self._create_person_facet()
        self.failUnless(facet.get_description(), facet.person.name)

class TestIndividual(_PersonFacetTest, DomainTest):
    facet = Person.getAdapterClass(IIndividual)

    def testIndividual(self):
        person = self.create_person()
        individual = person.addFacet(IIndividual, connection=self.trans)

        statuses = individual.get_marital_statuses()
        self.assertEqual(type(statuses), list)
        self.failUnless(len(statuses) > 0)
        self.assertEqual(type(statuses[0]), tuple)
        self.assertEqual(type(statuses[0][0]), unicode)
        self.assertEqual(type(statuses[0][1]), int)

    def testGetCPFNumber(self):
        individual = self.create_individual()
        individual.cpf = ''
        self.assertEquals(individual.get_cpf_number(), 0)
        individual.cpf = '123.456.789-203'
        self.assertEquals(individual.get_cpf_number(), 123456789203)


class TestCompany(_PersonFacetTest, DomainTest):
    facet = Person.getAdapterClass(ICompany)

    def testGetCnpjNumberNumber(self):
        company = self.create_company()
        company.cnpj = '111.222.333.444'
        self.assertEquals(company.get_cnpj_number(), 111222333444)


class TestClient(_PersonFacetTest, DomainTest):
    facet = PersonAdaptToClient

    def test_get_name(self):
        client = self.create_client()
        client.person.name = u'Laun'
        self.assertEquals(client.get_name(), u'Laun')

    def test_get_status_string(self):
        client = self.create_client()
        status = client.status
        status = client.statuses[status]
        self.assertEquals(client.get_status_string(), status)

    def test_get_active_clients(self):
         table = PersonAdaptToClient
         active_clients = table.get_active_clients(self.trans).count()
         client = self.create_client()
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
        people = PersonAdaptToSalesPerson.select(connection=self.trans)
        assert people
        salesperson = people[0]
        count_sales = client.get_client_sales().count()
        sale = self.create_sale()
        sale.client = client
        sale.set_valid()
        products = Product.select(connection=self.trans)
        assert products
        product = products[0]
        sellable_product = ISellable(product)
        sale.add_sellable(sellable_product)
        one_more_sale = client.get_client_sales().count()
        self.assertEquals(count_sales + 1, one_more_sale)


class TestSupplier(_PersonFacetTest, DomainTest):
    facet = PersonAdaptToSupplier

    def testGetActiveSuppliers(self):
         for supplier in PersonAdaptToSupplier.get_active_suppliers(self.trans):
              self.assertEquals(supplier.status,
                                PersonAdaptToSupplier.STATUS_ACTIVE)

    def testGetAllSuppliers(self):
        query = AND(Person.q.name ==  "test",
                    PersonAdaptToSupplier.q._originalID == Person.q.id)

        suppliers = Person.select(query, connection=self.trans)
        self.assertEqual(suppliers.count(), 0)

        supplier = self.create_supplier()
        supplier.person.name =  "test"

        suppliers = Person.select(query, connection=self.trans)
        self.assertEqual(suppliers.count(), 1)

    def testGetSupplierPurchase(self):
        supplier = self.create_supplier()

        self.failIf(supplier.get_supplier_purchases())

        order = self.create_receiving_order()
        order.purchase.supplier = supplier
        order_item = self.create_receiving_order_item(order)
        order.purchase.status = PurchaseOrder.ORDER_PENDING
        order.purchase.confirm()
        order.confirm()
        order.set_valid()
        order.purchase.set_valid()

        self.failUnless(supplier.get_supplier_purchases())


class TestEmployee(_PersonFacetTest, DomainTest):
    facet = PersonAdaptToEmployee

    def test_role_history(self):
        #this test depends bug 2457
        role_name = 'crazypaper'
        employee = self.create_employee()
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
        employee = self.create_employee()

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

class TestUser(_PersonFacetTest, DomainTest):
    facet = PersonAdaptToUser

    def test_get_status_str(self):
        users = PersonAdaptToUser.select(connection=self.trans)
        assert users
        user = users[0]
        user.is_active = False
        string = user.get_status_string()
        self.assertEquals(string, _(u'Inactive'))

class TestBranch(_PersonFacetTest, DomainTest):
    facet = PersonAdaptToBranch

    def test_get_status_str(self):
        branches = PersonAdaptToBranch.select(connection=self.trans)
        assert branches
        branch = branches[0]
        branch.is_active = False
        string = branch.get_status_string()
        self.assertEquals(string, _(u'Inactive'))

    def test_get_active_branches(self):
        person = self.create_person()
        person.addFacet(ICompany, connection=self.trans)
        count = PersonAdaptToBranch.get_active_branches(self.trans).count()
        manager = self.create_employee()
        branch = person.addFacet(IBranch, connection=self.trans,
                                 manager=manager, is_active=True)
        assert branch.get_active_branches(self.trans).count() == count + 1


class TestBankBranch(_PersonFacetTest, DomainTest):
    facet = PersonAdaptToBankBranch

class TestCreditProvider(_PersonFacetTest, DomainTest):
    facet = PersonAdaptToCreditProvider

    def testGetCardProviders(self):
        count = PersonAdaptToCreditProvider.get_card_providers(self.trans).count()
        facet = self._create_person_facet()
        self.assertEqual(facet.get_card_providers(self.trans).count(),
                         count + 1)

class SalesPersonTest(_PersonFacetTest, DomainTest):

    facet = PersonAdaptToSalesPerson

    def test_get_active_salespersons(self):
        count = PersonAdaptToSalesPerson.get_active_salespersons(self.trans).count()
        salesperson = self.create_sales_person()
        one_more = salesperson.get_active_salespersons(self.trans).count()
        assert count + 1 == one_more

    def test_get_status_string(self):
        salesperson = self.create_sales_person()
        string = salesperson.get_status_string()
        self.assertEquals(string, _(u'Active'))

class TransporterTest(_PersonFacetTest, DomainTest):

    facet = PersonAdaptToTransporter

    def testGetStatusString(self):
        transporter = self.create_transporter()
        string = transporter.get_status_string()
        self.assertEquals(string, _(u'Active'))

    def testGetActiveTransporters(self):
        count = PersonAdaptToTransporter.get_active_transporters(self.trans).count()
        transporter = self.create_transporter()
        one_more = transporter.get_active_transporters(self.trans).count()
        self.assertEqual(count + 1, one_more)
