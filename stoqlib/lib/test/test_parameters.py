# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Henrique Romano           <henrique@async.com.br>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##            Grazieno Pellegrino       <grazieno1@yahoo.com.br>
##            Johan Dahlin              <jdahlin@async.com.br>
##
""" Test for lib/parameters module.  """

from decimal import Decimal

from stoqlib.lib.parameters import sysparam
from stoqlib.database.runtime import get_current_station
from stoqlib.domain.fiscal import AbstractFiscalBookEntry
from stoqlib.domain.interfaces import (ICompany, ISupplier, IBranch,
                                       ISalesPerson, IClient,
                                       IUser, IPaymentGroup, IEmployee,
                                       IIndividual)
from stoqlib.domain.address import CityLocation
from stoqlib.domain.person import Person, EmployeeRole
from stoqlib.domain.payment.methods import BillPM, MoneyPM
from stoqlib.domain.renegotiation import AbstractRenegotiationAdapter
from stoqlib.domain.sellable import BaseSellableCategory, ASellable
from stoqlib.domain.profile import UserProfile
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.domain.sale import Sale
from stoqlib.domain.service import ServiceAdaptToSellable
from stoqlib.domain.till import Till
from stoqlib.exceptions import PaymentError, StockError
from stoqlib.domain.test.domaintest import DomainTest

