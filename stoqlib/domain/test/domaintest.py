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
## Author(s):   Johan Dahlin   <jdahlin@gmail.com>
##
""" Base module to be used by all domain test modules"""

from stoqlib.database.runtime import new_transaction
from stoqlib.domain.exampledata import ExampleCreator

try:
    from twisted.trial import unittest
    unittest # pyflakes
except:
    import unittest

class DomainTest(unittest.TestCase):
    def setUp(self):
        self.trans = new_transaction()

    def tearDown(self):
        self.trans.rollback()

    def create_person(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('Person')

    def create_branch(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('IBranch')

    def create_supplier(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ISupplier')

    def create_employee(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('IEmployee')

    def create_salesperson(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ISalesPerson')

    def create_client(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('IClient')

    def create_individual(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('IIndividual')

    def create_user(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('IUser')

    def create_storable(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ProductAdaptToStorable')

    def create_product(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('Product')

    def create_sellable(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ProductAdaptToSellable')

    def create_sale(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('Sale')

    def create_city_location(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('CityLocation')

    def create_parameter_data(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ParameterData')

    def create_service_sellable_item(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ServiceSellableItem')

    def create_device_settings(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('DeviceSettings')

    def create_company(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ICompany')

    def create_till(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('Till')

    def create_user_profile(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('UserProfile')

    def create_device_settings(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('DeviceSettings')

    def create_device_constant(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('DeviceConstant')

    def create_receiving_order(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ReceivingOrder')

    def create_receiving_order_item(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ReceivingOrderItem')

    def create_icms_ipi_book_entry(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('IcmsIpiBookEntry')

    def create_iss_book_entry(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('IssBookEntry')

    def create_abstract_fiscal_book_entry(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('AbstractFiscalBookEntry')

    def create_coupon_printer(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('CouponPrinter')

    def create_service(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('Service')

    def create_transporter(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('ITransporter')

    def create_employee_role(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('EmployeeRole')

    def create_sales_person(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('PersonAdaptToSalesPerson')

    def create_purchase_order(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('PurchaseOrder')

    def get_station(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('BranchStation')

    def get_location(self):
        ex = ExampleCreator(self.trans)
        return ex.create_by_type('CityLocation')

    def create_by_type(self, model_type):
        return ExampleCreator(self.trans).create_by_type(model_type)

# Ensure that the database settings and etc are available for all
# the domain tests
import tests.base
tests.base # pyflakes


