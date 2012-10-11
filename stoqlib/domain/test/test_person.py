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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Test case for stoq/domain/person.py module.  """

import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from storm.store import AutoReload

from kiwi.currency import currency

from stoqlib.database.orm import ORMObjectIntegrityError, AND
from stoqlib.domain.person import Calls, Liaison
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.exampledata import ExampleCreator
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import (Branch, Client, ClientCategory,
                                   ClientSalaryHistory, Company,
                                   CreditProvider, Employee, EmployeeRole,
                                   EmployeeRoleHistory, Individual,
                                   LoginUser, Person, SalesPerson, Supplier,
                                   Transporter)
from stoqlib.domain.product import Product
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sellable import ClientCategoryPrice
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.enums import LatePaymentPolicy
from stoqlib.exceptions import SellError
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class TestEmployeeRoleHistory(DomainTest):
    def testCreate(self):
        EmployeeRole(connection=self.trans, name='ajudante')

    def testHasRole(self):
        role = EmployeeRole(connection=self.trans, name='role')
        self.failIf(role.has_other_role(u'Role'))
        role = EmployeeRole(connection=self.trans, name='Role')
        self.failUnless(role.has_other_role(u'role'))


class TestEmployeeRole(DomainTest):
    def testGetdescription(self):
        role = self.create_employee_role()
        role.name = 'manager'
        self.assertEquals(role.name, role.get_description())


class TestPerson(DomainTest):

    def testAddresses(self):
        person = self.create_person()
        assert not person.get_main_address()
        ctlocs = CityLocation.select(connection=self.trans)
        assert ctlocs
        ctloc = ctlocs[0]
        address = Address(connection=self.trans, person=person,
                          city_location=ctloc, is_main_address=True)
        self.assertEquals(person.get_main_address(), address)

        self.assertEquals(len(list(person.addresses)), 1)
        self.assertEquals(person.addresses[0], address)

    def testCalls(self):
        person = self.create_person()
        user = self.create_user()
        self.assertEquals(len(list(person.calls)), 0)

        call = Calls(connection=self.trans, date=datetime.datetime.today(),
                     description='', message='', person=person, attendant=user)
        self.assertEquals(len(list(person.calls)), 1)
        self.assertEquals(person.calls[0], call)

    def testLiaison(self):
        person = self.create_person()
        self.assertEquals(len(list(person.liaisons)), 0)

        contact = Liaison(connection=self.trans, person=person)
        self.assertEquals(len(list(person.liaisons)), 1)
        self.assertEquals(person.liaisons[0], contact)

    def testGetaddressString(self):
        person = self.create_person()
        ctloc = CityLocation(connection=self.trans)
        address = Address(connection=self.trans, person=person,
                          city_location=ctloc, street='bla', streetnumber=2,
                          district='fed', is_main_address=True)
        self.assertEquals(person.get_address_string(), _(u'%s %s, %s') % (
            address.street, address.streetnumber, address.district))

    def testGetMobileNumberNumber(self):
        person = self.create_person()
        person.mobile_number = '0321-12345'
        self.assertEquals(person.mobile_number, '032112345')

    def testGetPhoneNumberNumber(self):
        person = self.create_person()
        person.phone_number = '0321-12345'
        self.assertEquals(person.get_phone_number_number(), 32112345)
        self.assertEquals(person.phone_number, '032112345')

        person.phone_number = None
        self.assertEquals(person.get_phone_number_number(), 0)

    def testGetFaxNumberNumber(self):
        person = self.create_person()
        person.fax_number = '0321-12345'
        self.assertEquals(person.fax_number, '032112345')
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
        return ExampleCreator.create(self.trans, self.facet.__name__)

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
    facet = Individual

    def testIndividual(self):
        person = self.create_person()
        individual = Individual(person=person, connection=self.trans)

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
    facet = Company

    def testGetCnpjNumberNumber(self):
        company = self.create_company()
        company.cnpj = '111.222.333.444'
        self.assertEquals(company.get_cnpj_number(), 111222333444)


class TestClient(_PersonFacetTest, DomainTest):
    facet = Client

    def testGetname(self):
        client = self.create_client()
        client.person.name = u'Laun'
        self.assertEquals(client.get_name(), u'Laun')

    def testGetStatusString(self):
        client = self.create_client()
        status = client.status
        status = client.statuses[status]
        self.assertEquals(client.get_status_string(), status)

    def testGetactiveClients(self):
        table = Client
        active_clients = table.get_active_clients(self.trans).count()
        client = self.create_client()
        client.status = table.STATUS_SOLVENT
        one_more_active_client = table.get_active_clients(self.trans).count()
        self.assertEquals(active_clients + 1, one_more_active_client)

    def testGetclient_sales(self):
        client = Client.select(connection=self.trans)
        assert client
        client = client[0]
        CfopData(code='123', description='bla', connection=self.trans)
        branches = Branch.select(connection=self.trans)
        assert branches
        people = SalesPerson.select(connection=self.trans)
        assert people
        count_sales = client.get_client_sales().count()
        sale = self.create_sale()
        sale.client = client
        products = Product.select(connection=self.trans)
        assert products
        product = products[0]
        sale.add_sellable(product.sellable)
        one_more_sale = client.get_client_sales().count()
        self.assertEquals(count_sales + 1, one_more_sale)

    def testClientCategory(self):
        categories = ClientCategory.selectBy(name='Category',
                                             connection=self.trans)
        self.assertEquals(categories.count(), 0)

        category = self.create_client_category('Category')
        categories = ClientCategory.selectBy(name='Category',
                                             connection=self.trans)
        self.assertEquals(categories.count(), 1)

        self.assertTrue(category.can_remove())
        category.remove()
        categories = ClientCategory.selectBy(name='Category',
                                             connection=self.trans)
        self.assertEquals(categories.count(), 0)

        sellable = self.create_sellable(price=50)
        category = self.create_client_category('Category')
        ClientCategoryPrice(sellable=sellable,
                            category=category,
                            price=75,
                            connection=self.trans)
        self.assertFalse(category.can_remove())

    def test_can_purchase_allow_all(self):
        #: This parameter always allows the client to purchase, no matter if he
        #: has late payments
        sysparam(self.trans).update_parameter('LATE_PAYMENTS_POLICY',
                                str(int(LatePaymentPolicy.ALLOW_SALES)))

        client = self.create_client()
        bill_method = PaymentMethod.get_by_name(self.trans, 'bill')
        check_method = PaymentMethod.get_by_name(self.trans, 'check')
        money_method = PaymentMethod.get_by_name(self.trans, 'money')
        store_credit_method = PaymentMethod.get_by_name(self.trans,
                                                        'store_credit')
        today = datetime.date.today()

        # client can pay if he doesn't have any payments
        client.credit_limit = Decimal("1000")
        self.assertTrue(client.can_purchase(money_method, currency("200")))

        # client can pay if he has payments that are not overdue
        payment = self.create_payment(Payment.TYPE_IN, today, method=bill_method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertTrue(client.can_purchase(check_method, currency("200")))

        # client can pay even if he does have overdue payments
        payment = self.create_payment(Payment.TYPE_IN,
                            today - relativedelta(days=1), method=check_method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertTrue(client.can_purchase(store_credit_method, currency("200")))

        # But he cannot pay if its above the credit limit
        self.assertRaises(SellError, client.can_purchase, store_credit_method, currency("1001"))

    def test_can_purchase_disallow_store_credit(self):
        #: This parameter disallows the client to purchase with store credit
        #: when he has late payments
        sysparam(self.trans).update_parameter('LATE_PAYMENTS_POLICY',
                                str(int(LatePaymentPolicy.DISALLOW_STORE_CREDIT)))

        client = self.create_client()
        bill_method = PaymentMethod.get_by_name(self.trans, 'bill')
        check_method = PaymentMethod.get_by_name(self.trans, 'check')
        money_method = PaymentMethod.get_by_name(self.trans, 'money')
        store_credit_method = PaymentMethod.get_by_name(self.trans,
                                                        'store_credit')
        today = datetime.date.today()

        # client can pay if he doesn't have any payments
        self.assertTrue(client.can_purchase(money_method, currency("0")))

        # client can pay if he has payments that are not overdue
        payment = self.create_payment(Payment.TYPE_IN, today, method=bill_method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertTrue(client.can_purchase(money_method, currency("0")))

        # for a client with overdue payments
        payment = self.create_payment(Payment.TYPE_IN,
                                      today - relativedelta(days=1),
                                      method=money_method)
        payment.status = Payment.STATUS_PENDING
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        # client can pay if payment method is not store credit
        self.assertTrue(client.can_purchase(check_method, currency("0")))
        self.assertTrue(client.can_purchase(money_method, currency("0")))
        # client can not pay if payment method is store credit
        self.assertRaises(SellError, client.can_purchase, store_credit_method, currency("0"))

    def test_can_purchase_disallow_all(self):
        #: This parameter disallows the client to purchase with store credit
        #: when he has late payments
        sysparam(self.trans).update_parameter('LATE_PAYMENTS_POLICY',
                                str(int(LatePaymentPolicy.DISALLOW_SALES)))

        client = self.create_client()
        bill_method = PaymentMethod.get_by_name(self.trans, 'bill')
        check_method = PaymentMethod.get_by_name(self.trans, 'check')
        money_method = PaymentMethod.get_by_name(self.trans, 'money')
        store_credit_method = PaymentMethod.get_by_name(self.trans,
                                                        'store_credit')
        today = datetime.date.today()

        # client can pay if he doesn't have any payments
        self.assertTrue(client.can_purchase(money_method, currency("0")))

        # client can pay if he has overdue payments
        payment = self.create_payment(Payment.TYPE_IN, today, method=bill_method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertTrue(client.can_purchase(check_method, currency("0")))

        # client can not pay if he has overdue payments
        payment = self.create_payment(Payment.TYPE_IN,
                                      today - relativedelta(days=1),
                                      method=bill_method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        payment.status = Payment.STATUS_PENDING
        self.assertRaises(SellError, client.can_purchase, store_credit_method,
                                     currency("0"))
        self.assertRaises(SellError, client.can_purchase, check_method,
                                     currency("0"))
        self.assertRaises(SellError, client.can_purchase, money_method,
                                     currency("0"))

    def test_can_purchase_total_amount(self):
        method = PaymentMethod.get_by_name(self.trans, 'store_credit')

        # client can not buy if he does not have enough store credit
        client = self.create_client()
        client.credit_limit = currency('0')
        self.assertRaises(SellError, client.can_purchase, method, currency('1'))

        # client can buy if he has enough store credit
        client.credit_limit = currency('1000')
        self.assertTrue(client.can_purchase(method, currency('200')))
        self.assertRaises(SellError, client.can_purchase, method, currency('1001'))

    def test_update_credit_limit(self):
        client = self.create_client()
        client.salary = 100

        # just setting paramater to a value that won't interfere in
        # the tests
        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "5")

        # testing if updates
        Client.update_credit_limit(10, self.trans)
        client.credit_limit = AutoReload
        self.assertEquals(client.credit_limit, 10)

        # testing if it does not update
        client.credit_limit = 200
        Client.update_credit_limit(0, self.trans)
        self.assertEquals(client.credit_limit, 200)

    def test_set_salary(self):
        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "10")

        client = self.create_client()

        self.assertEquals(client.salary, 0)
        self.assertEquals(client.credit_limit, 0)

        client.salary = 100

        self.assertEquals(client.salary, 100)
        self.assertEquals(client.credit_limit, 10)

        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "0")
        client.credit_limit = 100
        client.salary = 200

        self.assertEquals(client.salary, 200)
        self.assertEquals(client.credit_limit, 100)


class TestSupplier(_PersonFacetTest, DomainTest):
    facet = Supplier

    def testGetActiveSuppliers(self):
        for supplier in Supplier.get_active_suppliers(self.trans):
            self.assertEquals(supplier.status,
                              Supplier.STATUS_ACTIVE)

    def testGetAllSuppliers(self):
        query = AND(Person.q.name == "test",
                    Supplier.q.person_id == Person.q.id)

        suppliers = Person.select(query, connection=self.trans)
        self.assertEqual(suppliers.count(), 0)

        supplier = self.create_supplier()
        supplier.person.name = "test"

        suppliers = Person.select(query, connection=self.trans)
        self.assertEqual(suppliers.count(), 1)

    def testGetSupplierPurchase(self):
        supplier = self.create_supplier()

        self.failIf(supplier.get_supplier_purchases().count())

        order = self.create_receiving_order()
        order.purchase.supplier = supplier
        self.create_receiving_order_item(order)
        order.purchase.status = PurchaseOrder.ORDER_PENDING
        order.purchase.confirm()
        order.confirm()

        self.failUnless(supplier.get_supplier_purchases().count())

        last_date = supplier.get_last_purchase_date()
        self.assertEquals(last_date, order.purchase.open_date.date())


class TestEmployee(_PersonFacetTest, DomainTest):
    facet = Employee

    def testRoleHistory(self):
        #this test depends bug 2457
        employee = self.create_employee()
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            connection=self.trans,
                            salary=currency(500),
                            is_active=False)
        old_count = employee.get_role_history().count()
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            connection=self.trans,
                            salary=currency(900))
        new_count = employee.get_role_history().count()
        self.assertEquals(old_count + 1, new_count)

    def testGetActiveRoleHistory(self):
        employee = self.create_employee()

        #creating 2 active role history, asserting it fails
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            connection=self.trans,
                            salary=currency(230))
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            connection=self.trans,
                            salary=currency(320))
        self.assertRaises(ORMObjectIntegrityError,
                          employee.get_active_role_history)

        #now with one employeerolehistory
        #FIXME: this breaks in buildbot, figure out why.
        #history2.is_active = False
        #assert employee.get_role_history()


class TestUser(_PersonFacetTest, DomainTest):
    facet = LoginUser

    def testGetstatusStr(self):
        users = LoginUser.select(connection=self.trans)
        assert users
        user = users[0]
        user.is_active = False
        string = user.get_status_string()
        self.assertEquals(string, _(u'Inactive'))


class TestBranch(_PersonFacetTest, DomainTest):
    facet = Branch

    def testGetstatusStr(self):
        branches = Branch.select(connection=self.trans)
        assert branches
        branch = branches[0]
        branch.is_active = False
        string = branch.get_status_string()
        self.assertEquals(string, _(u'Inactive'))

    def testGetactiveBranches(self):
        person = self.create_person()
        Company(person=person, connection=self.trans)
        count = Branch.get_active_branches(self.trans).count()
        manager = self.create_employee()
        branch = Branch(person=person, connection=self.trans,
                        manager=manager, is_active=True)
        assert branch.get_active_branches(self.trans).count() == count + 1

    def test_is_from_same_company(self):
        branch1 = self.create_branch()
        branch1.person.company.cnpj = '111.222.333/0001-11'

        branch2 = self.create_branch()
        branch2.person.company.cnpj = '555.666.777/0001-11'
        self.assertFalse(branch1.is_from_same_company(branch2))

        branch2.person.company.cnpj = '111.222.333/0002-22'
        self.assertTrue(branch1.is_from_same_company(branch2))


class TestCreditProvider(_PersonFacetTest, DomainTest):
    facet = CreditProvider

    def testGetCardProviders(self):
        count = CreditProvider.get_card_providers(self.trans).count()
        facet = self._create_person_facet()
        self.assertEqual(facet.get_card_providers(self.trans).count(),
                         count + 1)


class SalesPersonTest(_PersonFacetTest, DomainTest):

    facet = SalesPerson

    def testGetactiveSalespersons(self):
        count = SalesPerson.get_active_salespersons(self.trans).count()
        salesperson = self.create_sales_person()
        one_more = salesperson.get_active_salespersons(self.trans).count()
        assert count + 1 == one_more

    def testGetStatusString(self):
        salesperson = self.create_sales_person()
        string = salesperson.get_status_string()
        self.assertEquals(string, _(u'Active'))


class TransporterTest(_PersonFacetTest, DomainTest):

    facet = Transporter

    def testGetStatusString(self):
        transporter = self.create_transporter()
        string = transporter.get_status_string()
        self.assertEquals(string, _(u'Active'))

    def testGetActiveTransporters(self):
        count = Transporter.get_active_transporters(self.trans).count()
        transporter = self.create_transporter()
        one_more = transporter.get_active_transporters(self.trans).count()
        self.assertEqual(count + 1, one_more)


class TestClientSalaryHistory(DomainTest):
    def testAdd(self):
        client = self.create_client()
        user = self.create_user()

        client.salary = 20
        ClientSalaryHistory.add(self.trans, 10, client, user)
        salary_histories = ClientSalaryHistory.select(connection=self.trans)
        last_salary_history = salary_histories[-1]

        self.assertEquals(last_salary_history.client, client)
        self.assertEquals(last_salary_history.new_salary, 20)
