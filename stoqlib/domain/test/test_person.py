# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/person.py'

from decimal import Decimal
import re

from dateutil.relativedelta import relativedelta
from kiwi.currency import currency
import mock
from storm.exceptions import NotOneError, IntegrityError
from storm.expr import And
from storm.store import AutoReload
from storm.tracer import BaseStatementTracer, install_tracer, remove_tracer_type

from stoqlib.database.expr import Age, Case, Date, DateTrunc, Interval
from stoqlib.domain.event import Event
from stoqlib.domain.person import (Calls, ContactInfo, ClientView, EmployeeView,
                                   SupplierView, TransporterView, BranchView,
                                   UserView, CreditCheckHistoryView, CallsView,
                                   ClientSalaryHistoryView)
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.exampledata import ExampleCreator
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import (Branch, Client, ClientCategory,
                                   ClientSalaryHistory, Company,
                                   Employee, EmployeeRole,
                                   EmployeeRoleHistory, Individual,
                                   LoginUser, Person, SalesPerson, Supplier,
                                   Transporter)
from stoqlib.domain.product import Product, ProductSupplierInfo
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sellable import ClientCategoryPrice
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.enums import LatePaymentPolicy
from stoqlib.exceptions import SellError, LoginError, DatabaseInconsistency
from stoqlib.lib.dateutils import localdate, localdatetime, localnow, localtoday
from stoqlib.database.runtime import get_current_branch
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class TestContactInfo(DomainTest):
    def test_get_description(self):
        contactinfo = ContactInfo(description=u'description')
        self.assertEquals(contactinfo.get_description(), u'description')


class TestEmployeeRoleHistory(DomainTest):
    def test_create(self):
        EmployeeRole(store=self.store, name=u'ajudante')

    def test_has_role(self):
        role = EmployeeRole(store=self.store, name=u'role')
        self.failIf(role.has_other_role(u'Role'))
        role = EmployeeRole(store=self.store, name=u'Role')
        self.failUnless(role.has_other_role(u'role'))


class TestEmployeeRole(DomainTest):
    def test_getdescription(self):
        role = self.create_employee_role()
        role.name = u'manager'
        self.assertEquals(role.name, role.get_description())


class TestPerson(DomainTest):
    def test_address(self):
        person = self.create_person()
        self.assertIsNone(person.get_main_address())
        ctlocs = self.store.find(CityLocation)
        assert not ctlocs.is_empty()
        ctloc = ctlocs[0]
        Address(store=self.store, person=person,
                city_location=ctloc, is_main_address=True)
        self.assertEquals(person.address, person.get_main_address())

    def test_addresses(self):
        person = self.create_person()
        assert not person.get_main_address()
        ctlocs = self.store.find(CityLocation)
        assert not ctlocs.is_empty()
        ctloc = ctlocs[0]
        address = Address(store=self.store, person=person,
                          city_location=ctloc, is_main_address=True)
        self.assertEquals(person.get_main_address(), address)

        self.assertEquals(len(list(person.addresses)), 1)
        self.assertEquals(list(person.addresses)[0], address)

    def test_calls(self):
        person = self.create_person()
        user = self.create_user()
        self.assertEquals(len(list(person.calls)), 0)

        call = Calls(store=self.store, date=localnow(),
                     description=u'', message=u'', person=person, attendant=user)
        self.assertEquals(len(list(person.calls)), 1)
        self.assertEquals(list(person.calls)[0], call)

    def test_contact_info(self):
        person = self.create_person()
        self.assertEquals(len(list(person.contact_infos)), 0)

        contact_info = ContactInfo(store=self.store, person=person)
        self.assertEquals(len(list(person.contact_infos)), 1)
        self.assertEquals(list(person.contact_infos)[0], contact_info)

    def test_get_address_string(self):
        person = self.create_person()
        self.assertEquals(person.get_address_string(), u'')
        ctloc = CityLocation(store=self.store)
        address = Address(store=self.store, person=person,
                          city_location=ctloc, street=u'bla', streetnumber=2,
                          district=u'fed', is_main_address=True)
        self.assertEquals(person.get_address_string(), _(u'%s %s, %s') % (
            address.street, address.streetnumber, address.district))

    def test_get_mobile_number_number(self):
        person = self.create_person()
        person.mobile_number = u'0321-12345'
        self.assertEquals(person.mobile_number, u'032112345')

    def test_get_phone_number_number(self):
        person = self.create_person()
        person.phone_number = u'0321-12345'
        self.assertEquals(person.get_phone_number_number(), 32112345)
        self.assertEquals(person.phone_number, u'032112345')

        person.phone_number = None
        self.assertEquals(person.get_phone_number_number(), 0)

    def test_get_fax_number_number(self):
        person = self.create_person()
        person.fax_number = u'0321-12345'
        self.assertEquals(person.fax_number, u'032112345')
        self.assertEquals(person.get_fax_number_number(), 32112345)

        person.fax_number = None
        self.assertEquals(person.get_fax_number_number(), 0)

    def test_get_formatted_phone_number(self):
        person = self.create_person()
        self.assertEquals(person.get_formatted_phone_number(), u"")
        phone = u'0321-1234'
        person.phone_number = phone
        self.assertEquals(person.get_formatted_phone_number(),
                          phone)

    def test_get_formatted_fax_number(self):
        person = self.create_person()
        self.assertEquals(person.get_formatted_fax_number(), u"")
        fax = u'0321-1234'
        person.fax_number = fax
        self.assertEquals(person.get_formatted_fax_number(),
                          fax)

    def test_get_formatted_mobile_number(self):
        person = self.create_person()
        self.assertEquals(person.get_formatted_mobile_number(), u"")
        person.mobile_number = u'91231234'
        self.assertEquals(person.get_formatted_mobile_number(),
                          u'9123-1234')

    def test_get_total_addresses(self):
        person = self.create_person()
        self.assertEquals(person.get_total_addresses(), 0)
        for i in range(3):
            self.create_address(person=person)
        self.assertEquals(person.get_total_addresses(), 3)

    def test_get_cnpj_or_cpf(self):
        person = self.create_person()
        Individual(store=self.store, person=person, cpf=u'123')
        self.assertEquals(person.get_cnpj_or_cpf(), u'123')

        Company(store=self.store, person=person, cnpj=u'456')
        self.assertEquals(person.get_cnpj_or_cpf(), u'456')

    def test_get_by_document(self):
        person = self.create_person()
        self.assertIsNone(person.get_by_document(self.store,
                                                 u'732.223.844-36'))
        self.assertIsNone(person.get_by_document(self.store,
                                                 u'57.310.832/0001-21'))
        individual = self.create_individual()
        individual.cpf = u'732.223.844-36'
        self.assertEquals(person.get_by_document(self.store, individual.cpf),
                          individual.person)
        company = self.create_company()
        company.cnpj = u'57.310.832/0001-21'
        self.assertEquals(person.get_by_document(self.store, company.cnpj),
                          company.person)


