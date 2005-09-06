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
## Author(s): Henrique Romano           <henrique@async.com.br>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##
"""
stoq/tests/test_parameters.py:

   Unit test implementation for lib/parameters module.
"""

import gettext

from twisted.trial.unittest import TestCase
from twisted.python.components import implements

from stoq.lib.runtime import new_transaction
from stoq.lib.parameters import ParameterAccess, sysparam
from stoq.domain.interfaces import ICompany, ISupplier, IBranch
from stoq.domain.person import (Person, PersonAdaptToSupplier,
                                PersonAdaptToBranch, 
                                PersonAdaptToCompany,
                                EmployeePosition)
from stoq.domain.sellable import BaseSellableCategory
from stoq.domain.payment import PaymentMethod
from stoq.domain.service import Service


_ = gettext.gettext


class ParameterTest(TestCase):
    def setUp(self):
        conn = new_transaction()
        self.sparam = sysparam(conn)
        self.failUnless(isinstance(self.sparam, ParameterAccess))



    #
    # System instances
    #



    def testCurrentBranch(self):
        branch = self.sparam.CURRENT_BRANCH
        self.failUnless(branch != None)
        self.failUnless(isinstance(branch, PersonAdaptToBranch))
        person = branch.get_adapted()
        self.failUnless(isinstance(person, Person))
        company = ICompany(person)
        self.failUnless(company != None)
        branch = IBranch(person)
        self.failUnless(branch != None)

    def testCurrentWarehouse(self):
        warehouse = self.sparam.CURRENT_WAREHOUSE
        self.failUnless(warehouse != None)
        self.failUnless(isinstance(warehouse, PersonAdaptToCompany))
        person = warehouse.get_adapted()
        self.failUnless(isinstance(person, Person))
        company = ICompany(person)
        self.failUnless(company != None)
    
    def testSuggestedSupplier(self):
        supplier = self.sparam.SUGGESTED_SUPPLIER
        self.failUnless(supplier != None)
        self.failUnless(isinstance(supplier, PersonAdaptToSupplier))
        person = supplier.get_adapted()
        self.failUnless(isinstance(person, Person))
        company = ICompany(person)
        self.failUnless(company != None)
        supplier = ISupplier(person)
        self.failUnless(supplier != None)
        
    def testDefaultEmployeePosition(self):
        employee_position = self.sparam.DEFAULT_EMPLOYEE_POSITION
        self.failUnless(employee_position != None)
        self.failUnless(isinstance(employee_position, EmployeePosition))

    def testDefaultBaseCategory(self):
        base_category = self.sparam.DEFAULT_BASE_CATEGORY
        self.failUnless(base_category != None)
        self.failUnless(isinstance(base_category, BaseSellableCategory))

    def testMoneyPaymentMethod(self):
        method = self.sparam.MONEY_PAYMENT_METHOD
        self.failUnless(method != None)
        self.failUnless(isinstance(method, PaymentMethod))

    def testDeliveryService(self):
        service = self.sparam.DELIVERY_SERVICE
        self.failUnless(service != None)
        self.failUnless(isinstance(service, Service))

        

    #
    # System constants
    #



    def testUseLogicQuantity(self):
        param = self.sparam.USE_LOGIC_QUANTITY
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testMaxLateDays(self):
        param = self.sparam.MAX_LATE_DAYS
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testAcceptOrderProducts(self):
        param = self.sparam.ACCEPT_ORDER_PRODUCTS
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testCitySuggested(self):
        param = self.sparam.CITY_SUGGESTED
        self.failUnless(param != None)
        self.failUnless(isinstance(param, basestring))

    def testStateSuggested(self):
        param = self.sparam.STATE_SUGGESTED
        self.failUnless(param != None)
        self.failUnless(isinstance(param, basestring))

    def testCountrySuggested(self):
        param = self.sparam.COUNTRY_SUGGESTED
        self.failUnless(param != None)
        self.failUnless(isinstance(param, basestring))

    def testSellablePricePrecision(self):
        param = self.sparam.SELLABLE_PRICE_PRECISION
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testStockBalancePrecision(self):
        param = self.sparam.STOCK_BALANCE_PRECISION
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testHasStockMode(self):
        param = self.sparam.HAS_STOCK_MODE
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testEditSellablePrice(self):
        param = self.sparam.EDIT_SELLABLE_PRICE
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testHasDeliveryMode(self):
        param = self.sparam.HAS_DELIVERY_MODE
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

    def testMaxSearchResults(self):
        param = self.sparam.MAX_SEARCH_RESULTS
        self.failUnless(param != None)
        self.failUnless(isinstance(param, int))

