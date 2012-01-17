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
from stoqlib.domain.interfaces import (IBranch, ICompany, IEmployee,
                                       IIndividual, ISupplier,
                                       IStorable, ISalesPerson,
                                       IClient, IUser, ITransporter,
                                       ICreditProvider)
from stoqlib.lib.parameters import sysparam

# Do not remove, these are used by doctests


def create_person(trans):
    return ExampleCreator.create(trans, 'Person')


def create_branch(trans):
    return ExampleCreator.create(trans, 'IBranch')


def create_supplier(trans):
    return ExampleCreator.create(trans, 'ISupplier')


def create_employee(trans):
    return ExampleCreator.create(trans, 'IEmployee')


def create_salesperson(trans):
    return ExampleCreator.create(trans, 'ISalesPerson')


def create_client(trans):
    return ExampleCreator.create(trans, 'IClient')


def create_individual(trans):
    return ExampleCreator.create(trans, 'IIndividual')


def create_user(trans):
    return ExampleCreator.create(trans, 'IUser')


def create_storable(trans):
    return ExampleCreator.create(trans, 'ProductAdaptToStorable')


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
    return ExampleCreator.create(trans, 'ICompany')


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

    def set_transaction(self, trans):
        self.trans = trans

    def create_by_type(self, model_type):
        known_types = {
            'Account': self.create_account,
            'AccountTransaction': self.create_account_transaction,
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
            'IClient': self.create_client,
            'ICompany': self.create_company,
            'IBranch': self.create_branch,
            'IEmployee': self.create_employee,
            'IIndividual': self.create_individual,
            'Inventory': self.create_inventory,
            'InventoryItem': self.create_inventory_item,
            'ISalesPerson': self.create_sales_person,
            'ISupplier': self.create_supplier,
            'ITransporter': self.create_transporter,
            'IUser': self.create_user,
            'Payment': self.create_payment,
            'ParameterData': self.create_parameter_data,
            'Person': self.create_person,
            'PersonAdaptToBranch': self.create_branch,
            'PersonAdaptToCompany': self.create_company,
            'PersonAdaptToClient': self.create_client,
            'PersonAdaptToCreditProvider': self.create_credit_provider,
            'PersonAdaptToEmployee': self.create_employee,
            'PersonAdaptToIndividual': self.create_individual,
            'PersonAdaptToSalesPerson': self.create_sales_person,
            'PersonAdaptToSupplier': self.create_supplier,
            'PersonAdaptToTransporter': self.create_transporter,
            'PersonAdaptToUser': self.create_user,
            'Product': self.create_product,
            'ProductAdaptToStorable': self.create_storable,
            'PurchaseOrder': self.create_purchase_order,
            'PurchaseItem': self.create_purchase_order_item,
            'ReceivingOrder': self.create_receiving_order,
            'ReceivingOrderItem': self.create_receiving_order_item,
            'RenegotiationData': self.create_renegotiation_data,
            'Sale': self.create_sale,
            'SaleItem': self.create_sale_item,
            'SaleItemIcms': self.create_sale_item_icms,
            'SaleItemIpi': self.create_sale_item_ipi,
            'Sellable': self.create_sellable,
            'SellableCategory': self.create_sellable_category,
            'SellableUnit': self.create_sellable_unit,
            'Service': self.create_service,
            'StockDecrease': self.create_stock_decrease,
            'Till': self.create_till,
            'UserProfile': self.create_user_profile,
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
            'BankAccount': self.create_bank_account,
            'QuoteGroup': self.create_quote_group,
            'Quotation': self.create_quotation,
            }
        if isinstance(model_type, basestring):
            model_name = model_type
        else:
            model_name = model_type.__name__
        if model_name in known_types:
            return known_types[model_name]()

    def create_person(self):
        from stoqlib.domain.person import Person
        return Person(name='John', connection=self.trans)

    def create_branch(self, name='Dummy'):
        from stoqlib.domain.person import Person
        person = Person(name=name, connection=self.trans)
        fancy_name = name + ' shop'
        person.addFacet(ICompany, fancy_name=fancy_name,
                        connection=self.trans)
        return person.addFacet(IBranch, connection=self.trans)

    def create_supplier(self):
        from stoqlib.domain.person import Person
        person = Person(name='Supplier', connection=self.trans)
        person.addFacet(ICompany, fancy_name='Company Name',
                        cnpj='90.117.749/7654-80',
                        connection=self.trans)
        return person.addFacet(ISupplier, connection=self.trans)

    def create_employee_role(self):
        if not self._role:
            from stoqlib.domain.person import EmployeeRole
            self._role = EmployeeRole(name='Role', connection=self.trans)
        return self._role

    def create_employee(self, name="SalesPerson"):
        from stoqlib.domain.person import Person
        person = Person(name=name, connection=self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        return person.addFacet(IEmployee,
                               role=self.create_employee_role(),
                               connection=self.trans)

    def create_sales_person(self):
        employee = self.create_employee()
        return employee.person.addFacet(ISalesPerson, connection=self.trans)

    def create_client(self):
        from stoqlib.domain.person import Person
        person = Person(name='Client', connection=self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        return person.addFacet(IClient, connection=self.trans)

    def create_individual(self):
        from stoqlib.domain.person import Person
        person = Person(name='individual', connection=self.trans)
        return person.addFacet(IIndividual, connection=self.trans)

    def create_user(self):
        individual = self.create_individual()
        profile = self.create_user_profile()
        return individual.person.addFacet(IUser, username='username',
                                          password='password',
                                          profile=profile,
                                          connection=self.trans)

    def create_storable(self):
        from stoqlib.domain.product import Product
        sellable = self.create_sellable()
        product = Product(sellable=sellable, connection=self.trans)
        return product.addFacet(IStorable, connection=self.trans)

    def create_product(self, price=None, create_supplier=True,
                       branch=None, stock=None):
        from stoqlib.domain.product import ProductSupplierInfo
        sellable = self.create_sellable(price=price)
        if create_supplier:
            ProductSupplierInfo(connection=self.trans,
                                supplier=self.create_supplier(),
                                product=sellable.product,
                                is_main_supplier=True)
        product = sellable.product
        if not branch:
            branch = get_current_branch(self.trans)

        if stock:
            storable = product.addFacet(IStorable, connection=self.trans)
            storable.increase_stock(stock, branch, unit_cost=10)

        return product

    def create_product_component(self):
        from stoqlib.domain.product import ProductComponent
        product = self.create_product()
        component = self.create_product()
        return ProductComponent(product=product,
                                component=component,
                                connection=self.trans)

    def create_sellable(self, price=None):
        from stoqlib.domain.product import Product
        from stoqlib.domain.sellable import Sellable
        tax_constant = sysparam(self.trans).DEFAULT_PRODUCT_TAX_CONSTANT
        if price is None:
            price = 10
        sellable = Sellable(cost=125,
                            tax_constant=tax_constant,
                            price=price,
                            description="Description",
                            connection=self.trans)
        Product(sellable=sellable, connection=self.trans)
        return sellable

    def create_sellable_unit(self, description=u'', allow_fraction=True):
        from stoqlib.domain.sellable import SellableUnit
        return SellableUnit(connection=self.trans,
                            description=description,
                            allow_fraction=allow_fraction)

    def create_sellable_category(self):
        from stoqlib.domain.sellable import SellableCategory
        return SellableCategory(description="Category",
                                connection=self.trans)

    def create_sale(self, id_=None):
        from stoqlib.domain.sale import Sale
        from stoqlib.domain.till import Till
        till = Till.get_current(self.trans)
        if till is None:
            till = self.create_till()
            till.open_till()
        salesperson = self.create_sales_person()
        branch = self.create_branch()
        group = self.create_payment_group()
        extra_args = dict()
        if id_:
            extra_args['id'] = id_

        return Sale(coupon_id=0,
                    open_date=const.NOW(),
                    salesperson=salesperson, branch=branch,
                    cfop=sysparam(self.trans).DEFAULT_SALES_CFOP,
                    group=group,
                    connection=self.trans,
                    **extra_args)

    def create_sale_item(self):
        from stoqlib.domain.sale import SaleItem
        sellable = self.create_sellable()
        return SaleItem(connection=self.trans,
                        quantity=1,
                        price=100,
                        sale=self.create_sale(),
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

    def create_client_category_price(self):
        from stoqlib.domain.sellable import ClientCategoryPrice
        sellable = self.create_sellable(price=50)
        return ClientCategoryPrice(sellable=sellable,
                                   category=self.create_client_category(),
                                   price=100,
                                   connection=self.trans)

    def create_stock_decrease(self):
        from stoqlib.domain.stockdecrease import StockDecrease

        branch = self.create_branch()
        user = self.create_user()
        employee = self.create_employee()
        cfop = self.create_cfop_data()

        return StockDecrease(responsible=user,
                             removed_by=employee,
                             branch=branch,
                             status=StockDecrease.STATUS_INITIAL,
                             cfop=cfop,
                             connection=self.trans)

    def create_city_location(self):
        from stoqlib.domain.address import CityLocation
        return CityLocation(country='Groenlandia',
                            city='Acapulco',
                            state='Wisconsin',
                            connection=self.trans)

    def create_address(self):
        from stoqlib.domain.address import Address
        return Address(street='Mainstreet',
                       streetnumber=138,
                       district='Cidade Araci',
                       postal_code='12345-678',
                       complement='Compl',
                       is_main_address=True,
                       person=None,
                       city_location=self.create_city_location(),
                       connection=self.trans)

    def create_parameter_data(self):
        from stoqlib.domain.parameter import ParameterData
        return ParameterData.select(connection=self.trans)[0]

    def create_company(self):
        from stoqlib.domain.person import Person
        person = Person(name='Dummy', connection=self.trans)
        return person.addFacet(ICompany, fancy_name='Dummy shop',
                               connection=self.trans)

    def create_till(self):
        from stoqlib.domain.till import Till
        station = get_current_station(self.trans)
        return Till(connection=self.trans, station=station)

    def create_user_profile(self):
        from stoqlib.domain.profile import UserProfile
        return UserProfile(connection=self.trans, name='assistant')

    def create_purchase_order(self):
        from stoqlib.domain.purchase import PurchaseOrder
        group = self.create_payment_group()
        return PurchaseOrder(supplier=self.create_supplier(),
                              branch=self.create_branch(),
                              group=group,
                              responsible=get_current_user(self.trans),
                              connection=self.trans)

    def create_quote_group(self):
        from stoqlib.domain.purchase import QuoteGroup
        return QuoteGroup(connection=self.trans)

    def create_quotation(self):
        from stoqlib.domain.purchase import Quotation
        quote_group = self.create_quote_group()
        purchase_order = self.create_purchase_order()
        return Quotation(connection=self.trans,
                         group=quote_group,
                         purchase=purchase_order)

    def create_purchase_order_item(self):
        from stoqlib.domain.purchase import PurchaseItem
        return PurchaseItem(connection=self.trans,
                            quantity=8, quantity_received=0,
                            cost=125, base_cost=125,
                            sellable=self.create_sellable(),
                            order=self.create_purchase_order())

    def create_production_order(self):
        from stoqlib.domain.production import ProductionOrder
        return ProductionOrder(branch=self.create_branch(),
                               responsible=self.create_employee(),
                               description='production',
                               connection=self.trans)

    def create_production_item(self, quantity=1, order=None):
        from stoqlib.domain.product import ProductComponent
        from stoqlib.domain.production import (ProductionItem,
                                               ProductionMaterial)
        product = self.create_product(10)
        product.addFacet(IStorable, connection=self.trans)
        component = self.create_product(5)
        component.addFacet(IStorable, connection=self.trans)
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

    def create_receiving_order(self, purchase_order=None):
        from stoqlib.domain.receiving import ReceivingOrder
        if purchase_order is None:
            purchase_order = self.create_purchase_order()
        cfop = self.create_cfop_data()
        cfop.code = '1.102'
        return ReceivingOrder(connection=self.trans,
                              invoice_number=222,
                              supplier=purchase_order.supplier,
                              responsible=self.create_user(),
                              purchase=purchase_order,
                              branch=self.create_branch(),
                              cfop=cfop)

    def create_receiving_order_item(self, receiving_order=None, sellable=None,
                                    purchase_item=None, quantity=8):
        from stoqlib.domain.receiving import ReceivingOrderItem
        if receiving_order is None:
            receiving_order = self.create_receiving_order()
        if sellable is None:
            sellable = self.create_sellable()
            product = sellable.product
            product.addFacet(IStorable, connection=self.trans)
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

    def create_service(self):
        from stoqlib.domain.sellable import Sellable, SellableTaxConstant
        from stoqlib.domain.service import Service
        tax_constant = SellableTaxConstant.get_by_type(
            TaxType.SERVICE, self.trans)
        sellable = Sellable(tax_constant=tax_constant,
                            price=10,
                            description="Description",
                            connection=self.trans)
        service = Service(sellable=sellable, connection=self.trans)
        return service

    def create_renegotiation_data(self):
        from stoqlib.domain.renegotiation import RenegotiationData
        person = self.create_person()
        return RenegotiationData(connection=self.trans,
                                 paid_total=10,
                                 invoice_number=None,
                                 responsible=person)

    def create_transporter(self):
        person = self.create_person()
        person.addFacet(ICompany, connection=self.trans)
        return person.addFacet(ITransporter, connection=self.trans)

    def create_bank_account(self, account=None):
        from stoqlib.domain.account import BankAccount
        return BankAccount(connection=self.trans,
                           bank_branch='2666-1',
                           bank_account='20.666-1',
                           bank_number=1,
                           account=account or self.create_account())

    def create_credit_provider(self):
        person = self.create_person()
        person.addFacet(ICompany, connection=self.trans)
        return person.addFacet(ICreditProvider,
                               connection=self.trans,
                               short_name='Velec',
                               open_contract_date=datetime.date(2006, 01, 01))

    def create_payment(self, date=None):
        if not date:
            date = datetime.date.today()
        from stoqlib.domain.payment.payment import Payment
        return Payment(group=None,
                       open_date=date,
                       due_date=date,
                       value=Decimal(10),
                       till=None,
                       method=self.get_payment_method(),
                       category=None,
                       connection=self.trans)

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
                             branch=None,
                             connection=self.trans)

    def create_transfer_order(self):
        from stoqlib.domain.transfer import TransferOrder
        source_branch = self.create_branch("Source")
        dest_branch = self.create_branch("Dest")
        source_resp = self.create_employee("Ipswich")
        dest_resp = self.create_employee("Bolton")
        return TransferOrder(source_branch=source_branch,
                             destination_branch=dest_branch,
                             source_responsible=source_resp,
                             destination_responsible=dest_resp,
                             connection=self.trans)

    def create_transfer_order_item(self, order=None, quantity=5):
        from stoqlib.domain.product import Product
        from stoqlib.domain.sellable import Sellable
        from stoqlib.domain.transfer import TransferOrderItem
        if not order:
            order = self.create_transfer_order()
        sellable = self.create_sellable()
        sellable.status = Sellable.STATUS_AVAILABLE
        product = Product.selectOneBy(sellable=sellable, connection=self.trans)
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(quantity, order.source_branch)
        return TransferOrderItem(sellable=sellable,
                                 transfer_order=order,
                                 quantity=quantity,
                                 connection=self.trans)

    def create_inventory(self):
        from stoqlib.domain.inventory import Inventory
        branch = self.create_branch("Main")
        return Inventory(branch=branch, connection=self.trans)

    def create_inventory_item(self, inventory=None, quantity=5):
        from stoqlib.domain.inventory import InventoryItem
        if not inventory:
            inventory = self.create_inventory()
        sellable = self.create_sellable()
        product = sellable.product
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(quantity, inventory.branch)
        return InventoryItem(product=product,
                             product_cost=product.sellable.cost,
                             recorded_quantity=quantity,
                             inventory=inventory,
                             connection=self.trans)

    def create_loan(self):
        from stoqlib.domain.loan import Loan
        user = self.create_user()
        return Loan(responsible=user, connection=self.trans)

    def create_loan_item(self):
        from stoqlib.domain.loan import LoanItem
        loan = self.create_loan()
        sellable = self.create_sellable()
        return LoanItem(loan=loan, sellable=sellable, price=10,
                        quantity=1, connection=self.trans)

    def get_payment_method(self, name='money'):
        from stoqlib.domain.payment.method import PaymentMethod
        return PaymentMethod.get_by_name(self.trans, name)

    def get_station(self):
        return get_current_station(self.trans)

    def get_location(self):
        from stoqlib.domain.address import CityLocation
        return CityLocation.get_default(self.trans)

    def add_product(self, sale, price=None, quantity=1):
        product = self.create_product(price=price)
        sellable = product.sellable
        sellable.tax_constant = self.create_sellable_tax_constant()
        sale.add_sellable(sellable, quantity=quantity)
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))
        return sellable

    def add_payments(self, obj, method_type='money', date=None):
        from stoqlib.domain.sale import Sale
        from stoqlib.domain.purchase import PurchaseOrder
        method = self.get_payment_method(method_type)
        if isinstance(obj, Sale):
            total = obj.get_sale_subtotal()
            payment = method.create_inpayment(obj.group, total)
        elif isinstance(obj, PurchaseOrder):
            total = obj.get_purchase_subtotal()
            payment = method.create_outpayment(obj.group, total)
        else:
            raise ValueError(obj)

        if date:
            payment.payment.due_date = date
            payment.payment.open_date = date

        return payment

    def create_account(self):
        from stoqlib.domain.account import Account
        return Account(description="Test Account",
                       account_type=Account.TYPE_CASH,
                       connection=self.trans)

    def create_account_transaction(self, account):
        from stoqlib.domain.account import AccountTransaction
        return AccountTransaction(
            description="Test Account Transaction",
            code="Code",
            date=datetime.datetime.now(),
            value=1,
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

    def create_call(self):
        from stoqlib.domain.person import Calls
        return Calls(date=datetime.date(2011, 1, 1),
                     message="Test call message",
                     person=self.create_person(),
                     attendant=self.create_user(),
                     description="Test call",
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