class TestParameter(DomainTest):

    def _create_examples(self):
        person = Person(name='Jonas', connection=self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        role = EmployeeRole(connection=self.trans, name='desenvolvedor')
        employee = person.addFacet(IEmployee, connection=self.trans,
                                   role=role)
        self.salesperson = person.addFacet(ISalesPerson,
                                           connection=self.trans)
        company = person.addFacet(ICompany, connection=self.trans)
        client = person.addFacet(IClient, connection=self.trans)
        self.branch = person.addFacet(IBranch, connection=self.trans)

        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        renegotiation = AbstractRenegotiationAdapter(connection=self.trans)
        self.sale = Sale(coupon_id=123, client=client,
                         cfop=self.sparam.DEFAULT_SALES_CFOP,
                         salesperson=self.salesperson,
                         renegotiation_data=renegotiation,
                         till=till, connection=self.trans)

        self.storable = self.create_storable()

        self.group = self.sale.addFacet(IPaymentGroup, connection=self.trans)


    def setUp(self):
        DomainTest.setUp(self)
        self.sparam = sysparam(self.trans)

    # System instances based on stoq.lib.parameters

    def testMainCompany(self):
        company = self.sparam.MAIN_COMPANY
        branchTable = Person.getAdapterClass(IBranch)
        assert isinstance(company, branchTable)
        assert isinstance(company.person, Person)

    def testDefaultEmployeeRole(self):
        employee_role = self.sparam.DEFAULT_SALESPERSON_ROLE
        assert isinstance(employee_role, EmployeeRole)

    def testSuggestedSupplier(self):
        supplier = self.sparam.SUGGESTED_SUPPLIER
        supplierTable = Person.getAdapterClass(ISupplier)
        assert isinstance(supplier, supplierTable)
        person = supplier.person
        assert isinstance(person, Person)
        supplier = ISupplier(person)
        assert isinstance(supplier, supplierTable)

    def testDefaultBaseCategory(self):
        base_category = self.sparam.DEFAULT_BASE_CATEGORY
        assert isinstance(base_category, BaseSellableCategory)

    def testPaymentDestination(self):
        self._create_examples()
        param = self.sparam.DEFAULT_PAYMENT_DESTINATION
        method = MoneyPM.selectOne(connection=self.trans)
        new_payment = self.group.add_payment(value=10, description='testing',
                                             method=method)
        self.failUnless(new_payment.destination is param)

    def testDeliveryService(self):
        service = self.sparam.DELIVERY_SERVICE
        assert isinstance(service, ServiceAdaptToSellable)

    def testDefaultGiftCertificateType(self):
        self._create_examples()
        param = self.sparam.DEFAULT_GIFT_CERTIFICATE_TYPE
        sellable_cert = self.sale.add_custom_gift_certificate(
                            certificate_value=Decimal(200),
                            certificate_number=u'500')
        assert isinstance(sellable_cert, ASellable)
        self.assertEqual(sellable_cert.base_sellable_info.description,
                         param.base_sellable_info.description)

    # System constants based on stoq.lib.parameters

    def testUseLogicQuantity(self):
        storable = self.create_storable()
        param = self.sparam.USE_LOGIC_QUANTITY
        self.assertEqual(storable._check_logic_quantity(), None)
        self.sparam.update_parameter(parameter_name='USE_LOGIC_QUANTITY',
                                     value=u'0')
        self.failUnlessRaises(StockError,
                              storable._check_logic_quantity)

    def testMaxLateDays(self):
        param = self.sparam.MAX_LATE_DAYS
        assert isinstance(param, int)

    def testPOSFullScreen(self):
        param = self.sparam.POS_FULL_SCREEN
        assert isinstance(param, bool)

    def testPOSSeparateCashier(self):
        param = self.sparam.POS_SEPARATE_CASHIER
        assert isinstance(param, bool)

    def testAcceptOrderProducts(self):
        param = self.sparam.ACCEPT_ORDER_PRODUCTS
        assert isinstance(param, int)

    def testLocationSuggested(self):
        location = CityLocation.get_default(self.trans)
        self.assertEqual(location.city, self.sparam.CITY_SUGGESTED)
        self.assertEqual(location.state, self.sparam.STATE_SUGGESTED)
        self.assertEqual(location.country, self.sparam.COUNTRY_SUGGESTED)

    def testHasDeliveryMode(self):
        param = self.sparam.HAS_DELIVERY_MODE
        assert isinstance(param, int)

    def testHasStockMode(self):
        param = self.sparam.HAS_STOCK_MODE
        assert isinstance(param, int)

    def testMaxSearchResults(self):
        param = self.sparam.MAX_SEARCH_RESULTS
        assert isinstance(param, int)

    def testMandatoryInterestCharge(self):
        return True
        self.sparam.update_parameter(
            parameter_name='MANDATORY_INTEREST_CHARGE',
            value=u'1')

        bill = BillPM.selectOne(connection=self.trans)
        self.failUnlessRaises(PaymentError,
                              bill._calculate_payment_value,
                              total_value=Decimal(512),
                              interest=Decimal(30),
                              installments_number=1)

    def testConfirmSalesOnTill(self):
        param = self.sparam.CONFIRM_SALES_ON_TILL
        assert isinstance(param, int)

    def testAcceptChangeSalesperson(self):
        param = self.sparam.ACCEPT_CHANGE_SALESPERSON
        assert isinstance(param, bool)

      # Cannot perform this test, see bug 2655 to further details.
#     def testPurchasePreviewPayment(self):
#         supplier = Person.getAdapterClass(ISupplier).select(
#                        connection=self.trans)[0]
#         branch = Person.getAdapterClass(IBranch).select(
#                      connection=self.trans)[0]
#         purchase = PurchaseOrder(connection=self.trans, supplier=supplier,
#                                  branch=branch,
#                                  status=PurchaseOrder.ORDER_PENDING)
#         purchase.addFacet(IPaymentGroup, connection=self.trans)
#         purchase.confirm()
#         param = self.sparam.USE_PURCHASE_PREVIEW_PAYMENTS
#         assert isinstance (param, int)

    # Some enhancement is necessary here, this test needs to be improved
    def testReturnMoneyOnSales(self):
        param = self.sparam.RETURN_MONEY_ON_SALES
        assert isinstance(param, bool)

    def testReceiveProductsWithoutOrder(self):
        param = self.sparam.RECEIVE_PRODUCTS_WITHOUT_ORDER
        assert isinstance(param, bool)

    def testMaxSaleOrderValidity(self):
        param = self.sparam.MAX_SALE_ORDER_VALIDITY
        assert isinstance(param, int)

    def testUseScalePrice(self):
        param = self.sparam.USE_SCALE_PRICE
        assert isinstance(param, int)

    def testAskSaleCFOP(self):
        param = self.sparam.ASK_SALES_CFOP
        assert isinstance(param, bool)

    def testDefaultSalesCFOP(self):
        self._create_examples()
        param = self.sparam.DEFAULT_SALES_CFOP
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        sale = Sale(coupon_id=123, salesperson=self.salesperson,
                    till=till, connection=self.trans)
        self.assertEqual(sale.cfop, param)
        param = self.sparam.DEFAULT_RECEIVING_CFOP
        sale = Sale(coupon_id=432, salesperson=self.salesperson,
                    till=till, connection=self.trans, cfop=param)
        self.failIfEqual(sale.cfop, self.sparam.DEFAULT_SALES_CFOP)

    def testDefaultReturnSalesCFOP(self):
        self._create_examples()
        wrong_param = self.sparam.DEFAULT_SALES_CFOP
        drawee = Person(name='Antonione', connection=self.trans)
        book_entry = AbstractFiscalBookEntry(invoice_number=123,
                                             cfop=wrong_param,
                                             branch=self.branch,
                                             drawee=drawee,
                                             payment_group=self.group,
                                             connection=self.trans)
        reversal = book_entry.get_reversal_clone(invoice_number=124)
        self.failIfEqual(wrong_param, reversal.cfop)
        self.assertEqual(self.sparam.DEFAULT_RETURN_SALES_CFOP,
                         reversal.cfop)

    def testDefaultReceivingCFOP(self):
        branch = self.create_branch()
        param = self.sparam.DEFAULT_RECEIVING_CFOP
        person = Person(name='Craudinho', connection=self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        profile = UserProfile(name='profile', connection=self.trans)
        responsible = person.addFacet(IUser, connection=self.trans,
                                      password='asdfgh', profile=profile,
                                      username='craudio')
        receiving_order = ReceivingOrder(responsible=responsible,
                                         branch=branch,
                                         connection=self.trans,
                                         invoice_number=876,
                                         supplier=None)
        param2 = self.sparam.DEFAULT_SALES_CFOP
        receiving_order2 = ReceivingOrder(responsible=responsible,
                                          cfop=param2, branch=branch,
                                          connection=self.trans,
                                          invoice_number=1231,
                                          supplier=None)
        self.assertEqual(param, receiving_order.cfop)
        self.failIfEqual(param, receiving_order2.cfop)

    def testICMSTax(self):
        param = self.sparam.ICMS_TAX
        assert isinstance(param, int)

    def testISSTax(self):
        param = self.sparam.ISS_TAX
        assert isinstance(param, int)

    def testSubstitutionTax(self):
        param = self.sparam.SUBSTITUTION_TAX
        assert isinstance(param, int)

    def testDefaultAreaCode(self):
        param = self.sparam.DEFAULT_AREA_CODE
        self.failUnless(isinstance(param, int), type(param))
