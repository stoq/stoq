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
## Author(s):     Henrique Romano <henrique@async.com.br>
##

from datetime import datetime

from kiwi.datatypes import currency

from stoqlib.domain.sale import Sale
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import (ICompany, ISupplier, ISellable,
                                       IPaymentGroup, IFinancePM)
from stoqlib.domain.product import Product, ProductSupplierInfo
from stoqlib.domain.sellable import (BaseSellableCategory, SellableCategory,
                                     BaseSellableInfo)
from stoqlib.domain.till import get_current_till_operation, Till
from stoqlib.domain.payment.methods import (PaymentMethodDetails,
                                            CreditProviderGroupData,
                                            FinanceDetails)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.runtime import get_current_station
from tests.base import BaseDomainTest

class TestPaymentMethodDetails(BaseDomainTest):
    _table = PaymentMethodDetails

    def test_max_installment_number(self):
        # Supplier
        person = Person(name="Henrique", connection=self.conn)
        person.addFacet(ICompany, connection=self.conn)
        supplier = person.addFacet(ISupplier, connection=self.conn)
        # Product
        product = Product(connection=self.conn)
        # ProductSupplierInfo
        supplier_info = ProductSupplierInfo(supplier=supplier,
                                            base_cost=currency(100),
                                            is_main_supplier=True,
                                            product=product,
                                            connection=self.conn)
        # Sellable
        base_category = BaseSellableCategory(description="Monitor",
                                             connection=self.conn)
        category = SellableCategory(description="LG",
                                    base_category=base_category,
                                    connection=self.conn)
        sellable_info = BaseSellableInfo(description="Studioworks 775N",
                                         price=currency(150),
                                         connection=self.conn)
        sellable = product.addFacet(ISellable, category=category,
                                    base_sellable_info=sellable_info,
                                    connection=self.conn)
        # Till
        till = get_current_till_operation(self.conn)
        if till is None:
            till = Till(connection=self.conn,
                        station=get_current_station(self.conn))
        # Sale
        sale = Sale(till=till, open_date=datetime.now(), coupon_id=5,
                    salesperson=None,
                    cfop=sysparam(self.conn).DEFAULT_SALES_CFOP,
                    connection=self.conn)
        item = sellable.add_sellable_item(sale, price=currency(150))
        group = sale.addFacet(IPaymentGroup, connection=self.conn)
        result = FinanceDetails.select(FinanceDetails.q.is_active == True,
                                       connection=self.conn)
        payment_type = result[0]
        base_method = sysparam(self.conn).BASE_PAYMENT_METHOD
        method = IFinancePM(base_method, connection=self.conn)
        provider = method.get_finance_companies()[0]
        provider_data = CreditProviderGroupData(group=group,
                                                payment_type=payment_type,
                                                provider=provider,
                                                connection=self.conn)
        max_installments_number = payment_type.get_max_installments_number()
        self.failUnlessRaises(ValueError,  payment_type.setup_inpayments,
                              group, max_installments_number + 1,
                              datetime.now(), currency(150))
        installments_number = payment_type.get_max_installments_number()
        payment_type.setup_inpayments(group, max_installments_number,
                                      datetime.now(), currency(150))