class _PersonFacetTest(object):
    facet = None

    def _create_person_facet(self):
        return ExampleCreator.create(self.store, self.facet.__name__)

    def test_inactivate(self):
        facet = self._create_person_facet()
        if not facet.is_active:
            facet.is_active = True
        facet.inactivate()
        self.failIf(facet.is_active)
        self.assertRaises(AssertionError, facet.inactivate)

    def test_activate(self):
        facet = self._create_person_facet()
        facet.is_active = False
        facet.activate()
        self.failUnless(facet.is_active)
        self.assertRaises(AssertionError, facet.activate)

    def test_get_description(self):
        facet = self._create_person_facet()
        self.failUnless(facet.get_description(), facet.person.name)


class TestIndividual(_PersonFacetTest, DomainTest):
    facet = Individual

    def test_get_status_string(self):
        individual = Individual(store=self.store)
        self.assertEquals(individual.get_status_string(), u'Active')
        individual.is_active = False
        self.assertEquals(individual.get_status_string(), u'Inactive')

    def test_individual(self):
        person = self.create_person()
        individual = Individual(person=person, store=self.store)

        statuses = individual.get_marital_statuses()
        self.assertEqual(type(statuses), list)
        self.failUnless(len(statuses) > 0)
        self.assertEqual(type(statuses[0]), tuple)
        self.assertEqual(type(statuses[0][0]), unicode)
        self.assertEqual(type(statuses[0][1]), unicode)

    def test_check_cpf_exist(self):
        individual = self.create_individual()
        individual.cpf = u'123.456.789-203'
        self.assertFalse(individual.check_cpf_exists(u'123.456.789-203'))
        individual2 = self.create_individual()
        individual2.cpf = u'123.456.789-203'
        self.assertTrue(individual.check_cpf_exists(u'123.456.789-203'))

    def test_get_c_p_f_number(self):
        individual = self.create_individual()
        individual.cpf = u''
        self.assertEquals(individual.get_cpf_number(), 0)
        individual.cpf = u'123.456.789-203'
        self.assertEquals(individual.get_cpf_number(), 123456789203)

    def test_get_birthday_date_query(self):
        start = localdate(2000, 3, 4)

        query = Individual.get_birthday_query(start)

        start_year = DateTrunc(u'year', Date(start))
        age_in_year = Age(Individual.birth_date,
                          DateTrunc(u'year', Individual.birth_date))
        test_query = (
            start_year + age_in_year +
            Case(condition=age_in_year < Age(Date(start), start_year),
                 result=Interval(u'1 year'),
                 else_=Interval(u'0 year'))
        )
        test_query = (test_query == Date(start))

        self.assertEquals(query, test_query)

        individuals = list(self.store.find(Individual, test_query))
        self.assertEquals(len(individuals), 0)

        client1 = self.create_client(u'Junio C. Hamano')
        client1.person.individual.birth_date = localdate(1972, 10, 15)
        client2 = self.create_client(u'Richard Stallman')
        client2.person.individual.birth_date = localdate(1989, 3, 4)
        client3 = self.create_client(u'Linus Torvalds')
        client3.person.individual.birth_date = localdate(2000, 3, 4)
        client4 = self.create_client(u'Guido van Rossum')
        client4.person.individual.birth_date = localdate(2005, 3, 4)

        individuals = list(self.store.find(Individual, test_query))
        self.assertEquals(len(individuals), 3)
        self.assertTrue(client2.person.individual in individuals)
        self.assertTrue(client3.person.individual in individuals)
        self.assertTrue(client4.person.individual in individuals)

    def test_get_birthday_interval_query(self):
        start = localdatetime(2000, 3, 1)
        end = localdatetime(2000, 3, 25)

        query = Individual.get_birthday_query(start, end)

        start_year = DateTrunc(u'year', Date(start))
        age_in_year = Age(Individual.birth_date,
                          DateTrunc(u'year', Individual.birth_date))
        test_query = (
            start_year + age_in_year +
            Case(condition=age_in_year < Age(Date(start), start_year),
                 result=Interval(u'1 year'),
                 else_=Interval(u'0 year'))
        )
        test_query = And(test_query >= Date(start),
                         test_query <= Date(end))

        self.assertEquals(query, test_query)

        individuals = list(self.store.find(Individual, test_query))
        self.assertEquals(len(individuals), 0)

        client1 = self.create_client(u'Junio C. Hamano')
        client1.person.individual.birth_date = localdate(1972, 10, 15)
        client2 = self.create_client(u'Richard Stallman')
        client2.person.individual.birth_date = localdate(1989, 3, 7)
        client3 = self.create_client(u'Linus Torvalds')
        client3.person.individual.birth_date = localdate(2000, 3, 4)
        client4 = self.create_client(u'Guido van Rossum')
        client4.person.individual.birth_date = localdate(2005, 3, 20)

        individuals = list(self.store.find(Individual, test_query))
        self.assertEquals(len(individuals), 3)
        self.assertTrue(client2.person.individual in individuals)
        self.assertTrue(client3.person.individual in individuals)
        self.assertTrue(client4.person.individual in individuals)


class TestCompany(_PersonFacetTest, DomainTest):
    facet = Company

    def test_get_status_string(self):
        company = self.create_company()
        self.assertEqual(company.get_status_string(), u'Active')
        company.is_active = False
        self.assertEqual(company.get_status_string(), u'Inactive')

    def test_get_cnpj_number_number(self):
        company = self.create_company()
        company.cnpj = u'111.222.333.444'
        self.assertEquals(company.get_cnpj_number(), 111222333444)
        company.cnpj = u'testcnpjasstring'
        self.assertFalse(company.get_cnpj_number())
        company.cnpj = None
        self.assertFalse(company.get_cnpj_number())

    def test_get_state_registry_number(self):
        company = self.create_company()
        self.assertFalse(company.get_state_registry_number())
        company.state_registry = u'12345.23'
        self.assertEquals(company.get_state_registry_number(), 1234523)
        company.state_registry = u'registry.company'
        self.assertFalse(company.get_state_registry_number())

    def test_check_cnpj_exists(self):
        company = self.create_company()
        company.cnpj = u'123456789'
        self.assertFalse(company.check_cnpj_exists(cnpj=u'123456789'))
        company2 = self.create_company()
        company2.cnpj = u'123456789'
        self.assertTrue(company.check_cnpj_exists(u'123456789'))


