# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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

import datetime
from decimal import Decimal

from stoqdrivers.enum import TaxType

from stoqlib.database.orm import const
from stoqlib.database.runtime import (get_current_station,
                                      get_current_branch,
                                      get_current_user)
from stoqlib.lib.parameters import sysparam

# Do not remove, these are used by doctests


def create_person(trans):
    return ExampleCreator.create(trans, 'Person')


def create_branch(trans):
    return ExampleCreator.create(trans, 'Branch')


def create_supplier(trans):
    return ExampleCreator.create(trans, 'Supplier')


def create_employee(trans):
    return ExampleCreator.create(trans, 'Employee')


def create_salesperson(trans):
    return ExampleCreator.create(trans, 'SalesPerson')


def create_client(trans):
    return ExampleCreator.create(trans, 'Client')


def create_individual(trans):
    return ExampleCreator.create(trans, 'Individual')


def create_user(trans):
    return ExampleCreator.create(trans, 'LoginUser')


def create_storable(trans):
    return ExampleCreator.create(trans, 'Storable')


def create_product(trans):
    return ExampleCreator.create(trans, 'Product')


def create_sellable(trans):
    return ExampleCreator.create(trans, 'Sellable')


def create_sellable_unit(trans):
    return ExampleCreator.create(trans, 'SellableUnit')


def create_sale(trans):
    return ExampleCreator.create(trans, 'Sale')


def create_sale_item_icms(trans):
    return ExampleCreator.create(trans, 'SaleItemIcms')


def create_stock_decrease(trans):
    return ExampleCreator.create(trans, 'StockDecrease')


def create_city_location(trans):
    return ExampleCreator.create(trans, 'CityLocation')


def create_parameter_data(trans):
    return ExampleCreator.create(trans, 'ParameterData')


def create_company(trans):
    return ExampleCreator.create(trans, 'Company')


def create_till(trans):
    return ExampleCreator.create(trans, 'Till')


def create_user_profile(trans):
    return ExampleCreator.create(trans, 'UserProfile')


def get_station(trans):
    return ExampleCreator.create(trans, 'BranchStation')


def get_location(trans):
    return ExampleCreator.create(trans, 'CityLocation')


def create_production_order(trans):
    return ExampleCreator.create(trans, 'ProductionOrder')


def create_production_item(trans):
    return ExampleCreator.create(trans, 'ProductionItem')


def create_production_material(trans):
    return ExampleCreator.create(trans, 'ProductionMaterial')


def create_production_service(trans):
    return ExampleCreator.create(trans, 'ProductionService')


def create_loan(trans):
    return ExampleCreator.create(trans, 'Loan')


def create_loan_item(trans):
    return ExampleCreator.create(trans, 'LoanItem')


def create_call(trans):
    return ExampleCreator.create(trans, 'Calls')


def create_credit_check_history(trans):
    return ExampleCreator.create(trans, 'CreditCheckHistory')


def create_client_category(trans):
    return ExampleCreator.create(trans, 'ClientCategory')


def create_client_category_price(trans):
    return ExampleCreator.create(trans, 'ClientCategoryPrice')


def create_bank_account(trans):
    return ExampleCreator.create(trans, 'BankAccount')


def create_quote_group(trans):
    return ExampleCreator.create(trans, 'QuoteGroup')


