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
## Author(s):   Henrique Romano  <henrique@async.com.br>
##

from twisted.trial import unittest

from zope.interface import implementedBy
from zope.interface.verify import verifyClass
from zope.interface.exceptions import Invalid

from stoqlib.database.tables import get_table_types

def _test_table(self, table):
    ifaces = implementedBy(table)
    if not ifaces:
        return
    for iface in ifaces:
        try:
            verifyClass(iface, table)
        except Invalid, message:
            self.fail("%s: %s" % (table.__name__, message))

namespace = {}
namespace['_test_table'] = _test_table
SKIPPED = {
    "AbstractCheckBillAdapter": "activate attribute was not provided",
    "AbstractPaymentGroup": "requires too many arguments",
    "AbstractPaymentMethodAdapter": "activate attribute was not provided",
    "AbstractSellable": "set_sold attribute was not provided",
    "CardInstallmentsProviderDetails": "activate attribute was not provided",
    "CardInstallmentsStoreDetails": "activate attribute was not provided",
    "CreditCardDetails": "activate attribute was not provided",
    "DebitCardDetails": "activate attribute was not provided",
    "DeviceConstants": "doesn't allow enough arguments",
    "FinanceDetails": "activate attribute was not provided",
    "GiftCertificateAdaptToSellable": "set_sold attribute was not provided",
    "IcmsIpiBookEntry": "requires too many arguments",
    "IssBookEntry": "requires too many arguments",
    "PMAdaptToBillPM": "activate attribute was not provided",
    "PMAdaptToCardPM": "activate attribute was not provided",
    "PMAdaptToCheckPM": "activate attribute was not provided",
    "PMAdaptToFinancePM": "activate attribute was not provided",
    "PMAdaptToGiftCertificatePM": "activate attribute was not provided",
    "PMAdaptToMoneyPM": "activate attribute was not provided",
    "PaymentAdaptToInPayment": "doesn't allow enough arguments",
    "PaymentAdaptToOutPayment": "doesn't allow enough arguments",
    "PaymentMethodDetails": "activate attribute was not provided",
    "ProductAdaptToSellable": "set_sold attribute was not provided.",
    "ProductAdaptToStorable": "doesn't allow enough arguments",
    "ProductSellableItem": "remove_items attribute was not provided",
    "PurchaseOrder": "remove_items attribute was not provided",
    "PurchaseOrderAdaptToPaymentGroup": "requires too many arguments",
    "ReceivingOrderAdaptToPaymentGroup": "requires too many arguments",
    "Sale": "remove_items attribute was not provided",
    "SaleAdaptToPaymentGroup": "requires too many arguments",
    "ServiceAdaptToSellable": "set_sold attribute was not provided",
    "TillAdaptToPaymentGroup": "requires too many arguments",
    }

for table in get_table_types():
    if not hasattr(table, "__implemented__"):
        continue
    tname = table.__name__
    name = 'test_' + tname
    func = lambda self, f=table: self._test_table(f)
    func.__name__ = name
    if tname in SKIPPED:
        func.skip = SKIPPED[tname]
    namespace[name] = func

TestInterfacesImplementation = type('TestInterfacesImplementation',
                                    (unittest.TestCase, ),
                                    namespace)