class TestClient(_PersonFacetTest, DomainTest):
    facet = Client

    def test_getname(self):
        client = self.create_client()
        client.person.name = u'Laun'
        self.assertEquals(client.get_name(), u'Laun')

    def test_get_active_items(self):
        company = self.create_company()
        company.fancy_name = u'fancy'
        company.person.name = u'Company'

        Client(person=company.person, store=self.store)

        items = Client.get_active_items(self.store)
        self.assertEquals(len(items), 5)
        self.assertEquals(items[4][0], u'fancy (Company)')

    def test_get_status_string(self):
        client = self.create_client()
        status = client.status
        status = client.statuses[status]
        self.assertEquals(client.get_status_string(), status)
        client.status = 999
        with self.assertRaises(DatabaseInconsistency):
            client.get_status_string()

    def test_active_setter(self):
        client = self.create_client()
        client.is_active = None
        self.assertFalse(client.is_active)
        client.is_active = True
        self.assertTrue(client.is_active)

    def test_get_active_clients(self):
        table = Client
        active_clients = table.get_active_clients(self.store).count()
        client1 = self.create_client()
        client1.status = table.STATUS_SOLVENT
        one_more_active_client = table.get_active_clients(self.store).count()
        client2 = self.create_client()
        client2.status = table.STATUS_INACTIVE
        self.assertEquals(active_clients + 1, one_more_active_client)

    def test_getclient_sales(self):
        client = self.store.find(Client)
        assert not client.is_empty()
        client = client[0]
        CfopData(code=u'123', description=u'bla', store=self.store)
        branches = self.store.find(Branch)
        assert not branches.is_empty()
        people = self.store.find(SalesPerson)
        assert not people.is_empty()
        count_sales = client.get_client_sales().count()
        sale = self.create_sale()
        sale.client = client
        products = self.store.find(Product)
        assert not products.is_empty()
        product = products[0]
        sale.add_sellable(product.sellable)
        one_more_sale = client.get_client_sales().count()
        self.assertEquals(count_sales + 1, one_more_sale)

    def test_get_client_returned_sales(self):
        client = self.create_client()

        # We cannot use count() since there is a group by in the viewable
        count_sales = len(list(client.get_client_returned_sales()))
        self.assertEquals(count_sales, 0)

        sale = self.create_sale()
        sale.client = client

        sellable = self.create_sellable()
        sale.add_sellable(sellable)

        sale.create_sale_return_adapter()

        after_return_count = len(list(client.get_client_returned_sales()))
        self.assertEquals(after_return_count, 1)

    def test_get_client_services(self):
        client = self.create_client()
        self.assertIsNone(client.get_client_services().one())
        sale = self.create_sale(client=client)
        sellable = self.create_sellable(description=u'Test')
        sale.add_sellable(sellable=sellable)
        service = self.create_service()
        service.sellable = sellable
        soldserviceview = client.get_client_services().one()
        self.assertEquals(soldserviceview.description, u'Test')

    def test_get_client_work_orders(self):
        client = self.create_client(name=u'Client Test')
        self.assertIsNone(client.get_client_work_orders().one())
        workorder = self.create_workorder()
        workorder.client = client
        result = client.get_client_work_orders().one()
        result_client_name = result.client.person.name
        self.assertEquals(result_client_name, u'Client Test')

    def test_get_client_products(self):
        client = self.create_client(name=u'Client Test')
        self.assertIsNone(client.get_client_products().one())
        sale = self.create_sale(client=client)
        sellable = self.create_sellable(description=u'Product')
        sale.add_sellable(sellable=sellable)
        sold_product_view = client.get_client_products().one()
        self.assertEquals(sold_product_view.description, u'Product')
        self.assertEquals(sold_product_view.client_name, u'Client Test')

    def test_get_client_payments(self):
        client = self.create_client()
        group = self.create_payment_group(payer=client.person)
        self.assertIsNone(client.get_client_payments().one())
        payment = self.create_payment(payment_type=Payment.TYPE_IN,
                                      group=group)
        item = self.create_sale_item()
        item.sale.client = client
        payment.sale = item.sale
        payment.group.payer = client.person
        group.payer = client.person
        result_client_name = client.get_client_payments().one().drawee
        self.assertEquals(result_client_name, client.person.name)

    def test_get_last_purchase_date(self):
        client = self.create_client()
        self.assertIsNone(client.get_last_purchase_date())
        sale_item = self.create_sale_item()
        sale_item.sale.client = client
        self.assertEquals(client.get_last_purchase_date(),
                          localnow().date())

    def test_client_category(self):
        categories = self.store.find(ClientCategory, name=u'Category')
        self.assertEquals(categories.count(), 0)

        category = self.create_client_category(u'Category')
        categories = self.store.find(ClientCategory, name=u'Category')
        self.assertEquals(categories.count(), 1)

        self.assertTrue(category.can_remove())
        category.remove()
        categories = self.store.find(ClientCategory, name=u'Category')
        self.assertEquals(categories.count(), 0)

        sellable = self.create_sellable(price=50)
        category = self.create_client_category(u'Category')
        ClientCategoryPrice(sellable=sellable,
                            category=category,
                            price=75,
                            store=self.store)
        self.assertFalse(category.can_remove())

    def test_can_purchase_allow_all(self):
        #: This parameter always allows the client to purchase, no matter if he
        #: has late payments
        sysparam.set_int(self.store, 'LATE_PAYMENTS_POLICY',
                         int(LatePaymentPolicy.ALLOW_SALES))

        client = self.create_client()
        bill_method = PaymentMethod.get_by_name(self.store, u'bill')
        check_method = PaymentMethod.get_by_name(self.store, u'check')
        money_method = PaymentMethod.get_by_name(self.store, u'money')
        credit_method = PaymentMethod.get_by_name(self.store, u'credit')
        store_credit_method = PaymentMethod.get_by_name(self.store,
                                                        u'store_credit')
        today = localtoday()

        # client can pay if he doesn't have any payments
        client.credit_limit = Decimal("1000")
        self.assertTrue(client.can_purchase(money_method, currency("200")))

        # client can pay if he has payments that are not overdue
        payment = self.create_payment(Payment.TYPE_IN, today, method=bill_method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertTrue(client.can_purchase(check_method, currency("200")))

        # client can pay even if he does have overdue payments
        payment = self.create_payment(payment_type=payment.TYPE_OUT, value=2000,
                                      method=credit_method)
        payment.set_pending()
        payment.pay()
        payment.group.payer = client.person
        self.assertTrue(client.can_purchase(credit_method, currency("200")))
        self.assertTrue(client.can_purchase(store_credit_method, currency("200")))

        # But he cannot pay if its above the credit limit
        self.assertRaises(SellError, client.can_purchase, store_credit_method, currency("1001"))

    def test_can_purchase_disallow_store_credit(self):
        #: This parameter disallows the client to purchase with store credit
        #: when he has late payments
        sysparam.set_int(self.store, 'LATE_PAYMENTS_POLICY',
                         int(LatePaymentPolicy.DISALLOW_STORE_CREDIT))

        client = self.create_client()
        bill_method = PaymentMethod.get_by_name(self.store, u'bill')
        check_method = PaymentMethod.get_by_name(self.store, u'check')
        money_method = PaymentMethod.get_by_name(self.store, u'money')
        store_credit_method = PaymentMethod.get_by_name(self.store,
                                                        u'store_credit')
        today = localtoday()

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
        sysparam.set_int(self.store, 'LATE_PAYMENTS_POLICY',
                         int(LatePaymentPolicy.DISALLOW_SALES))

        client = self.create_client()
        bill_method = PaymentMethod.get_by_name(self.store, u'bill')
        check_method = PaymentMethod.get_by_name(self.store, u'check')
        money_method = PaymentMethod.get_by_name(self.store, u'money')
        store_credit_method = PaymentMethod.get_by_name(self.store,
                                                        u'store_credit')
        today = localtoday()

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
        method = PaymentMethod.get_by_name(self.store, u'store_credit')

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
        sysparam.set_decimal(
            self.store,
            u"CREDIT_LIMIT_SALARY_PERCENT",
            Decimal(5))

        # testing if updates
        Client.update_credit_limit(10, self.store)
        client.credit_limit = AutoReload
        self.assertEquals(client.credit_limit, 10)

        # testing if it does not update
        client.credit_limit = 200
        Client.update_credit_limit(0, self.store)
        self.assertEquals(client.credit_limit, 200)

    def test_set_salary(self):
        sysparam.set_decimal(
            self.store,
            u"CREDIT_LIMIT_SALARY_PERCENT",
            Decimal("10"))

        client = self.create_client()

        self.assertEquals(client.salary, 0)
        self.assertEquals(client.credit_limit, 0)

        client.salary = 100

        self.assertEquals(client.salary, 100)
        self.assertEquals(client.credit_limit, 10)

        sysparam.set_decimal(
            self.store,
            u"CREDIT_LIMIT_SALARY_PERCENT",
            Decimal(0))
        client.credit_limit = 100
        client.salary = 200

        self.assertEquals(client.salary, 200)
        self.assertEquals(client.credit_limit, 100)

    def test_get_client_credit_transactions(self):
        method = self.store.find(PaymentMethod, method_name=u'credit').one()
        client = self.create_client()
        sale = self.create_sale(client=client)
        self.add_product(sale)
        self.add_payments(sale)
        sale.order()
        sale.confirm()

        returned_sale = ReturnedSale(sale=sale,
                                     branch=get_current_branch(self.store),
                                     store=self.store)
        ReturnedSaleItem(sale_item=list(sale.get_items())[0], quantity=1,
                         returned_sale=returned_sale,
                         store=self.store)
        sale.return_(returned_sale)
        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                                      value=100, method=method,
                                      group=sale.group)
        payment.set_pending()
        payment.pay()

        payment_domain_list = list(client.get_credit_transactions())
        self.assertTrue(len(payment_domain_list) == 1)

        payment_domain = payment_domain_list[0]
        self.assertEquals(payment.identifier, payment_domain.identifier)
        self.assertEquals(payment.paid_date, payment_domain.paid_date)
        self.assertEquals(payment.description, payment_domain.description)
        self.assertEquals(payment.paid_value, payment_domain.paid_value)

    def test_credit_account_balance(self):
        method = self.store.find(PaymentMethod, method_name=u'credit').one()
        client = self.create_client()
        sale = self.create_sale(client=client)
        self.add_product(sale)
        self.add_payments(sale)
        sale.order()
        sale.confirm()

        returned_sale = ReturnedSale(sale=sale,
                                     branch=get_current_branch(self.store),
                                     store=self.store)
        ReturnedSaleItem(sale_item=list(sale.get_items())[0], quantity=1,
                         returned_sale=returned_sale,
                         store=self.store)
        sale.return_(returned_sale)
        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                                      value=100, method=method,
                                      group=sale.group)
        payment.set_pending()
        payment.pay()

        self.assertEquals(client.credit_account_balance, 100)

        payment.payment_type = payment.TYPE_IN
        self.assertEquals(client.credit_account_balance, -100)


