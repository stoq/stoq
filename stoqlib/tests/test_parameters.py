# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Henrique Romano           <henrique@async.com.br>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##            Grazieno Pellegrino       <grazieno1@yahoo.com.br>
##
""" Test for lib/parameters module.  """

from stoqlib.lib.runtime import new_transaction
from stoqlib.lib.parameters import ParameterAccess, sysparam
from stoqlib.domain.interfaces import ICompany, ISupplier, IBranch, IMoneyPM
from stoqlib.domain.person import Person, EmployeeRole
from stoqlib.domain.sellable import BaseSellableCategory
from stoqlib.domain.payment.methods import PaymentMethod
from stoqlib.domain.payment.destination import PaymentDestination
from stoqlib.domain.service import ServiceAdaptToSellable

class TestParameter:

    def setup_class(self):
        self.conn = new_transaction()
        self.sparam = sysparam(self.conn)
        assert isinstance(self.sparam, ParameterAccess)

    # System instances based on stoq.lib.parameters

    def test_CurrentBranch(self):
        branch = self.sparam.CURRENT_BRANCH
        branchTable = Person.getAdapterClass(IBranch)
        assert isinstance(branch, branchTable)
        person = branch.get_adapted()
        assert isinstance(person, Person)

    def test_CurrentWarehouse(self):
        warehouse = self.sparam.CURRENT_WAREHOUSE
        companyTable = Person.getAdapterClass(ICompany)
        assert isinstance(warehouse, companyTable)
        person = warehouse.get_adapted()
        assert isinstance(person, Person)
        company = ICompany(person, connection=self.conn)
        assert isinstance(company, companyTable)

    def test_DefaultEmployeeRole(self):
        employee_role = self.sparam.DEFAULT_SALESPERSON_ROLE
        assert isinstance(employee_role, EmployeeRole)

    def test_SuggestedSupplier(self):
        supplier = self.sparam.SUGGESTED_SUPPLIER
        supplierTable = Person.getAdapterClass(ISupplier)
        assert isinstance(supplier, supplierTable)
        person = supplier.get_adapted()
        assert isinstance(person, Person)
        supplier = ISupplier(person, connection=self.conn)
        assert isinstance(supplier, supplierTable)

    def test_DefaultBaseCategory(self):
        base_category = self.sparam.DEFAULT_BASE_CATEGORY
        assert isinstance(base_category, BaseSellableCategory)

    def test_PaymentDestination (self):
        payment = self.sparam.DEFAULT_PAYMENT_DESTINATION
        assert isinstance(payment, PaymentDestination)

    def test_PaymentMethod (self):
        payment_method = self.sparam.BASE_PAYMENT_METHOD
        assert isinstance(payment_method, PaymentMethod)

    def test_MethodMoney(self):
        method = self.sparam.METHOD_MONEY
        moneyTable = PaymentMethod.getAdapterClass (IMoneyPM)
        assert isinstance(method, moneyTable)

    def test_DeliveryService(self):
        service = self.sparam.DELIVERY_SERVICE
        assert isinstance(service, ServiceAdaptToSellable)

    # System constants based on stoq.lib.parameters

    def test_UseLogicQuantity(self):
        param = self.sparam.USE_LOGIC_QUANTITY
        assert isinstance(param, int)

    def test_MaxLateDays(self):
        param = self.sparam.MAX_LATE_DAYS
        assert isinstance(param, int)

    def test_AcceptOrderProducts(self):
        param = self.sparam.ACCEPT_ORDER_PRODUCTS
        assert isinstance(param, int)

    def test_CitySuggested(self):
        param = self.sparam.CITY_SUGGESTED
        assert isinstance(param, basestring)

    def test_StateSuggested(self):
        param = self.sparam.STATE_SUGGESTED
        assert isinstance(param, basestring)

    def test_CountrySuggested(self):
        param = self.sparam.COUNTRY_SUGGESTED
        assert isinstance(param, basestring)

    def test_DecimalSize(self):
        param = self.sparam.DECIMAL_SIZE
        assert isinstance(param, int)

    def test_DecimalPrecision(self):
        param = self.sparam.DECIMAL_PRECISION
        assert isinstance(param, int)

    def test_HasDeliveryMode(self):
        param = self.sparam.HAS_DELIVERY_MODE
        assert isinstance(param, int)

    def test_HasStockMode(self):
        param = self.sparam.HAS_STOCK_MODE
        assert isinstance(param, int)

    def test_EditSellablePrice(self):
        param = self.sparam.EDIT_SELLABLE_PRICE
        assert isinstance(param, int)

    def test_MaxSearchResults(self):
        param = self.sparam.MAX_SEARCH_RESULTS
        assert isinstance(param, int)

    def test_MandatoryInterestChange(self):
        param = self.sparam.MANDATORY_INTEREST_CHARGE
        assert isinstance(param, int)

    def test_ConfirmSalesOnTill(self):
        param = self.sparam.CONFIRM_SALES_ON_TILL
        assert isinstance(param, int)

    def test_SetPaymentMethodsOnTill(self):
        param = self.sparam.SET_PAYMENT_METHODS_ON_TILL
        assert isinstance (param, int)

    def test_PurchasePreviewPayment(self):
        param = self.sparam.USE_PURCHASE_PREVIEW_PAYMENTS
        assert isinstance (param, int)
