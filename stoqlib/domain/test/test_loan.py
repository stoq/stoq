# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010-2013 Async Open Source <http://www.async.com.br>
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
import decimal

from kiwi.currency import currency

from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.loan import Loan, LoanItem, _
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.taxes import (ProductTaxTemplate, ProductIcmsTemplate,
                                  ProductIpiTemplate, ProductCofinsTemplate,
                                  ProductPisTemplate)
from stoqlib.domain.test.domaintest import DomainTest

__tests__ = 'stoqlib/domain/loan.py'


class TestLoan(DomainTest):

    def test_get_status_name(self):
        loan = self.create_loan()
        for status in loan.statuses:
            self.assertEqual(loan.get_status_name(status), loan.statuses[status])
        with self.assertRaises(DatabaseInconsistency) as error:
            loan.get_status_name(9)
        expected = _("Invalid status %d") % 9
        self.assertEqual(str(error.exception), expected)

    def test_add_item(self):
        loan = self.create_loan()
        loan_item = self.create_loan_item()
        with self.assertRaises(AssertionError):
            loan.add_item(loan_item)
        loan_item.loan = None
        loan.add_item(loan_item)
        self.assertEqual(loan_item.loan, loan)

    def test_add_sellable(self):
        loan = self.create_loan()
        sellable = self.create_sellable()
        self.create_storable(product=sellable.product,
                             branch=loan.branch, stock=2)
        loan.add_sellable(sellable, quantity=1, price=10)
        items = list(loan.get_items())
        self.assertEqual(len(items), 1)
        self.assertFalse(items[0].sellable is not sellable)

    def test_get_total_amount(self):
        loan_item = self.create_loan_item()
        self.assertEqual(loan_item.loan.get_total_amount(), currency(10))

    def test_get_client_name(self):
        loan = self.create_loan()
        self.assertIs(loan.get_client_name(), u'')
        client = self.create_client(name=u'Client XX')
        loan.client = client
        self.assertEqual(loan.get_client_name(), u'Client XX')

    def test_get_branch_name(self):
        loan = self.create_loan()
        self.assertEqual(loan.get_branch_name(), u'Moda Stoq')
        branch = self.create_branch(name=u'New Branch')
        loan.branch = branch
        self.assertEqual(loan.get_branch_name(), u'New Branch shop')
        loan.branch = None
        self.assertEqual(loan.get_branch_name(), u'')

    def test_get_responsible_name(self):
        loan = self.create_loan()
        self.assertEqual(loan.get_responsible_name(), u'Administrator')
        loan.responsible.person.name = u''
        self.assertEqual(loan.get_responsible_name(), u'')

    def test_sync_stock(self):
        loan = self.create_loan()
        for i in range(5):
            item = self.create_loan_item(loan=loan)
            if i % 2 == 0:
                item.sellable.product.manage_stock = False
            elif i % 3 == 0:
                item._original_quantity = 10 * i
                item.quantity = i * 5
                item.return_quantity = 0
                item._original_return_quantity = 0
            else:
                item._original_quantity = 3
                item.quantity = 5
                item.return_quantity = 5
                item._original_return_quantity = 6
        results = self.store.find(LoanItem, loan=loan)
        stock_item = results[1].storable.get_stock_item(branch=loan.branch,
                                                        batch=None)

        before_quantity = stock_item.quantity
        loan.sync_stock(self.current_user)
        after_quantity = stock_item.quantity
        compare = [[before_quantity, after_quantity]]

        stock_item = results[3].storable.get_stock_item(branch=loan.branch,
                                                        batch=None)

        before_quantity = stock_item.quantity
        loan.sync_stock(self.current_user)
        after_quantity = stock_item.quantity
        compare.append([before_quantity, after_quantity])

        expected = [[decimal.Decimal(10), decimal.Decimal(7)],
                    [decimal.Decimal(25), decimal.Decimal(25)]]

        self.assertEqual(compare, expected)

    def test_can_close(self):
        loan_item = self.create_loan_item()
        loan = loan_item.loan
        self.assertEqual(loan.status, Loan.STATUS_OPEN)
        self.assertFalse(loan.can_close())

        loan_item.return_quantity = loan_item.quantity
        self.assertTrue(loan.can_close())

        loan.status = Loan.STATUS_CLOSED
        result = loan.can_close()
        self.assertFalse(result)

    def test_close(self):
        loan_item = self.create_loan_item()
        loan = loan_item.loan
        self.assertEqual(loan.status, Loan.STATUS_OPEN)
        self.assertFalse(loan.can_close())

        loan_item.return_quantity = loan_item.quantity
        self.assertTrue(loan.can_close())
        loan.close()
        self.assertEqual(loan.status, Loan.STATUS_CLOSED)

    def test_remove_item(self):
        loan_item = self.create_loan_item()
        loan = loan_item.loan

        total_items = self.store.find(LoanItem, loan=loan).count()
        self.assertEqual(total_items, 1)

        loan.remove_item(loan_item)

        total_items = self.store.find(LoanItem, loan=loan).count()
        self.assertEqual(total_items, 0)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            loan_item = self.create_loan_item()
            loan = loan_item.loan

            before_remove = self.store.find(LoanItem).count()
            loan.remove_item(loan_item)
            after_remove = self.store.find(LoanItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEqual(self.store.find(LoanItem, loan=loan).count(), 0)

    def test_get_available_discount_for_items(self):
        loan_item = self.create_loan_item()
        loan_item.loan.client = self.create_client()
        user = self.create_user()
        user.profile.max_discount = decimal.Decimal('5')
        discount = loan_item.loan.get_available_discount_for_items(user)
        self.assertEqual(discount, decimal.Decimal('0.50'))

        # Test exclude item
        loan = self.create_loan()
        loan_item2 = self.create_loan_item()
        loan_item2.loan = None
        loan.add_item(loan_item2)
        discount = loan.get_available_discount_for_items(user, loan_item2)
        self.assertEqual(discount, decimal.Decimal('0'))

        # Test surcharge
        loan_item2.set_discount(decimal.Decimal('-5'))
        self.assertEqual(loan_item2.price, currency('10.50'))
        discount = loan_item2.loan.get_available_discount_for_items(user)
        self.assertEqual(discount, decimal.Decimal('0'))

    def test_set_items_discount(self):
        loan = self.create_loan()
        loan_item1 = self.create_loan_item()
        loan_item2 = self.create_loan_item()

        loan_item1.loan = None
        loan_item2.loan = None

        loan.add_item(loan_item1)
        loan.add_item(loan_item2)
        self.assertEqual(loan.get_total_amount(), 20)
        # 5% of discount
        loan.set_items_discount(5)
        self.assertEqual(loan.get_total_amount(), 19)

        # 5% of discount
        loan.set_items_discount(decimal.Decimal('5.27'))
        self.assertEqual(loan.get_total_amount(), decimal.Decimal('18.95'))

    # NF-e operations

    def test_comments(self):
        loan = self.create_loan()
        loan.notes = u'Loan notes 1\n Loan notes 2'
        expected_notes = u'Loan notes 1\n Loan notes 2'
        comments = '\n'.join(c.comment for c in loan.comments)
        self.assertEqual(expected_notes, comments)

    def test_discount_value(self):
        loan = self.create_loan()
        loan_item1 = self.create_loan_item(loan=loan)

        self.assertEqual(loan.invoice_total, currency(10))

        # Loan item price < base_price
        loan_item1.price = 9
        self.assertEqual(loan.discount_value, currency(1))
        self.assertEqual(loan.invoice_total, currency(9))

        # Loan item price > base_price
        loan_item2 = self.create_loan_item()
        loan_item2.price = 20
        loan_item2.loan = loan
        self.assertEqual(loan.invoice_total, currency(29))
        self.assertEqual(loan.discount_value, currency(1))
        self.assertEqual(loan.invoice_subtotal, currency(20))

    def test_get_items(self):
        loan = self.create_loan()
        loan_item = self.create_loan_item(loan=loan)
        items = loan.get_items()
        self.assertEqual(items[0], loan_item)

    def test_recipient(self):
        client = self.create_client()
        loan = self.create_loan(client=client)
        self.assertEqual(loan.recipient, client.person)

    def test_operation_nature(self):
        # FIXME: Check using the operation_nature that will be saved in new field.
        loan = self.create_loan()
        self.assertEqual(loan.operation_nature, u'Loan')


class TestLoanItem(DomainTest):

    def test_storm_loaded(self):
        item = self.create_loan_item()
        item.return_quantity = 2

        self.assertEqual(item._original_quantity, 0)
        self.assertEqual(item._original_return_quantity, 0)

        item.__storm_loaded__()

        self.assertEqual(item._original_quantity, 1)
        self.assertEqual(item._original_return_quantity, 2)

    def test_sync_stock(self):
        loan = self.create_loan()
        product = self.create_product()
        storable = self.create_storable(product, self.current_branch, 4)
        loan.branch = self.current_branch
        initial = storable.get_balance_for_branch(self.current_branch)
        sellable = product.sellable

        # creates a loan with 4 items of the same product
        quantity = 4
        loan_item = loan.add_sellable(sellable, quantity=quantity, price=10)
        loan_item.sync_stock(self.current_user)
        self.assertEqual(loan_item.quantity, quantity)
        self.assertEqual(loan_item.return_quantity, 0)
        self.assertEqual(loan_item.sale_quantity, 0)
        # The quantity loaned items should be removed from stock
        self.assertEqual(
            storable.get_balance_for_branch(self.current_branch),
            initial - quantity)

        # Sell one of the loaned items and return one item (leaving 2 in the
        # loan)
        loan_item.return_quantity = 1
        loan_item.sale_quantity = 1
        loan_item.sync_stock(self.current_user)
        self.assertEqual(loan_item.quantity, quantity)
        self.assertEqual(loan_item.return_quantity, 1)
        self.assertEqual(loan_item.sale_quantity, 1)
        # The return_quantity should be returned to the stock
        self.assertEqual(
            storable.get_balance_for_branch(self.current_branch),
            initial - quantity + loan_item.return_quantity)

        # Return the 2 remaining products in this loan.
        loan_item.return_quantity += 2
        loan_item.sync_stock(self.current_user)
        self.assertEqual(loan_item.quantity, quantity)
        self.assertEqual(loan_item.return_quantity, 3)
        self.assertEqual(loan_item.sale_quantity, 1)
        # The return_quantity should be returned to the stock
        self.assertEqual(
            storable.get_balance_for_branch(self.current_branch),
            initial - quantity + loan_item.return_quantity)

    def test_sync_stock_with_storable(self):
        loan = self.create_loan(branch=self.create_branch())
        product = self.create_product()
        storable = self.create_storable(product, loan.branch, is_batch=True)
        batch = self.create_storable_batch(storable=storable)
        storable.increase_stock(10, loan.branch,
                                StockTransactionHistory.TYPE_INITIAL,
                                None, self.current_user, batch=batch)

        loan_item = loan.add_sellable(product.sellable, quantity=4, price=10,
                                      batch=batch)
        self.assertEqual(batch.get_balance_for_branch(loan.branch), 10)
        loan_item.sync_stock(self.current_user)
        self.assertEqual(batch.get_balance_for_branch(loan.branch), 6)
        self.assertEqual(loan_item.quantity, 4)
        self.assertEqual(loan_item.return_quantity, 0)
        self.assertEqual(loan_item.sale_quantity, 0)

        # The sale quantity should still be decreased
        loan_item.sale_quantity = 2
        loan_item.sync_stock(self.current_user)
        self.assertEqual(batch.get_balance_for_branch(loan.branch), 6)

        # The return quantity should go back to the stock
        loan_item.return_quantity = 2
        loan_item.sync_stock(self.current_user)
        self.assertEqual(batch.get_balance_for_branch(loan.branch), 8)

    def test_remaining_quantity(self):
        loan = self.create_loan()
        product = self.create_product()
        self.create_storable(product, self.current_branch, 4)
        loan.branch = self.current_branch

        # creates a loan with 4 items of the same product
        loan_item = loan.add_sellable(product.sellable, quantity=4, price=10)
        self.assertEqual(loan_item.get_remaining_quantity(), 4)
        loan_item.sale_quantity = 1
        self.assertEqual(loan_item.get_remaining_quantity(), 3)
        loan_item.return_quantity = 2
        self.assertEqual(loan_item.get_remaining_quantity(), 1)

    def test_get_quantity_unit_string(self):
        loan_item = self.create_loan_item()
        loan_item.sellable.unit = self.create_sellable_unit(description=u'Kg')
        self.assertEqual(loan_item.get_quantity_unit_string(), u'1.000 Kg')

    def test_get_total(self):
        item = self.create_loan_item()
        self.assertEqual(item.get_total(), currency(10))

    def test_set_discount(self):
        loan_item = self.create_loan_item()
        self.assertEqual(loan_item.get_total(), currency(10))

        # It requires a currency value but is 5% of discount
        loan_item.set_discount(decimal.Decimal('4.9'))
        self.assertEqual(loan_item.get_total(), currency('9.51'))

    # NF-e operations

    def test_nfe_data(self):
        loan = self.create_loan()
        product = self.create_product()
        icms_tax_template = ProductTaxTemplate(store=self.store,
                                               tax_type=ProductTaxTemplate.TYPE_ICMS)
        icms_template = ProductIcmsTemplate(store=self.store,
                                            product_tax_template=icms_tax_template)

        ipi_tax_template = ProductTaxTemplate(store=self.store,
                                              tax_type=ProductTaxTemplate.TYPE_IPI)
        ipi_template = ProductIpiTemplate(store=self.store,
                                          product_tax_template=ipi_tax_template)

        pis_tax_template = ProductTaxTemplate(store=self.store,
                                              tax_type=ProductTaxTemplate.TYPE_PIS)
        pis_template = ProductPisTemplate(store=self.store,
                                          product_tax_template=pis_tax_template)

        cofins_tax_template = ProductTaxTemplate(store=self.store,
                                                 tax_type=ProductTaxTemplate.TYPE_COFINS)
        cofins_template = ProductCofinsTemplate(store=self.store,
                                                product_tax_template=cofins_tax_template)
        product.set_icms_template(icms_template)
        product.set_ipi_template(ipi_template)
        product.set_pis_template(pis_template)
        product.set_cofins_template(cofins_template)

        loan_item = loan.add_sellable(product.sellable)
        self.assertIsNotNone(loan_item.icms_info)
        self.assertIsNotNone(loan_item.ipi_info)
        self.assertIsNotNone(loan_item.pis_info)
        self.assertIsNotNone(loan_item.cofins_info)

        self.assertEqual(loan_item.item_discount, 0)
        loan_item.price -= 2
        self.assertEqual(loan_item.item_discount, 2)

    def test_cfop_code(self):
        loan_item = self.create_loan_item()
        self.assertEqual(loan_item.cfop_code, u'5917')