class TestClientCategory(DomainTest):
    def test_get_description(self):
        category = self.create_client_category(name=u'Control')
        self.assertEquals(category.get_description(), u'Control')


class TestSupplier(_PersonFacetTest, DomainTest):
    facet = Supplier

    def test_get_status_string(self):
        supplier = self.create_supplier()
        self.assertEquals(supplier.get_status_string(), u'Active')
        supplier.is_active = False
        self.assertEquals(supplier.get_status_string(), u'Inactive')

    def test_get_active_items(self):
        company = self.create_company()
        company.fancy_name = u'fancy'
        company.person.name = u'Company'

        Supplier(person=company.person, store=self.store)

        items = Supplier.get_active_items(self.store)
        self.assertEquals(len(items), 2)
        self.assertEquals(items[1][0], u'fancy (Company)')

    def test_get_name(self):
        supplier = self.create_supplier(name=u'Supplier Test')
        self.assertEquals(supplier.get_name(), u'Supplier Test')

    def test_get_active_suppliers(self):
        for supplier in Supplier.get_active_suppliers(self.store):
            self.assertEquals(supplier.status,
                              Supplier.STATUS_ACTIVE)

    def test_get_all_suppliers(self):
        query = And(Person.name == u"test",
                    Supplier.person_id == Person.id)

        suppliers = self.store.find(Person, query)
        self.assertEqual(suppliers.count(), 0)

        supplier = self.create_supplier()
        supplier.person.name = u"test"

        suppliers = self.store.find(Person, query)
        self.assertEqual(suppliers.count(), 1)

    def test_get_supplier_purchase(self):
        supplier = self.create_supplier()

        self.failIf(supplier.get_supplier_purchases().count())

        order = self.create_receiving_order()
        order.purchase_orders.find()[0].supplier = supplier
        self.create_receiving_order_item(order)
        purchase = order.purchase_orders.find()[0]
        purchase.status = PurchaseOrder.ORDER_PENDING
        purchase.confirm()
        order.confirm()

        self.failUnless(supplier.get_supplier_purchases().count())

        last_date = supplier.get_last_purchase_date()
        purchase = order.purchase_orders.find()[0]
        self.assertEquals(last_date, purchase.open_date.date())


class TestEmployee(_PersonFacetTest, DomainTest):
    facet = Employee

    def test_get_status_string(self):
        employee = self.create_employee()
        self.assertEquals(employee.get_status_string(), u'Active')
        employee.is_active = False
        self.assertEquals(employee.get_status_string(), u'Inactive')

    def test_get_active_employees(self):
        employee = self.create_employee()
        employees = list(employee.get_active_employees(store=self.store))
        results = list(self.store.find(Employee, status=Employee.STATUS_NORMAL))
        self.assertEquals(employees, results)

    def test_role_history(self):
        # this test depends bug 2457
        employee = self.create_employee()
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            store=self.store,
                            salary=currency(500),
                            is_active=False)
        old_count = employee.get_role_history().count()
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            store=self.store,
                            salary=currency(900))
        new_count = employee.get_role_history().count()
        self.assertEquals(old_count + 1, new_count)

    def test_get_active_role_history(self):
        employee = self.create_employee()

        # creating 2 active role history, asserting it fails
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            store=self.store,
                            salary=currency(230))
        EmployeeRoleHistory(role=employee.role,
                            employee=employee,
                            store=self.store,
                            salary=currency(320))
        self.assertRaises(NotOneError, employee.get_active_role_history)

        # now with one employeerolehistory
        # FIXME: this breaks in buildbot, figure out why.
        # history2.is_active = False
        # assert employee.get_role_history()


