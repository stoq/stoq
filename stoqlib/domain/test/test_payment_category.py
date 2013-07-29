# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/payment/category.py'

from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.test.domaintest import DomainTest


class TestPaymentCategory(DomainTest):
    def test_get_by_type(self):
        pcs = PaymentCategory.get_by_type(self.store, PaymentCategory.TYPE_RECEIVABLE)
        self.assertTrue(pcs.is_empty())
        pcs = PaymentCategory.get_by_type(self.store, PaymentCategory.TYPE_PAYABLE)
        self.assertTrue(pcs.is_empty())

        category = self.create_payment_category()
        category.name = u'receiviable'
        category.category_type = PaymentCategory.TYPE_RECEIVABLE

        pcs = PaymentCategory.get_by_type(self.store, PaymentCategory.TYPE_RECEIVABLE)
        self.assertFalse(pcs.is_empty())
        pcs = PaymentCategory.get_by_type(self.store, PaymentCategory.TYPE_PAYABLE)
        self.assertTrue(pcs.is_empty())

        category = self.create_payment_category()
        category.name = u'payable'
        category.category_type = PaymentCategory.TYPE_PAYABLE

        pcs = PaymentCategory.get_by_type(self.store, PaymentCategory.TYPE_RECEIVABLE)
        self.assertFalse(pcs.is_empty())
        pcs = PaymentCategory.get_by_type(self.store, PaymentCategory.TYPE_PAYABLE)
        self.assertFalse(pcs.is_empty())

    def test_get_description(self):
        category = self.create_payment_category()
        self.assertEquals(category.get_description(), u'category')
