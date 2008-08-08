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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):    Evandro Vale Miquelito <evandro@async.com.br>
##               Johan Dahlin <jdahlin@async.com.br>
##
"""A list of all tables in database and a way to get them.

 Add new tables here:
 ('domain.modulo') : ['classA', 'classB', ...],

 module is the domain module which lives the classes in the list
 (classA, classB, ...).
"""


from kiwi.log import Logger
from kiwi.python import namedAny

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = Logger('stoqlib.database.tables')


_tables = [
     ('transaction', ["TransactionEntry"]),
     ('system', ["SystemTable"]),
     ('base', ["InheritableModelAdapter", "InheritableModel"]),
     ('parameter', ["ParameterData"]),
     ('account', ["BankAccount", "Bank"]),
     ('profile', ["UserProfile", "ProfileSettings"]),
     ('person', ["Person"]),
     ('address', ["CityLocation", "Address",]),
     ('person', ["EmployeeRole",
                 "WorkPermitData",
                 "MilitaryData",
                 "VoterData",
                 "Liaison",
                 "PersonAdaptToUser",
                 "Calls",
                 "PersonAdaptToIndividual",
                 "_PersonAdaptToCompany",
                 "PersonAdaptToClient",
                 "PersonAdaptToSupplier",
                 "PersonAdaptToEmployee",
                 "PersonAdaptToBranch",
                 "PersonAdaptToSalesPerson",
                 "PersonAdaptToBankBranch",
                 "PersonAdaptToCreditProvider",
                 "PersonAdaptToTransporter",
                 "EmployeeRoleHistory"]),
     ('synchronization', ["BranchSynchronization"]),
     ('station', ["BranchStation"]),
     ('till', ["Till", "TillEntry"]),
     ('payment.category', ["PaymentCategory"]),
     ('payment.destination', ["PaymentDestination", "StoreDestination",
                              "BankDestination"]),
     ('payment.operation', ["PaymentOperation", "POAdaptToPaymentDevolution",
                            "POAdaptToPaymentDeposit"]),
    # XXX Unfortunately we must add 'methods.py' module in two places
    # here since the class Payment needs one of its classes. This will
    # be fixed in bug 2036.
     ('payment.group', ["AbstractPaymentGroup"]),
     ('payment.methods', ["APaymentMethod",
                          "PaymentMethodDetails"]),
     ('payment.payment', ["Payment",
                          "PaymentAdaptToInPayment",
                          "PaymentAdaptToOutPayment"]),
     ('fiscal', ["CfopData", "FiscalBookEntry"]),
     ('payment.methods', ["BillCheckGroupData",
                          "CheckData",
                          "MoneyPM",
                          "CheckPM",
                          "BillPM",
                          "CardPM",
                          "FinancePM",
                          "GiftCertificatePM",
                          "CardInstallmentSettings",
                          "DebitCardDetails",
                          "CreditCardDetails",
                          "CardInstallmentsStoreDetails",
                          "CardInstallmentsProviderDetails",
                          "FinanceDetails",
                          "CreditProviderGroupData"]),
     ('sellable', ["OnSaleInfo", "BaseSellableInfo"]),
     ('giftcertificate', ["GiftCertificate",
                          "GiftCertificateAdaptToSellable",
                          "GiftCertificateType"]),
     ('sale', ["SaleItem",
               "DeliveryItem",
               "SaleItemAdaptToDelivery",
               "Sale",
               "SaleAdaptToPaymentGroup"]),
     ('renegotiation', ["RenegotiationData"]),
     ('sellable', ["SellableUnit",
                   "SellableTaxConstant",
                   "SellableCategory",
                   "ASellable"]),
     ('service', ["Service",
                  "ServiceAdaptToSellable"]),
     ('product', ["Product",
                  "ProductSupplierInfo",
                  "ProductAdaptToSellable",
                  "ProductAdaptToStorable",
                  "ProductStockItem",
                  "ProductRetentionHistory"]),
     ('purchase', ["PurchaseOrder",
                   "PurchaseOrderAdaptToPaymentGroup",
                   "PurchaseOrderAdaptToQuote",
                   "PurchaseItem",
                   "QuoteGroup"]),
     ('receiving', ["ReceivingOrder", "ReceivingOrderItem"]),
     ('devices', ["DeviceSettings",
                  "FiscalDayHistory",
                  "FiscalDayTax"]),
     ('commission', ["CommissionSource", "Commission"]),
     ('transfer', ["TransferOrder", "TransferOrderItem"]),
     ('inventory', ["Inventory", "InventoryItem"]),

]

# fullname (eg "stoqlib.domain.person.Person") -> class
_table_cache = {}
# list of classes, used by get_table_types where order is important
_table_list = []

def _import():
    global _table_cache, _table_list, _tables

    for path, table_names in _tables:
        for table_name in table_names:
            klass = namedAny('stoqlib.domain.%s.%s' % (path, table_name))
            _table_cache[table_name] = klass
            _table_list.append(klass)

def get_table_type_by_name(table_name):
    """Gets a table by name.

    @param table_name: name of the table
    """

    global _table_cache
    if not _table_cache:
        _import()

    return _table_cache[table_name]

def get_table_types():
    global _table_list
    if not _table_list:
        _import()

    return _table_list