class TestUser(_PersonFacetTest, DomainTest):
    facet = LoginUser

    def test_get_status_string(self):
        user = self.create_user()
        self.assertEquals(user.get_status_string(), u'Active')
        user.is_active = False
        self.assertEquals(user.get_status_string(), u'Inactive')

    def test_authenticate(self):
        branch = get_current_branch(store=self.store)
        user = self.create_user()
        with self.assertRaises(LoginError) as error:
            user.authenticate(store=self.store, username=u'username',
                              pw_hash=u'anything', current_branch=branch)
        expected = "Invalid user or password"
        self.assertEquals(str(error.exception), expected)

        with self.assertRaises(LoginError) as error:
            user.authenticate(store=self.store, username=u'username',
                              pw_hash=user.pw_hash, current_branch=branch)
        expected = u'This user does not have access to this branch.'
        self.assertEquals(str(error.exception), expected)

        user.add_access_to(branch=branch)
        result = user.authenticate(store=self.store, username=u'username',
                                   pw_hash=user.pw_hash, current_branch=branch)
        self.assertEquals(result, user)

    def test_status_str(self):
        user = self.create_user()
        self.assertEquals(user.status_str, u'Active')
        user.is_active = False
        self.assertEquals(user.status_str, u'Inactive')

    def test_get_associated_branches(self):
        user = self.create_user()
        self.assertIsNone(user.get_associated_branches().one())
        branch = get_current_branch(store=self.store)
        new_branch = self.create_branch(name=u'New Branch')
        user.add_access_to(branch)
        user.add_access_to(new_branch)
        self.assertEquals(user.get_associated_branches().count(), 2)

    def test_has_access_to(self):
        user = self.create_user()
        branch = self.create_branch()
        self.assertFalse(user.has_access_to(branch))
        user.add_access_to(branch)
        self.assertTrue(user.has_access_to(branch))
        user_profile = self.create_user_profile(name=u'admin')
        self.create_profile_settings(user_profile=user_profile,
                                     app=u'admin')
        user.profile = user_profile
        self.assertTrue(user.has_access_to(branch))

    @mock.patch('stoqlib.domain.person.get_current_station')
    @mock.patch('stoqlib.domain.person.Event.log')
    def test_login(self, log, get_current_station):
        user = self.create_user()
        user.login()
        station = get_current_station(store=self.store)

        expected = _(u"User '%s' logged in on '%s'") % (user.username,
                                                        station.name)
        log.assert_called_with(self.store, Event.TYPE_USER, expected)

        get_current_station.return_value = None
        user.login()
        expected = _(u"User '%s' logged in") % (user.username, )
        log.assert_called_with(self.store, Event.TYPE_USER, expected)

    @mock.patch('stoqlib.domain.person.get_current_station')
    @mock.patch('stoqlib.domain.person.Event.log')
    def test_logout(self, log, get_current_station):
        user = self.create_user()
        new_station = self.create_station()
        get_current_station.return_value = new_station
        station = get_current_station()
        user.logout()

        expected = _(u"User '%s' logged out from '%s'") % (user.username,
                                                           station.name)
        log.assert_called_with(self.store, Event.TYPE_USER, expected)

        get_current_station.return_value = None
        user.logout()
        expected = _(u"User '%s' logged out") % (user.username, )
        log.assert_called_with(self.store, Event.TYPE_USER, expected)

    def test_get_active_users(self):
        active_users_count = LoginUser.get_active_users(self.store).count()

        user = self.create_user()
        active_users = LoginUser.get_active_users(self.store)
        self.assertTrue(user in active_users)
        self.assertEqual(active_users.count(), active_users_count + 1)

        user.inactivate()
        active_users = LoginUser.get_active_users(self.store)
        self.assertFalse(user in active_users)
        self.assertEqual(active_users.count(), active_users_count)


class TestBranch(_PersonFacetTest, DomainTest):
    facet = Branch

    def test_get_status_string(self):
        branch = self.create_branch()
        self.assertEquals(branch.get_status_string(), u'Active')
        branch.is_active = False
        self.assertEquals(branch.get_status_string(), u'Inactive')

    def test_get_active_items(self):
        company = self.create_company()
        company.fancy_name = u'fancy'
        company.person.name = u'Company'

        Branch(person=company.person, store=self.store)

        items = Branch.get_active_items(self.store)
        self.assertEquals(len(items), 3)
        self.assertEquals(items[2][0], u'fancy')

    def test_set_acronym(self):
        branch = self.create_branch()
        self.assertIsNone(branch.acronym)
        branch.set_acronym(value=u'Async')
        self.assertEquals(branch.acronym, u'Async')
        branch.set_acronym(value=u'')
        self.assertIsNone(branch.acronym)

    def test_check_acronym_exists(self):
        branch = self.create_branch()
        branch.set_acronym(value=u'acronym')

        branch2 = self.create_branch()
        self.assertTrue(branch2.check_acronym_exists(acronym=u'acronym'))
        branch2.set_acronym(value=u'acronym')

        with self.assertRaises(IntegrityError):
            branch.check_acronym_exists(acronym=u'acronym')

    def test_getstatus_str(self):
        branches = self.store.find(Branch)
        assert not branches.is_empty()
        branch = branches[0]
        branch.is_active = False
        string = branch.get_status_string()
        self.assertEquals(string, _(u'Inactive'))

    def test_getactive_branches(self):
        person = self.create_person()
        Company(person=person, store=self.store)
        count = Branch.get_active_branches(self.store).count()
        manager = self.create_employee()
        branch = Branch(person=person, store=self.store,
                        manager=manager, is_active=True)
        assert branch.get_active_branches(self.store).count() == count + 1

    def test_get_active_remote_branches(self):
        current_branch = get_current_branch(self.store)
        self.assertIn(current_branch, Branch.get_active_branches(self.store))
        self.assertNotIn(current_branch,
                         Branch.get_active_remote_branches(self.store))

    def test_is_from_same_company(self):
        branch1 = self.create_branch()
        branch1.person.company.cnpj = u'111.222.333/0001-11'

        branch2 = self.create_branch()
        branch2.person.company.cnpj = u'555.666.777/0001-11'
        self.assertFalse(branch1.is_from_same_company(branch2))

        branch2.person.company.cnpj = u'111.222.333/0002-22'
        self.assertTrue(branch1.is_from_same_company(branch2))

        branch2.person.company.cnpj = None
        self.assertFalse(branch1.is_from_same_company(branch2))


class TestSalesPerson(_PersonFacetTest, DomainTest):

    facet = SalesPerson

    def test_getactive_salespersons(self):
        count = len(SalesPerson.get_active_salespersons(self.store))
        salesperson = self.create_sales_person()
        one_more = len(salesperson.get_active_salespersons(self.store))
        assert count + 1 == one_more

    def test_get_status_string(self):
        salesperson = self.create_sales_person()
        self.assertEquals(salesperson.get_status_string(), _(u'Active'))
        salesperson.is_active = False
        self.assertEquals(salesperson.get_status_string(), _(u'Inactive'))

    def test_get_active_items(self):
        salesperson = self.create_sales_person()
        salesperson.person.name = u'Teste sales person'

        items = SalesPerson.get_active_items(self.store)
        self.assertEquals(len(items), 6)
        self.assertEquals(items[5][0], u'Teste sales person')


