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
## Author(s):     Lincoln Molica <lincoln@async.com.br>
##                Henrique Romano <henrique@async.com.br>
##

from kiwi.datatypes import currency

from stoqlib.domain.giftcertificate import GiftCertificateType, GiftCertificate
from stoqlib.domain.interfaces import ISellable, IPaymentGroup
from stoqlib.domain.sellable import BaseSellableInfo, OnSaleInfo, ASellable
from stoqlib.exceptions import InvalidStatus

from tests.base import DomainTest

class TestGiftCertificateType(DomainTest):

    def setUp(self):
        DomainTest.setUp(self)
        self._info = BaseSellableInfo(price=currency(10), description="Testing",
                                      commission=currency(5),
                                      max_discount=currency(3),
                                      connection=self.trans)
        self._cert = GiftCertificateType(base_sellable_info=self._info,
                                         connection=self.trans)

    def test_create(self):
        self.failUnless(isinstance(self._cert.on_sale_info, OnSaleInfo),
                        ("The on_sale_info information should be created "
                         "automatically while creating a new cert. type."))

    def test_description(self):
        self.failUnless(self._cert.description == self._info.description,
                        ("Description should be `%s', got `%s'"
                         % (self._info.description, self._cert.description)))
        self._cert.description = "new description"
        self.failUnless((self._info.description ==
                         self._cert.description == "new description"),
                        ("New description should be `new description', got %s"
                         % self._cert.description))

    def test_price(self):
        self.failUnless(self._cert.price == self._info.price,
                        ("Price should be %s, got %s"
                         % (self._info.price, self._cert.price)))
        self._cert.price = currency(666)
        self.failUnless(self._info.price == self._cert.price,
                        "New price should be %s, got %s" % (self._cert.price,
                                                            self._info.price))

    def test_max_discount(self):
        self.failUnless(self._cert.max_discount == self._info.max_discount,
                        ("Max discount should be %s, got %s"
                         % (self._info.max_discount, self._cert.max_discount)))
        self._cert.max_discount = currency(70)
        self.failUnless(self._info.max_discount == self._cert.max_discount,
                        ("New max discount should be %s, got %s"
                         % (self._cert.price, self._info.max_discount)))

    def test_commission(self):
        self.failUnless(self._cert.commission == self._info.commission,
                        ("Commission should be %s, got %s"
                         % (self._info.commission, self._cert.commission)))
        self._cert.commission = currency(0)
        self.failUnless(self._info.commission == self._cert.commission,
                        ("New commission should be %s, got %s"
                         % (self._cert.commission, self._info.commission)))

    def test_active(self):
        self._cert.inactivate()
        actives = GiftCertificateType.get_active_gift_certificates(self.trans)
        self.failUnless(self._cert not in actives)
        self._cert.activate()
        actives = GiftCertificateType.get_active_gift_certificates(self.trans)
        self.failUnless(self._cert in actives)



class TestGiftCertificateAdaptToSellable(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self._info = BaseSellableInfo(price=currency(10), description="Testing",
                                      commission=currency(5),
                                      max_discount=currency(3),
                                      connection=self.trans)
        self._type = GiftCertificateType(base_sellable_info=self._info,
                                         connection=self.trans)
        gift = GiftCertificate(connection=self.trans)
        self.sellable = gift.addFacet(
            ISellable, base_sellable_info=self._type.base_sellable_info,
            connection=self.trans)

    def test_create(self):
        self.failUnless(self.sellable.status == ASellable.STATUS_AVAILABLE)

    def test_apply_as_payment_method(self):
        sale = self.create_sale()
        self.sellable.group = sale.addFacet(IPaymentGroup, connection=self.trans)
        self.failUnlessRaises(InvalidStatus, self.sellable.apply_as_payment_method)
        self.sellable.sell()
        self.sellable.apply_as_payment_method()
        self.failUnless(self.sellable.status == ASellable.STATUS_CLOSED,
                        ("The gift certificate status should be close at this "
                         "point"))
        self.failUnless(self.sellable.group.get_items().count() == 1,
                        ("The payment group where the gift certificate was "
                         "used should have 1 payment"))
