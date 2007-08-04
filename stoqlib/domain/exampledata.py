# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin  <jdahlin@async.com.br>
##              Fabio Morbec  <fabio@async.com.br>
##

import datetime
from decimal import Decimal

from stoqdrivers.enum import TaxType
from sqlobject.sqlbuilder import const

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.interfaces import (IBranch, ICompany, IEmployee,
                                       IIndividual, ISupplier,
                                       ISellable, IStorable, ISalesPerson,
                                       IClient, IUser, ITransporter,
                                       IBankBranch,
                                       ICreditProvider,
                                       IPaymentGroup, IProduct)
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
    return ExampleCreator.create(trans, 'ProductAdaptToSellable')

def create_sale(trans):
    return ExampleCreator.create(trans, 'Sale')

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

class ExampleCreator(object):
    def __init__(self, trans):
        self.trans = trans

    # Public API

    @classmethod
    def create(cls, trans, name):
        return cls(trans).create_by_type(name)

    def create_by_type(self, model_type):
        known_types = {
            'APaymentMethod': self.create_payment_method,
            'ASellable': self.create_sellable,
            'AbstractPaymentGroup' : self.create_payment_group,
            'BaseSellableInfo': self.create_base_sellable_info,
            'BranchStation': self.get_station,
            'Bank': self.create_bank,
            'CityLocation': self.get_location,
            'CfopData': self.create_cfop_data,
            'EmployeeRole': self.create_employee_role,
            'FiscalBookEntry' : self.create_fiscal_book_entry,
            'IClient': self.create_client,
            'IBranch': self.create_branch,
            'IEmployee': self.create_employee,
            'IIndividual': self.create_individual,
            'ISalesPerson': self.create_sales_person,
            'ISupplier': self.create_supplier,
            'ITransporter': self.create_transporter,
            'IUser': self.create_user,
            'OnSaleInfo': self.create_on_sale_info,
            'Payment': self.create_payment,
            'PaymentDestination' : self.create_payment_destination,
            'ParameterData': self.create_parameter_data,
            'Person': self.create_person,
            'PersonAdaptToBankBranch': self.create_bank_branch,
            'PersonAdaptToBranch': self.create_branch,
            '_PersonAdaptToCompany': self.create_company,
            'PersonAdaptToClient': self.create_client,
            'PersonAdaptToCreditProvider': self.create_credit_provider,
            'PersonAdaptToEmployee': self.create_employee,
            'PersonAdaptToIndividual': self.create_individual,
            'PersonAdaptToSalesPerson': self.create_sales_person,
            'PersonAdaptToSupplier': self.create_supplier,
            'PersonAdaptToTransporter': self.create_transporter,
            'PersonAdaptToUser': self.create_user,
            'Product': self.create_product,
            'ProductAdaptToSellable' : self.create_sellable,
            'ProductAdaptToStorable' : self.create_storable,
            'PurchaseOrder' : self.create_purchase_order,
            'PurchaseItem' : self.create_purchase_order_item,
            'ReceivingOrder' : self.create_receiving_order,
            'ReceivingOrderItem' : self.create_receiving_order_item,
            'RenegotiationData' : self.create_renegotiation_data,
            'Sale': self.create_sale,
            'Service': self.create_service,
            'Till': self.create_till,
            'UserProfile': self.create_user_profile,
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

    def create_branch(self):
        from stoqlib.domain.person import Person
        person = Person(name='Dummy', connection=self.trans)
        person.addFacet(ICompany, fancy_name='Dummy shop',
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
        from stoqlib.domain.person import EmployeeRole
        return EmployeeRole(name='Role', connection=self.trans)

    def create_employee(self):
        from stoqlib.domain.person import Person
        person = Person(name='SalesPerson', connection=self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        return person.addFacet(IEmployee,
                               role=self.create_employee,
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
        product = Product(connection=self.trans)
        return product.addFacet(IStorable, connection=self.trans)

    def create_product(self, price=None):
        from stoqlib.domain.product import ProductSupplierInfo
        sellable = self.create_sellable(price=price)
        product = IProduct(sellable)
        ProductSupplierInfo(connection=self.trans,
                            supplier=self.create_supplier(),
                            product=product,
                            is_main_supplier=True)
        return product

    def create_base_sellable_info(self, price=None):
        from stoqlib.domain.sellable import BaseSellableInfo
        if price is None:
            price = 10
        return BaseSellableInfo(connection=self.trans,
                                description="Description",
                                price=price)

    def create_sellable(self, price=None):
        from stoqlib.domain.product import Product
        product = Product(connection=self.trans)
        tax_constant = sysparam(self.trans).DEFAULT_PRODUCT_TAX_CONSTANT
        base_sellable_info = self.create_base_sellable_info(price=price)
        on_sale_info = self.create_on_sale_info()
        return product.addFacet(ISellable,
                                cost=125,
                                tax_constant=tax_constant,
                                base_sellable_info=base_sellable_info,
                                on_sale_info=on_sale_info,
                                connection=self.trans)

    def create_sale(self):
        from stoqlib.domain.sale import Sale
        from stoqlib.domain.till import Till
        till = Till.get_current(self.trans)
        if till is None:
            till = self.create_till()
            till.open_till()
        salesperson = self.create_sales_person()
        branch = self.create_branch()
        return Sale(coupon_id=0,
                    open_date=const.NOW(),
                    salesperson=salesperson, branch=branch,
                    cfop=sysparam(self.trans).DEFAULT_SALES_CFOP,
                    connection=self.trans)

    def create_city_location(self):
        from stoqlib.domain.address import CityLocation
        return CityLocation(country='Groenlandia',
                            city='Acapulco',
                            state='Wisconsin',
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
        order = PurchaseOrder(supplier=self.create_supplier(),
                              branch=self.create_branch(),
                            connection=self.trans)
        order.addFacet(IPaymentGroup, connection=self.trans)
        return order

    def create_purchase_order_item(self):
        from stoqlib.domain.purchase import PurchaseItem
        return PurchaseItem(connection=self.trans,
                            quantity=8, quantity_received=0,
                            cost=125, base_cost=125,
                            sellable=self.create_sellable(),
                            order=self.create_purchase_order())

    def create_cfop_data(self):
        from stoqlib.domain.fiscal import CfopData
        return CfopData(connection=self.trans, code=u'123',
                        description=u'test')

    def create_receiving_order(self):
        from stoqlib.domain.receiving import ReceivingOrder
        purchase = self.create_purchase_order()
        cfop = self.create_cfop_data()
        cfop.code = '1.102'
        return ReceivingOrder(connection=self.trans,
                              invoice_number=222,
                              supplier=purchase.supplier,
                              responsible=self.create_user(),
                              purchase=purchase,
                              branch=self.create_branch(),
                              cfop=cfop)

    def create_receiving_order_item(self, receiving_order=None, sellable=None):
        from stoqlib.domain.receiving import ReceivingOrderItem
        if receiving_order is None:
            receiving_order = self.create_receiving_order()
        if sellable is None:
            sellable = self.create_sellable()
            product = IProduct(sellable)
            product.addFacet(IStorable, connection=self.trans)
        purchase_item = receiving_order.purchase.add_item(sellable, 8)
        return ReceivingOrderItem(connection=self.trans,
                                  quantity=8, cost=125,
                                  purchase_item=purchase_item,
                                  sellable=sellable,
                                  receiving_order=receiving_order)

    def create_fiscal_book_entry(self, entry_type, icms_value=0, iss_value=0,
                                 ipi_value=0, invoice_number=None):
        from stoqlib.domain.payment.group import AbstractPaymentGroup
        from stoqlib.domain.fiscal import FiscalBookEntry
        payment_group = AbstractPaymentGroup(connection=self.trans)
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
        from stoqlib.domain.sellable import SellableTaxConstant
        from stoqlib.domain.service import Service
        service = Service(connection=self.trans)
        sellable_info = self.create_base_sellable_info()
        tax_constant = SellableTaxConstant.get_by_type(
            TaxType.SERVICE, self.trans)
        service.addFacet(ISellable,
                         tax_constant=tax_constant,
                         base_sellable_info=sellable_info,
                         connection=self.trans)
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

    def create_bank(self):
        from stoqlib.domain.account import Bank
        return Bank(connection=self.trans, name='Boston', short_name='short',
                    compensation_code='1234')

    def create_bank_branch(self):
        person = self.create_person()
        person.addFacet(ICompany, connection=self.trans)
        return person.addFacet(IBankBranch, connection=self.trans,
                               bank=self.create_bank())

    def create_credit_provider(self):
        person = self.create_person()
        person.addFacet(ICompany, connection=self.trans)
        return  person.addFacet(ICreditProvider,
                                connection=self.trans,
                                short_name='Velec',
                                open_contract_date=datetime.date(2006, 01, 01))

    def create_payment_method(self):
        from stoqdrivers.enum import PaymentMethodType
        from stoqlib.domain.payment.methods import APaymentMethod
        return APaymentMethod.get_by_enum(self.trans, PaymentMethodType.MONEY)

    def create_payment(self):
        from stoqlib.domain.payment.payment import Payment
        return Payment(group=None,
                       due_date=None,
                       destination=None,
                       value=Decimal(10),
                       till=None,
                       method=self.create_payment_method(),
                       connection=self.trans)

    def create_payment_group(self):
        from stoqlib.domain.payment.group import AbstractPaymentGroup
        return AbstractPaymentGroup(connection=self.trans)

    def create_payment_destination(self):
        from stoqlib.domain.payment.destination import PaymentDestination
        return PaymentDestination(description='foobar',
                                  connection=self.trans)

    def create_on_sale_info(self):
        from stoqlib.domain.sellable import OnSaleInfo
        return OnSaleInfo(connection=self.trans)

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

    def get_station(self):
        return get_current_station(self.trans)

    def get_location(self):
        from stoqlib.domain.address import CityLocation
        return CityLocation.get_default(self.trans)