class TestTransporter(_PersonFacetTest, DomainTest):

    facet = Transporter

    def test_get_status_string(self):
        transporter = self.create_transporter()
        self.assertEquals(transporter.get_status_string(), _(u'Active'))
        transporter.is_active = False
        self.assertEquals(transporter.get_status_string(), _(u'Inactive'))

    def test_get_active_transporters(self):
        count = Transporter.get_active_transporters(self.store).count()
        transporter = self.create_transporter()
        one_more = transporter.get_active_transporters(self.store).count()
        self.assertEqual(count + 1, one_more)

    def test_get_active_items(self):
        transporter = self.create_transporter()
        transporter.person.name = u'Teste transporter'

        items = Transporter.get_active_items(self.store)
        self.assertEquals(len(items), 2)
        self.assertEquals(items[1][0], u'Teste transporter')


class TestClientSalaryHistory(DomainTest):
    def test_add(self):
        client = self.create_client()
        user = self.create_user()

        client.salary = 20
        ClientSalaryHistory.add(self.store, 10, client, user)
        salary_histories = self.store.find(ClientSalaryHistory)
        last_salary_history = salary_histories.order_by(ClientSalaryHistory.id).last()

        self.assertEquals(last_salary_history.client, client)
        self.assertEquals(last_salary_history.new_salary, 20)


class TestClientView(DomainTest):
    def test_get_active_clients(self):
        client1 = self.create_client()
        client1.status = Client.STATUS_INACTIVE

        total_clients = self.store.find(Client).count()
        actives = ClientView.get_active_clients(store=self.store).count()

        # There is one client that is not active.
        self.assertEquals(total_clients, (actives + 1))

    def test_get_description(self):
        client = self.create_client()
        company = self.create_company()
        company.person = client.person
        result = self.store.find(ClientView, id=client.id).one()
        self.assertEquals(result.get_description(), u'Client (Dummy shop)')

    def test_status_str(self):
        client = self.create_client()
        client.person.individual.cpf = u'123.123.123.-12'
        result = self.store.find(ClientView, id=client.id).one()
        self.assertEquals(result.status_str, 'Solvent')

    def test_cnpj_or_cpf(self):
        client = self.create_client()
        client.person.individual.cpf = u'123.123.123.-12'
        result = self.store.find(ClientView, id=client.id).one()
        self.assertEquals(result.cnpj_or_cpf, u'123.123.123.-12')
        company = self.create_company()
        company.cnpj = u'60.746.948.0001-12'
        company.person = client.person
        result = self.store.find(ClientView, id=client.id).one()
        self.assertEquals(result.cnpj_or_cpf, u'60.746.948.0001-12')


class TestEmployeeView(DomainTest):
    def test_get_description(self):
        employee = self.create_employee()
        employee.person.name = u'Test'
        result = self.store.find(EmployeeView, id=employee.id).one()
        self.assertEquals(result.get_description(), u'Test')

    def test_get_status_string(self):
        employee = self.create_employee()
        employee.status = employee.STATUS_AWAY
        result = self.store.find(EmployeeView, id=employee.id).one()
        self.assertEquals(result.get_status_string(),
                          employee.statuses[employee.STATUS_AWAY])

    def test_get_active_employees(self):
        for i in range(4):
            if i % 2 == 0:
                employee = self.create_employee()
                employee.status = employee.STATUS_OFF
                employee.is_active = True
            elif i % 3 == 0:
                employee2 = self.create_employee()
                employee2.status = employee.STATUS_NORMAL
                employee2.is_active = False
            else:
                employee3 = self.create_employee()
                employee3.status = employee3.STATUS_NORMAL
        active = EmployeeView.get_active_employees(store=self.store)
        self.assertEquals(active.count(), 6)


class TestSupplierView(DomainTest):
    def test_get_description(self):
        supplier = self.create_supplier()
        view = self.store.find(SupplierView, id=supplier.id).one()
        self.assertEquals(view.get_description(), u'Supplier (Company Name)')

        # With no fancy_name, get_description should fallback
        # to the person's name alone
        supplier.person.company.fancy_name = u""
        view = self.store.find(SupplierView, id=supplier.id).one()
        self.assertEquals(view.get_description(), u'Supplier')

    def test_get_status_string(self):
        supplier = self.create_supplier()
        supplier.status = supplier.STATUS_BLOCKED
        view = self.store.find(SupplierView, id=supplier.id).one()
        self.assertEquals(view.get_status_string(),
                          supplier.statuses[supplier.STATUS_BLOCKED])


class TestTransporterView(DomainTest):
    def test_get_description(self):
        transporter = self.create_transporter()
        view = self.store.find(TransporterView, id=transporter.id).one()
        self.assertEquals(view.get_description(), u'John')


class TestBranchView(DomainTest):
    def test_get_description(self):
        branch = self.create_branch()
        view = self.store.find(BranchView, id=branch.id).one()
        self.assertEquals(view.get_description(), u'Dummy')

    def test_status_str(self):
        branch = self.create_branch()
        view = self.store.find(BranchView, id=branch.id).one()
        self.assertEquals(view.status_str, u'Active')
        branch.is_active = False
        view = self.store.find(BranchView, id=branch.id).one()
        self.assertEquals(view.status_str, u'Inactive')


class TestUserView(DomainTest):
    def test_get_description(self):
        user = self.create_user()
        view = self.store.find(UserView, id=user.id).one()
        self.assertEquals(view.get_description(), u'individual')

    def test_status_str(self):
        user = self.create_user()
        view = self.store.find(UserView, id=user.id).one()
        self.assertEquals(view.status_str, u'Active')
        user.is_active = False
        view = self.store.find(UserView, id=user.id).one()
        self.assertEquals(view.status_str, u'Inactive')


class TestCreditCheckHistoryView(DomainTest):
    def test_find_by_client(self):
        client = self.create_client()
        result = CreditCheckHistoryView.find_by_client(store=self.store,
                                                       client=client).count()
        self.assertEquals(result, 0)
        check_history = self.create_credit_check_history()
        check_history.client = client
        result = CreditCheckHistoryView.find_by_client(store=self.store,
                                                       client=client).count()
        self.assertEquals(result, 1)


class TestCallsView(DomainTest):
    def test_get_description(self):
        call = self.create_call()
        view = self.store.find(CallsView, id=call.id).one()
        self.assertEquals(view.get_description(), u'Test call')

    def test_find_by_client_date(self):
        call = self.create_call()
        client = self.create_client()
        result = CallsView.find_by_client_date(store=self.store,
                                               client=client,
                                               date=Date(localnow())).count()
        self.assertFalse(result)
        call.date = localnow()
        result = CallsView.find_by_client_date(store=self.store,
                                               client=call.person,
                                               date=Date(localnow())).count()
        self.assertTrue(result)
        date = Date(localnow()), Date(localnow())
        result = CallsView.find_by_client_date(store=self.store,
                                               client=call.person,
                                               date=date).count()
        self.assertTrue(result)

    def test_find_by_date(self):
        call = self.create_call()
        result = CallsView.find_by_date(store=self.store,
                                        date=Date(localnow())).count()
        self.assertFalse(result)
        call.date = localnow()
        result = CallsView.find_by_date(store=self.store,
                                        date=Date(localnow())).count()
        self.assertTrue(result)