class ExampleCreator(object):
    def __init__(self):
        self.clear()

    # Public API

    @classmethod
    def create(cls, trans, name):
        ec = cls()
        ec.set_transaction(trans)
        return ec.create_by_type(name)

    def clear(self):
        self._role = None

    def clean_domain(self, domains):
        # The database used for tests is the example one. So, when the tests
        # start, there is already data that could cause unwanted behavior in
        # a few tests, like GUI search ones.
        for domain in domains:
            for item in domain.select(connection=self.trans):
                domain.delete(item.id, self.trans)

    def set_transaction(self, trans):
        self.trans = trans

    def create_by_type(self, model_type):
        known_types = {
            'Account': self.create_account,
            'AccountTransaction': self.create_account_transaction,
            'Address': self.create_address,
            'PaymentMethod': self.get_payment_method,
            'Sellable': self.create_sellable,
            'PaymentGroup': self.create_payment_group,
            'BranchStation': self.get_station,
            'CityLocation': self.get_location,
            'CfopData': self.create_cfop_data,
            'ClientCategory': self.create_client_category,
            'ClientCategoryPrice': self.create_client_category_price,
            'EmployeeRole': self.create_employee_role,
            'FiscalBookEntry': self.create_fiscal_book_entry,
            'Client': self.create_client,
            'Company': self.create_company,
            'Branch': self.create_branch,
            'Employee': self.create_employee,
            'Image': self.create_image,
            'Individual': self.create_individual,
            'Inventory': self.create_inventory,
            'InventoryItem': self.create_inventory_item,
            'SalesPerson': self.create_sales_person,
            'Supplier': self.create_supplier,
            'Transporter': self.create_transporter,
            'LoginUser': self.create_user,
            'Payment': self.create_payment,
            'ParameterData': self.create_parameter_data,
            'Person': self.create_person,
            'Branch': self.create_branch,
            'Company': self.create_company,
            'Client': self.create_client,
            'CreditProvider': self.create_credit_provider,
            'Employee': self.create_employee,
            'Individual': self.create_individual,
            'SalesPerson': self.create_sales_person,
            'Supplier': self.create_supplier,
            'Transporter': self.create_transporter,
            'LoginUser': self.create_user,
            'MilitaryData': self.create_military_data,
            'Product': self.create_product,
            'ProductSupplierInfo': self.create_product_supplier_info,
            'Storable': self.create_storable,
            'PurchaseOrder': self.create_purchase_order,
            'PurchaseItem': self.create_purchase_order_item,
            'ReceivingOrder': self.create_receiving_order,
            'ReceivingOrderItem': self.create_receiving_order_item,
            'ReturnedSale': self.create_returned_sale,
            'Sale': self.create_sale,
            'SaleItem': self.create_sale_item,
            'SaleItemIcms': self.create_sale_item_icms,
            'SaleItemIpi': self.create_sale_item_ipi,
            'Sellable': self.create_sellable,
            'SellableCategory': self.create_sellable_category,
            'SellableTaxConstant': self.create_sellable_tax_constant,
            'SellableUnit': self.create_sellable_unit,
            'Service': self.create_service,
            'StockDecrease': self.create_stock_decrease,
            'StockDecreaseItem': self.create_stock_decrease_item,
            'Till': self.create_till,
            'UserProfile': self.create_user_profile,
            'VoterData': self.create_voter_data,
            'WorkPermitData': self.create_work_permit_data,
            'ProductionOrder': self.create_production_order,
            'ProductionItem': self.create_production_item,
            'ProductionMaterial': self.create_production_material,
            'ProductionService': self.create_production_service,
            'Loan': self.create_loan,
            'LoanItem': self.create_loan_item,
            'Account': self.create_account,
            'AccountTransaction': self.create_account_transaction,
            'TransferOrder': self.create_transfer,
            'PaymentCategory': self.create_payment_category,
            'FiscalDayHistory': self.create_fiscal_day_history,
            'Calls': self.create_call,
            'CreditCheckHistory': self.create_credit_check_history,
            'BankAccount': self.create_bank_account,
            'QuoteGroup': self.create_quote_group,
            'Quotation': self.create_quotation,
            'InvoicePrinter': self.create_invoice_printer,
            'Delivery': self.create_delivery,
            'Liaison': self.create_liaison,
            'PaymentRenegotiation': self.create_payment_renegotiation,
            }
        if isinstance(model_type, basestring):
            model_name = model_type
        else:
            model_name = model_type.__name__
        if model_name in known_types:
            return known_types[model_name]()

    def create_person(self, name='John'):
        from stoqlib.domain.person import Person
        return Person(name=name, connection=self.trans)

    def create_branch(self, name='Dummy', phone_number='12345678',
                      fax_number='87564321'):
        from stoqlib.domain.person import Branch, Company, Person
        person = Person(name=name, phone_number=phone_number,
                        fax_number=fax_number, connection=self.trans)
        self.create_address(person=person)
        fancy_name = name + ' shop'
        Company(person=person, fancy_name=fancy_name,
                connection=self.trans)
        return Branch(person=person, connection=self.trans)

    def create_supplier(self, name='Supplier', fancy_name='Company Name'):
        from stoqlib.domain.person import Company, Person, Supplier
        person = Person(name=name, connection=self.trans)
        Company(person=person, fancy_name=fancy_name,
                cnpj='90.117.749/7654-80',
                connection=self.trans)
        return Supplier(person=person, connection=self.trans)

    def create_employee_role(self, name='Role'):
        from stoqlib.domain.person import EmployeeRole
        role = EmployeeRole.selectOneBy(name=name, connection=self.trans)
        if not role:
            role = EmployeeRole(name=name, connection=self.trans)
        if not self._role:
            self._role = role
        return role

    def create_employee(self, name="SalesPerson"):
        from stoqlib.domain.person import Employee, Individual, Person
        person = Person(name=name, connection=self.trans)
        Individual(person=person, connection=self.trans)
        return Employee(person=person,
                        role=self.create_employee_role(),
                        connection=self.trans)

    def create_sales_person(self):
        from stoqlib.domain.person import SalesPerson
        employee = self.create_employee()
        return SalesPerson(person=employee.person, connection=self.trans)

    def create_client(self, name='Client'):
        from stoqlib.domain.person import Client, Individual, Person
        person = Person(name=name, connection=self.trans)
        Individual(person=person, connection=self.trans)
        return Client(person=person, connection=self.trans)

    def create_individual(self):
        from stoqlib.domain.person import Individual, Person
        person = Person(name='individual', connection=self.trans)
        return Individual(person=person, connection=self.trans)

    def create_user(self, username='username'):
        from stoqlib.domain.person import LoginUser
        individual = self.create_individual()
        profile = self.create_user_profile()
        return LoginUser(person=individual.person,
                         username=username,
                         password='password',
                         profile=profile,
                         connection=self.trans)

    def create_storable(self, product=None):
        from stoqlib.domain.product import Storable
        if not product:
            sellable = self.create_sellable()
            product = sellable.product
        return Storable(product=product, connection=self.trans)

    def create_product_supplier_info(self, supplier=None, product=None):
        from stoqlib.domain.product import ProductSupplierInfo
        product = product or self.create_product(create_supplier=False)
        supplier = supplier or self.create_supplier()
        ProductSupplierInfo(
            connection=self.trans,
            supplier=supplier,
            product=product,
            is_main_supplier=True,
            )

    def create_product(self, price=None, create_supplier=True,
                       branch=None, stock=None):
        from stoqlib.domain.product import Storable
        sellable = self.create_sellable(price=price)
        if create_supplier:
            self.create_product_supplier_info(product=sellable.product)
        product = sellable.product
        if not branch:
            branch = get_current_branch(self.trans)

        if stock:
            storable = Storable(product=product, connection=self.trans)
            storable.increase_stock(stock, branch, unit_cost=10)

        return product

    def create_product_component(self, product=None, component=None):
        from stoqlib.domain.product import ProductComponent
        return ProductComponent(product=product or self.create_product(),
                                component=component or self.create_product(),
                                connection=self.trans)

    def create_sellable(self, price=None, product=True,
                        description='Description'):
        from stoqlib.domain.product import Product
        from stoqlib.domain.service import Service
        from stoqlib.domain.sellable import Sellable
        tax_constant = sysparam(self.trans).DEFAULT_PRODUCT_TAX_CONSTANT
        if price is None:
            price = 10
        sellable = Sellable(cost=125,
                            tax_constant=tax_constant,
                            price=price,
                            description=description,
                            connection=self.trans)
        if product:
            Product(sellable=sellable, connection=self.trans)
        else:
            Service(sellable=sellable, connection=self.trans)
        return sellable

    def create_sellable_unit(self, description=u'', allow_fraction=True):
        from stoqlib.domain.sellable import SellableUnit
        return SellableUnit(connection=self.trans,
                            description=description,
                            allow_fraction=allow_fraction)

    def create_sellable_category(self, description=None, parent=None):
        from stoqlib.domain.sellable import SellableCategory
        description = description or "Category"
        return SellableCategory(description=description,
                                category=parent,
                                connection=self.trans)

    def create_sale(self, id_=None, branch=None, client=None):
        from stoqlib.domain.sale import Sale
        from stoqlib.domain.till import Till
        till = Till.get_current(self.trans)
        if till is None:
            till = self.create_till()
            till.open_till()
        salesperson = self.create_sales_person()
        group = self.create_payment_group()
        if client:
            group.payer = client.person
        extra_args = dict()
        if id_:
            extra_args['id'] = id_
            extra_args['identifier'] = id_

        return Sale(coupon_id=0,
                    open_date=const.NOW(),
                    salesperson=salesperson,
                    branch=branch or get_current_branch(self.trans),
                    cfop=sysparam(self.trans).DEFAULT_SALES_CFOP,
                    group=group,
                    client=client,
                    connection=self.trans,
                    **extra_args)

    def create_returned_sale(self):
        sale = self.create_sale()
        return sale.create_sale_return_adapter()

    def create_sale_item(self, sale=None, product=True):
        from stoqlib.domain.sale import SaleItem
        sellable = self.create_sellable(product=product)
        return SaleItem(connection=self.trans,
                        quantity=1,
                        price=100,
                        sale=sale or self.create_sale(),
                        sellable=sellable)

    def create_sale_item_icms(self):
        from stoqlib.domain.taxes import SaleItemIcms
        return SaleItemIcms(connection=self.trans)

    def create_sale_item_ipi(self):
        from stoqlib.domain.taxes import SaleItemIpi
        return SaleItemIpi(connection=self.trans)

    def create_client_category(self, name='Category 1'):
        from stoqlib.domain.person import ClientCategory
        return ClientCategory(name=name, connection=self.trans)

    def create_client_category_price(self, category=None, sellable=None,
                                     price=None):
        from stoqlib.domain.sellable import ClientCategoryPrice
        return ClientCategoryPrice(sellable=sellable or self.create_sellable(price=50),
                                   category=category or self.create_client_category(),
                                   price=price or 100,
                                   connection=self.trans)

    def create_stock_decrease_item(self):
        from stoqlib.domain.stockdecrease import StockDecreaseItem
        return StockDecreaseItem(stock_decrease=self.create_stock_decrease(),
                                 sellable=self.create_sellable(),
                                 quantity=1,
                                 connection=self.trans)

    def create_stock_decrease(self, branch=None, user=None, reason=''):
        from stoqlib.domain.stockdecrease import StockDecrease

        employee = self.create_employee()
        cfop = self.create_cfop_data()
        return StockDecrease(responsible=user or get_current_user(self.trans),
                             removed_by=employee,
                             branch=branch or get_current_branch(self.trans),
                             status=StockDecrease.STATUS_INITIAL,
                             cfop=cfop,
                             reason=reason,
                             connection=self.trans)

    def create_city_location(self):
        from stoqlib.domain.address import CityLocation
        return CityLocation.get_or_create(
            self.trans,
            country='United States',
            city='Los Angeles',
            state='Californa',
            )

    def create_address(self, person=None, city_location=None):
        from stoqlib.domain.address import Address
        city_location = city_location or self.create_city_location()
        return Address(street='Mainstreet',
                       streetnumber=138,
                       district='Cidade Araci',
                       postal_code='12345-678',
                       complement='Compl',
                       is_main_address=True,
                       person=person,
                       city_location=city_location,
                       connection=self.trans)

    def create_parameter_data(self):
        from stoqlib.domain.parameter import ParameterData
        return ParameterData.select(connection=self.trans)[0]

    def create_company(self):
        from stoqlib.domain.person import Company, Person
        person = Person(name='Dummy', connection=self.trans)
        return Company(person=person, fancy_name='Dummy shop',
                       connection=self.trans)

    def create_till(self):
        from stoqlib.domain.till import Till
        station = get_current_station(self.trans)
        return Till(connection=self.trans, station=station)

    def create_user_profile(self):
        from stoqlib.domain.profile import UserProfile
        return UserProfile(connection=self.trans, name='assistant')

    def create_profile_settings(self, user_profile=None, app='admin'):
        from stoqlib.domain.profile import ProfileSettings
        if not user_profile:
            user_profile = self.create_user_profile()
        return ProfileSettings(connection=self.trans, app_dir_name=app,
                               has_permission=True,
                               user_profile=user_profile)

    def create_purchase_order(self, supplier=None, branch=None):
        from stoqlib.domain.purchase import PurchaseOrder
        group = self.create_payment_group()
        return PurchaseOrder(supplier=supplier or self.create_supplier(),
                             branch=branch or self.create_branch(),
                             group=group,
                             responsible=get_current_user(self.trans),
                             connection=self.trans)

    def create_quote_group(self, branch=None):
        from stoqlib.domain.purchase import QuoteGroup
        if not branch:
            branch = get_current_branch(self.trans)
        return QuoteGroup(connection=self.trans, branch=branch)

    def create_quotation(self):
        from stoqlib.domain.purchase import Quotation
        purchase_order = self.create_purchase_order()
        quote_group = self.create_quote_group(branch=purchase_order.branch)
        return Quotation(connection=self.trans,
                         group=quote_group,
                         purchase=purchase_order,
                         branch=purchase_order.branch)

    def create_purchase_order_item(self, order=None):
        if not order:
            order = self.create_purchase_order()

        from stoqlib.domain.purchase import PurchaseItem
        return PurchaseItem(connection=self.trans,
                            quantity=8, quantity_received=0,
                            cost=125, base_cost=125,
                            sellable=self.create_sellable(),
                            order=order)

    def create_production_order(self):
        from stoqlib.domain.production import ProductionOrder
        return ProductionOrder(branch=get_current_branch(self.trans),
                               responsible=self.create_employee(),
                               description='production',
                               connection=self.trans)

    def create_production_item(self, quantity=1, order=None):
        from stoqlib.domain.product import ProductComponent, Storable
        from stoqlib.domain.production import (ProductionItem,
                                               ProductionMaterial)
        product = self.create_product(10)
        Storable(product=product, connection=self.trans)
        component = self.create_product(5)
        Storable(product=component, connection=self.trans)
        ProductComponent(product=product,
                         component=component,
                         connection=self.trans)

        if not order:
            order = self.create_production_order()
        component = list(product.get_components())[0]
        ProductionMaterial(product=component.component,
                           order=order,
                           needed=quantity,
                           connection=self.trans)

        return ProductionItem(product=product,
                              order=order,
                              quantity=quantity,
                              connection=self.trans)

    def create_production_material(self):
        from stoqlib.domain.production import ProductionMaterial
        production_item = self.create_production_item()
        order = production_item.order
        component = list(production_item.get_components())[0]
        return ProductionMaterial.selectOneBy(product=component.component,
                                              order=order,
                                              connection=self.trans)

    def create_production_service(self):
        from stoqlib.domain.production import ProductionService
        service = self.create_service()
        return ProductionService(service=service,
                                 order=self.create_production_order(),
                                 connection=self.trans)

    def create_cfop_data(self):
        from stoqlib.domain.fiscal import CfopData
        return CfopData(connection=self.trans, code=u'123',
                        description=u'test')

    def create_receiving_order(self, purchase_order=None, branch=None, user=None):
        from stoqlib.domain.receiving import ReceivingOrder
        if purchase_order is None:
            purchase_order = self.create_purchase_order()
        cfop = self.create_cfop_data()
        cfop.code = '1.102'
        return ReceivingOrder(connection=self.trans,
                              invoice_number=222,
                              supplier=purchase_order.supplier,
                              responsible=user or get_current_user(self.trans),
                              purchase=purchase_order,
                              branch=branch or get_current_branch(self.trans),
                              cfop=cfop)

    def create_receiving_order_item(self, receiving_order=None, sellable=None,
                                    purchase_item=None, quantity=8):
        from stoqlib.domain.receiving import ReceivingOrderItem
        from stoqlib.domain.product import Storable
        if receiving_order is None:
            receiving_order = self.create_receiving_order()
        if sellable is None:
            sellable = self.create_sellable()
            product = sellable.product
            Storable(product=product, connection=self.trans)
        if purchase_item is None:
            purchase_item = receiving_order.purchase.add_item(
                sellable, quantity)
        return ReceivingOrderItem(connection=self.trans,
                                  quantity=quantity, cost=125,
                                  purchase_item=purchase_item,
                                  sellable=sellable,
                                  receiving_order=receiving_order)

    def create_fiscal_book_entry(self, entry_type=None, icms_value=0,
                                 iss_value=0, ipi_value=0,
                                 invoice_number=None):
        from stoqlib.domain.payment.group import PaymentGroup
        from stoqlib.domain.fiscal import FiscalBookEntry
        payment_group = PaymentGroup(connection=self.trans)
        return FiscalBookEntry(invoice_number=invoice_number,
                               icms_value=icms_value,
                               iss_value=iss_value,
                               ipi_value=ipi_value,
                               entry_type=entry_type,
                               cfop=self.create_cfop_data(),
                               branch=self.create_branch(),
                               drawee=self.create_person(),
                               payment_group=payment_group,
                               connection=self.trans)

    def create_icms_ipi_book_entry(self):
        from stoqlib.domain.fiscal import FiscalBookEntry
        return self.create_fiscal_book_entry(FiscalBookEntry.TYPE_PRODUCT,
                                             icms_value=10, ipi_value=10,
                                             invoice_number=200)

    def create_iss_book_entry(self):
        from stoqlib.domain.fiscal import FiscalBookEntry
        return self.create_fiscal_book_entry(FiscalBookEntry.TYPE_SERVICE,
                                             iss_value=10,
                                             invoice_number=201)

    def create_service(self, description='Description', price=10):
        from stoqlib.domain.sellable import Sellable, SellableTaxConstant
        from stoqlib.domain.service import Service
        tax_constant = SellableTaxConstant.get_by_type(
            TaxType.SERVICE, self.trans)
        sellable = Sellable(tax_constant=tax_constant,
                            price=price,
                            description=description,
                            connection=self.trans)
        service = Service(sellable=sellable, connection=self.trans)
        return service

    def create_transporter(self, name='John'):
        from stoqlib.domain.person import Company, Transporter
        person = self.create_person(name)
        Company(person=person, connection=self.trans)
        return Transporter(person=person,
                           connection=self.trans)

    def create_bank_account(self, account=None):
        from stoqlib.domain.account import BankAccount
        return BankAccount(connection=self.trans,
                           bank_branch='2666-1',
                           bank_account='20.666-1',
                           bank_number=1,
                           account=account or self.create_account())

    def create_credit_provider(self):
        from stoqlib.domain.person import Company, CreditProvider
        person = self.create_person()
        Company(person=person, connection=self.trans)
        return CreditProvider(person=person,
                              connection=self.trans,
                              short_name='Velec',
                              open_contract_date=datetime.date(2006, 01, 01))

    def create_payment(self, payment_type=None, date=None, value=None,
                       method=None, branch=None, group=None):
        from stoqlib.domain.payment.payment import Payment
        if payment_type is None:
            payment_type = Payment.TYPE_OUT
        if not date:
            date = datetime.date.today()
        return Payment(group=group or self.create_payment_group(),
                       description='Test payment',
                       branch=branch or get_current_branch(self.trans),
                       open_date=date,
                       due_date=date,
                       value=Decimal(10),
                       till=None,
                       method=method or self.get_payment_method(),
                       category=None,
                       connection=self.trans,
                       payment_type=payment_type)

    def create_card_payment(self, date=None, provider_id='AMEX'):
        from stoqlib.domain.payment.method import CreditCardData
        from stoqlib.domain.person import CreditProvider
        if date is None:
            date = datetime.datetime.today()

        provider = CreditProvider.selectOneBy(provider_id=provider_id,
                                              connection=self.trans)
        payment = self.create_payment(date=date,
                                      method=self.get_payment_method('card'))

        CreditCardData(payment=payment, provider=provider,
                       connection=self.trans)

        return payment

    def create_payment_group(self):
        from stoqlib.domain.payment.group import PaymentGroup
        return PaymentGroup(connection=self.trans)

    def create_sellable_tax_constant(self):
        from stoqdrivers.enum import TaxType
        from stoqlib.domain.sellable import SellableTaxConstant
        return SellableTaxConstant(description="18",
                                   tax_type=int(TaxType.CUSTOM),
                                   tax_value=18,
                                   connection=self.trans)

    def create_station(self):
        from stoqlib.domain.station import BranchStation
        return BranchStation(name="station",
                             branch=get_current_branch(self.trans),
                             connection=self.trans)

    def create_transfer_order(self, source_branch=None, dest_branch=None):
        from stoqlib.domain.transfer import TransferOrder
        source_branch = source_branch or self.create_branch("Source")
        dest_branch = dest_branch or self.create_branch("Dest")
        source_resp = self.create_employee("Ipswich")
        dest_resp = self.create_employee("Bolton")
        return TransferOrder(source_branch=source_branch,
                             destination_branch=dest_branch,
                             source_responsible=source_resp,
                             destination_responsible=dest_resp,
                             connection=self.trans)

    def create_transfer_order_item(self, order=None, quantity=5, sellable=None):
        from stoqlib.domain.product import Product, Storable
        from stoqlib.domain.sellable import Sellable
        from stoqlib.domain.transfer import TransferOrderItem
        if not order:
            order = self.create_transfer_order()
        if not sellable:
            sellable = self.create_sellable()
            sellable.status = Sellable.STATUS_AVAILABLE
        product = Product.selectOneBy(sellable=sellable, connection=self.trans)
        if not product.storable:
            storable = Storable(product=product, connection=self.trans)
            storable.increase_stock(quantity, order.source_branch)
        return TransferOrderItem(sellable=sellable,
                                 transfer_order=order,
                                 quantity=quantity,
                                 connection=self.trans)

    def create_inventory(self, branch=None):
        from stoqlib.domain.inventory import Inventory
        branch = branch or self.create_branch("Main")
        return Inventory(branch=branch, connection=self.trans)

    def create_inventory_item(self, inventory=None, quantity=5):
        from stoqlib.domain.inventory import InventoryItem
        from stoqlib.domain.product import Storable
        if not inventory:
            inventory = self.create_inventory()
        sellable = self.create_sellable()
        product = sellable.product
        storable = Storable(product=product, connection=self.trans)
        storable.increase_stock(quantity, inventory.branch)
        return InventoryItem(product=product,
                             product_cost=product.sellable.cost,
                             recorded_quantity=quantity,
                             inventory=inventory,
                             connection=self.trans)

    def create_loan(self, branch=None, client=None):
        from stoqlib.domain.loan import Loan
        user = get_current_user(self.trans)
        return Loan(responsible=user,
                    client=client,
                    branch=branch or get_current_branch(self.trans),
                    connection=self.trans)

    def create_loan_item(self, loan=None, product=None, quantity=1):
        from stoqlib.domain.loan import LoanItem
        from stoqlib.domain.product import Storable
        loan = loan or self.create_loan()
        if not product:
            sellable = self.create_sellable()
            storable = Storable(product=sellable.product,
                                connection=self.trans)
            storable.increase_stock(10, loan.branch)
        else:
            sellable = product.sellable
            storable = product.storable
        return LoanItem(loan=loan, sellable=sellable, price=10,
                        quantity=quantity, connection=self.trans)

    def get_payment_method(self, name='money'):
        from stoqlib.domain.payment.method import PaymentMethod
        return PaymentMethod.get_by_name(self.trans, name)

    def get_station(self):
        return get_current_station(self.trans)

    def get_location(self):
        from stoqlib.domain.address import CityLocation
        return CityLocation.get_default(self.trans)

    def add_product(self, sale, price=None, quantity=1):
        from stoqlib.domain.product import Storable
        product = self.create_product(price=price)
        sellable = product.sellable
        sellable.tax_constant = self.create_sellable_tax_constant()
        sale.add_sellable(sellable, quantity=quantity)
        storable = Storable(product=product, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))
        return sellable

    def add_payments(self, obj, method_type='money', installments=1,
                     date=None):
        from stoqlib.domain.sale import Sale
        from stoqlib.domain.purchase import PurchaseOrder
        assert installments > 0
        if not date:
            date = datetime.datetime.today()
        elif isinstance(date, datetime.date):
            date = datetime.datetime(date.year, date.month, date.day)

        method = self.get_payment_method(method_type)
        due_dates = self.create_installment_dates(date, installments)
        if isinstance(obj, Sale):
            total = obj.get_total_sale_amount()
            payment = method.create_inpayments(obj.group, obj.branch, total,
                                               due_dates=due_dates)
        elif isinstance(obj, PurchaseOrder):
            total = obj.get_purchase_total()
            payment = method.create_outpayments(obj.group, obj.branch, total,
                                                due_dates=due_dates)
        else:
            raise ValueError(obj)

        for p in payment:
            p.open_date = date

        return payment

    def create_installment_dates(self, date, installments):
        due_dates = []
        for i in range(installments):
            due_dates.append(date + datetime.timedelta(days=i))
        return due_dates

    def create_account(self):
        from stoqlib.domain.account import Account
        return Account(description="Test Account",
                       account_type=Account.TYPE_CASH,
                       connection=self.trans)

    def create_account_transaction(self, account, value=1):
        from stoqlib.domain.account import AccountTransaction
        return AccountTransaction(
            description="Test Account Transaction",
            code="Code",
            date=datetime.datetime.now(),
            value=value,
            account=account,
            source_account=sysparam(self.trans).IMBALANCE_ACCOUNT,
            connection=self.trans)

    def create_transfer(self):
        from stoqlib.domain.transfer import TransferOrder
        return TransferOrder(source_branch=self.create_branch(),
                             destination_branch=self.create_branch(),
                             source_responsible=self.create_employee(),
                             destination_responsible=self.create_employee(),
                             connection=self.trans)

    def create_payment_category(self):
        from stoqlib.domain.payment.category import PaymentCategory
        return PaymentCategory(name="category",
                               color='#ff0000',
                               connection=self.trans)

    def create_fiscal_day_history(self):
        from stoqlib.domain.devices import FiscalDayHistory
        return FiscalDayHistory(emission_date=datetime.datetime.today(),
                                reduction_date=datetime.datetime.today(),
                                serial="123456",
                                serial_id=12345,
                                coupon_start=1,
                                coupon_end=100,
                                cro=1,
                                crz=1,
                                period_total=100,
                                total=100,
                                station=self.create_station(),
                                connection=self.trans)

    def create_call(self, person=None, attendant=None):
        from stoqlib.domain.person import Calls
        return Calls(date=datetime.date(2011, 1, 1),
                     message="Test call message",
                     person=person or self.create_person(),
                     attendant=attendant or self.create_user(),
                     description="Test call",
                     connection=self.trans)

    def create_credit_check_history(self, user=None, client=None):
        from stoqlib.domain.person import CreditCheckHistory
        return CreditCheckHistory(check_date=datetime.date(2011, 1, 1),
                                  identifier="identifier123",
                                  status=CreditCheckHistory.STATUS_NOT_INCLUDED,
                                  notes="random note",
                                  user=user or self.create_user(),
                                  client=client or self.create_client(),
                                  connection=self.trans)

    def create_commission_source(self, category=None):
        from stoqlib.domain.commission import CommissionSource
        if not category:
            sellable = self.create_sellable()
        else:
            sellable = None
        return CommissionSource(direct_value=10,
                                category=category,
                                sellable=sellable,
                                installments_value=1,
                                connection=self.trans)

    def create_invoice_printer(self):
        from stoqlib.domain.invoice import InvoicePrinter
        return InvoicePrinter(device_name='/dev/ttyS0',
                              description='Invoice Printer',
                              connection=self.trans)

    def create_delivery(self):
        from stoqlib.domain.sale import Delivery
        return Delivery(connection=self.trans)

    def create_liaison(self):
        from stoqlib.domain.person import Liaison
        return Liaison(connection=self.trans,
                       person=self.create_person(),
                       name='name',
                       phone_number='12345678')

    def create_work_permit_data(self):
        from stoqlib.domain.person import WorkPermitData
        return WorkPermitData(connection=self.trans)

    def create_military_data(self):
        from stoqlib.domain.person import MilitaryData
        return MilitaryData(connection=self.trans)

    def create_voter_data(self):
        from stoqlib.domain.person import VoterData
        return VoterData(connection=self.trans)

    def create_image(self):
        from stoqlib.domain.image import Image
        return Image(
            connection=self.trans,
            description="Test image",
            )

    def create_payment_renegotiation(self, group=None):
        from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
        return PaymentRenegotiation(responsible=get_current_user(self.trans),
                                    branch=get_current_branch(self.trans),
                                    group=group or self.create_payment_group(),
                                    client=self.create_client(),
                                    connection=self.trans)