class TestClientSalaryHistoryView(DomainTest):
    def test_find_by_client(self):
        client = self.create_client()
        result = ClientSalaryHistoryView.find_by_client(store=self.store,
                                                        client=client).count()
        self.assertFalse(result)
        ClientSalaryHistory(client=client)
        result = ClientSalaryHistoryView.find_by_client(store=self.store,
                                                        client=client).count()
        self.assertTrue(result)


class StoqlibUpdateTracer(BaseStatementTracer):

    def __init__(self, expected_updates):
        self.expected_updates = expected_updates
        self.statements = []

    def reset(self):
        self.statements = []

    def connection_raw_execute(self, connection, cursor, statement, params):
        self.statements.append((statement, params))

    def __enter__(self):
        install_tracer(self)

    def __exit__(self, exc_type, exc_value, traceback):
        remove_tracer_type(type(self))
        # something wrong happend, let it propagate
        if traceback:
            return
        statements = [i[0] for i in self.statements
                      if i[0].startswith('UPDATE')]

        # Now check the executed queries
        for (real, expected) in zip(statements, self.expected_updates):
            assert re.match(expected, real), (expected, real)
        assert len(statements) == len(self.expected_updates)


class TestPersonMerging(DomainTest):
    person_updates = [
        'UPDATE calls SET person_id=%s WHERE calls.person_id = %s',
        'UPDATE contact_info SET person_id=%s WHERE contact_info.person_id = %s',
        'UPDATE fiscal_book_entry SET drawee_id=%s WHERE fiscal_book_entry.drawee_id = %s',
        'UPDATE optical_medic SET person_id=%s WHERE optical_medic.person_id = %s',
        'UPDATE payment_group SET payer_id=%s WHERE payment_group.payer_id = %s',
        'UPDATE payment_group SET recipient_id=%s WHERE payment_group.recipient_id = %s',
        'UPDATE stock_decrease SET person_id=%s WHERE stock_decrease.person_id = %s',
    ]

    employee_updates = [
        'UPDATE employee_role_history SET is_active=%s'
        ' WHERE employee_role_history.employee_id = %s',
        'UPDATE branch SET manager_id=%s WHERE branch.manager_id = %s',  # nopep8
        'UPDATE employee_role_history SET employee_id=%s WHERE employee_role_history.employee_id = %s',  # nopep8
        'UPDATE production_order SET responsible_id=%s WHERE production_order.responsible_id = %s',  # nopep8
        'UPDATE stock_decrease SET removed_by_id=%s WHERE stock_decrease.removed_by_id = %s',  # nopep8
        'UPDATE transfer_order SET cancel_responsible_id=%s WHERE transfer_order.cancel_responsible_id = %s',  # nopep8
        'UPDATE transfer_order SET destination_responsible_id=%s WHERE transfer_order.destination_responsible_id = %s',  # nopep8
        'UPDATE transfer_order SET source_responsible_id=%s WHERE transfer_order.source_responsible_id = %s',  # nopep8
        'UPDATE work_order SET execution_responsible_id=%s WHERE work_order.execution_responsible_id = %s',  # nopep8
        'UPDATE work_order SET quote_responsible_id=%s WHERE work_order.quote_responsible_id = %s',  # nopep8
    ]

    def test_merge_client(self):
        person = self.create_person()
        person.email = u'teste@email.com'
        person.mobile_number = u'999'
        person.notes = u'Person 1'
        client = self.create_client(person=person)
        address = self.create_address(person=person)
        address.streetnumber = 123
        sale = self.create_sale(client=client)
        self.assertEquals(list(client.sales), [sale])

        person2 = self.create_person()
        person2.phone_number = u'123'
        person2.mobile_number = u'456'
        person2.notes = u'Person 2'
        client2 = self.create_client(person=person2)
        address2 = self.create_address(person=person2)
        address2.streetnumber = None
        self.store.flush()

        address_update = 'UPDATE address SET streetnumber=%s WHERE address.id = %s'
        email_update = 'UPDATE person SET email=%s WHERE person.id = %s'
        notes_update = 'UPDATE person SET notes=%s WHERE person.id = %s'
        expected_updates = [
            'UPDATE client_salary_history SET client_id=%s WHERE client_salary_history.client_id = %s',  # nopep8
            'UPDATE credit_check_history SET client_id=%s WHERE credit_check_history.client_id = %s',  # nopep8
            'UPDATE loan SET client_id=%s WHERE loan.client_id = %s',  # nopep8
            'UPDATE payment_renegotiation SET client_id=%s WHERE payment_renegotiation.client_id = %s',  # nopep8
            'UPDATE sale SET client_id=%s WHERE sale.client_id = %s',  # nopep8
            'UPDATE work_order SET client_id=%s WHERE work_order.client_id = %s',  # nopep8

            # Optical plugin
            'UPDATE optical_patient_history SET client_id=%s WHERE optical_patient_history.client_id = %s',  # nopep8
            'UPDATE optical_patient_measures SET client_id=%s WHERE optical_patient_measures.client_id = %s',  # nopep8
            'UPDATE optical_patient_test SET client_id=%s WHERE optical_patient_test.client_id = %s',  # nopep8
            'UPDATE optical_patient_visual_acuity SET client_id=%s WHERE optical_patient_visual_acuity.client_id = %s',  # nopep8
        ]
        tracer = StoqlibUpdateTracer(sorted(expected_updates) +
                                     [notes_update, address_update, email_update] +
                                     sorted(self.person_updates))
        with tracer:
            person2.merge_with(person)

        self.store.invalidate()
        self.assertEquals(sale.client, client2)
        # The person2 didnt have an email, but now it shold have
        self.assertEquals(person2.email, 'teste@email.com')
        # The phone and mobile for the person2 should remain the same
        self.assertEquals(person2.phone_number, '123')
        self.assertEquals(person2.mobile_number, '456')
        # The notes should be merged
        self.assertEquals(person2.notes, 'Person 2\nPerson 1')

        # The address should also be updated
        self.assertEquals(address2.streetnumber, 123)

    def test_merge_supplier(self):
        supplier = self.create_supplier()
        supplier2 = self.create_supplier()

        cnpj_query = 'UPDATE company SET cnpj=%s WHERE company.id = %s'
        info_query = (
            'UPDATE product_supplier_info SET supplier_id=%s'
            ' WHERE product_supplier_info.supplier_id = %s AND product_supplier_info.product_id'
            '  NOT IN  \(SELECT product_supplier_info.product_id FROM product_supplier_info'
            ' WHERE product_supplier_info.supplier_id = %s\)')
        expected_updates = [
            # Supplier
            'UPDATE purchase_order SET supplier_id=%s WHERE purchase_order.supplier_id = %s',
            'UPDATE receiving_order SET supplier_id=%s WHERE receiving_order.supplier_id = %s',
        ]
        tracer = StoqlibUpdateTracer([cnpj_query, info_query] + expected_updates
                                     + self.person_updates)
        with tracer:
            supplier.person.merge_with(supplier2.person)

    def test_merge_employee(self):
        emp = self.create_employee()
        emp2 = self.create_employee()

        tracer = StoqlibUpdateTracer(self.employee_updates + self.person_updates)
        with tracer:
            emp.person.merge_with(emp2.person)

    def test_merge_login_user(self):
        facet = self.create_user()
        facet2 = self.create_user()

        # this is a regexp, so the () should be escaped.
        access_query = (
            'UPDATE user_branch_access SET user_id=%s WHERE user_branch_access.user_id = %s'
            ' AND user_branch_access.branch_id  NOT IN '
            ' \(SELECT user_branch_access.branch_id FROM user_branch_access'
            ' WHERE user_branch_access.user_id = %s\)')

        expected_updates = [
            'UPDATE calls SET attendant_id=%s WHERE calls.attendant_id = %s',
            'UPDATE client_salary_history SET user_id=%s WHERE client_salary_history.user_id = %s',
            'UPDATE credit_check_history SET user_id=%s WHERE credit_check_history.user_id = %s',  # nopep8
            'UPDATE inventory SET responsible_id=%s WHERE inventory.responsible_id = %s',  # nopep8
            'UPDATE loan SET responsible_id=%s WHERE loan.responsible_id = %s',  # nopep8
            'UPDATE payment_comment SET author_id=%s WHERE payment_comment.author_id = %s',  # nopep8
            'UPDATE payment_renegotiation SET responsible_id=%s WHERE payment_renegotiation.responsible_id = %s',  # nopep8
            'UPDATE production_item_quality_result SET tested_by_id=%s WHERE production_item_quality_result.tested_by_id = %s',  # nopep8
            'UPDATE production_produced_item SET produced_by_id=%s WHERE production_produced_item.produced_by_id = %s',  # nopep8
            'UPDATE purchase_order SET responsible_id=%s WHERE purchase_order.responsible_id = %s',  # nopep8
            'UPDATE receiving_order SET responsible_id=%s WHERE receiving_order.responsible_id = %s',  # nopep8
            'UPDATE returned_sale SET confirm_responsible_id=%s WHERE returned_sale.confirm_responsible_id = %s',  # nopep8
            'UPDATE returned_sale SET responsible_id=%s WHERE returned_sale.responsible_id = %s',  # nopep8
            'UPDATE returned_sale SET undo_responsible_id=%s WHERE returned_sale.undo_responsible_id = %s',  # nopep8
            'UPDATE sale_comment SET author_id=%s WHERE sale_comment.author_id = %s',  # nopep8
            'UPDATE stock_decrease SET responsible_id=%s WHERE stock_decrease.responsible_id = %s',  # nopep8
            'UPDATE stock_transaction_history SET responsible_id=%s WHERE stock_transaction_history.responsible_id = %s',  # nopep8
            'UPDATE till SET responsible_close_id=%s WHERE till.responsible_close_id = %s',  # nopep8
            'UPDATE till SET responsible_open_id=%s WHERE till.responsible_open_id = %s',  # nopep8
            'UPDATE work_order_history SET user_id=%s WHERE work_order_history.user_id = %s',  # nopep8
            'UPDATE work_order_package SET receive_responsible_id=%s WHERE work_order_package.receive_responsible_id = %s',  # nopep8
            'UPDATE work_order_package SET send_responsible_id=%s WHERE work_order_package.send_responsible_id = %s',  # nopep8

            # optical plugin
            'UPDATE optical_patient_history SET responsible_id=%s WHERE optical_patient_history.responsible_id = %s',  # nopep8
            'UPDATE optical_patient_measures SET responsible_id=%s WHERE optical_patient_measures.responsible_id = %s',  # nopep8
            'UPDATE optical_patient_test SET responsible_id=%s WHERE optical_patient_test.responsible_id = %s',  # nopep8
            'UPDATE optical_patient_visual_acuity SET responsible_id=%s WHERE optical_patient_visual_acuity.responsible_id = %s',  # nopep8
        ]
        tracer = StoqlibUpdateTracer([access_query] + sorted(expected_updates)
                                     + self.person_updates)
        with tracer:
            facet.person.merge_with(facet2.person)

    def test_merge_branch(self):
        facet = self.create_branch()
        facet2 = self.create_branch()

        with self.assertRaises(AssertionError):
            facet.person.merge_with(facet2.person)

    def test_merge_sales_person(self):
        facet = self.create_sales_person()
        facet2 = self.create_sales_person()

        expected_updates = [
            'UPDATE sale SET salesperson_id=%s WHERE sale.salesperson_id = %s',
        ]
        tracer = StoqlibUpdateTracer(expected_updates + self.employee_updates + self.person_updates)
        with tracer:
            facet.person.merge_with(facet2.person)

    def test_merge_transporter(self):
        facet = self.create_transporter()
        facet2 = self.create_transporter()

        expected_updates = [
            'UPDATE delivery SET transporter_id=%s WHERE delivery.transporter_id = %s',
            'UPDATE purchase_order SET transporter_id=%s WHERE purchase_order.transporter_id = %s',
            'UPDATE receiving_order SET transporter_id=%s WHERE receiving_order.transporter_id = %s',  # nopep8
            'UPDATE sale SET transporter_id=%s WHERE sale.transporter_id = %s',
        ]
        tracer = StoqlibUpdateTracer(expected_updates + self.person_updates)
        with tracer:
            facet.person.merge_with(facet2.person)

    def test_merge_with_different_facets(self):
        transporter = self.create_transporter()
        old_person = transporter.person
        client = self.create_client()

        client.person.merge_with(transporter.person)
        self.assertEquals(transporter.person, client.person)

        # The old person should still exist, and point to this new person:
        self.assertEquals(old_person.merged_with_id, client.person.id)
        self.assertEquals(old_person.transporter, None)

    def test_merge_login_user_branch_access(self):
        branch1 = self.create_branch()
        branch2 = self.create_branch()
        branch3 = self.create_branch()

        user1 = self.create_user()
        user2 = self.create_user()

        # First user will access branches 1 and 2
        user1.add_access_to(branch1)
        user1.add_access_to(branch2)

        # Second user will access branches 2 and 3
        user2.add_access_to(branch2)
        user2.add_access_to(branch3)

        # Now merging user 2 into 1, he should have access to all branches
        user1.merge_with(user2)

        assert user1.has_access_to(branch1)
        assert user1.has_access_to(branch2)
        assert user1.has_access_to(branch3)

    def test_merge_supplier_product_info(self):
        sup1 = self.create_supplier()
        sup2 = self.create_supplier()

        product1 = self.create_product()
        product2 = self.create_product()

        # product 1 is supplied by supplier 1 and vice-versa
        self.create_product_supplier_info(supplier=sup1, product=product1)
        self.create_product_supplier_info(supplier=sup2, product=product2)

        #Now, merging supplier2 into supplier 1 will also merge the infos
        sup1.merge_with(sup2)

        infos = list(self.store.find(ProductSupplierInfo, supplier=sup1))
        self.assertEquals(len(infos), 2)

        products = set(i.product for i in infos)
        self.assertEquals(products, set([product1, product2]))
