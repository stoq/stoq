# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
##
"""A list of all tables in database and a way to get them.

 Add new tables here:
 ('domain.modulo') : ['classA', 'classB', ...],

 module is the domain module which lives the classes in the list
 (classA, classB, ...).
"""


from kiwi.log import Logger
from kiwi.python import namedAny

from stoqlib.database.exceptions import ProgrammingError
from stoqlib.database.runtime import new_transaction
from stoqlib.database.database import db_table_name
from stoqlib.exceptions import StoqlibError
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
                 "PersonAdaptToCompany",
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
     ('till', ["Till",
               "TillAdaptToPaymentGroup"]),
     ('payment.destination', ["PaymentDestination", "StoreDestination",
                              "BankDestination"]),
     ('payment.operation', ["PaymentOperation", "POAdaptToPaymentDevolution",
                            "POAdaptToPaymentDeposit"]),
    # XXX Unfortunately we must add 'methods.py' module in two places
    # here since the class Payment needs one of its classes. This will
    # be fixed in bug 2036.
     ('payment.methods', ["PaymentMethod",
                          "AbstractPaymentMethodAdapter",
                          "PaymentMethodDetails"]),
     ('renegotiation', ["AbstractRenegotiationAdapter"]),
     ('payment.base', ["AbstractPaymentGroup",
                       "Payment",
                       "PaymentAdaptToInPayment",
                       "PaymentAdaptToOutPayment",
                       "CashAdvanceInfo"]),
     ('till', ["TillEntry"]),
     ('fiscal', ["CfopData", "AbstractFiscalBookEntry", "IcmsIpiBookEntry",
                 "IssBookEntry"]),
     ('payment.methods', ["BillCheckGroupData",
                          "PMAdaptToMoneyPM",
                          "AbstractCheckBillAdapter",
                          "PMAdaptToCheckPM",
                          "PMAdaptToBillPM",
                          "PMAdaptToCardPM",
                          "PMAdaptToFinancePM",
                          "PMAdaptToGiftCertificatePM",
                          "CardInstallmentSettings",
                          "DebitCardDetails",
                          "CreditCardDetails",
                          "CardInstallmentsStoreDetails",
                          "CardInstallmentsProviderDetails",
                          "FinanceDetails",
                          "CreditProviderGroupData",
                          "CheckData"]),
     ('sellable', ["OnSaleInfo", "BaseSellableInfo"]),
     ('giftcertificate', ["GiftCertificate",
                          "GiftCertificateAdaptToSellable",
                          "GiftCertificateItem",
                          "GiftCertificateType"]),
     ('sale', ["Sale", "SaleAdaptToPaymentGroup"]),
     ('renegotiation', ["RenegotiationData",
                        "RenegotiationAdaptToReturnSale",
                        "RenegotiationAdaptToExchange",
                        "RenegotiationAdaptToChangeInstallments"]),
     ('sellable', ["SellableUnit",
                   "ASellableCategory",
                   "BaseSellableCategory",
                   "SellableCategory",
                   "ASellable",
                   "ASellableItem"]),
     ('stock', ["AbstractStockItem"]),
     ('service', ["Service",
                  "ServiceAdaptToSellable",
                  "ServiceSellableItem",
                  "ServiceSellableItemAdaptToDelivery",
                  "DeliveryItem"]),
     ('product', ["Product",
                  "ProductSupplierInfo",
                  "ProductSellableItem",
                  "ProductStockReference",
                  "ProductAdaptToSellable",
                  "ProductAdaptToStorable",
                  "ProductStockItem",
                  "ProductRetentionHistory"]),
     ('purchase', ["PurchaseOrder",
                   "PurchaseOrderAdaptToPaymentGroup",
                   "PurchaseItem"]),
     ('receiving', ["ReceivingOrder", "ReceivingOrderItem",
                    "ReceivingOrderAdaptToPaymentGroup"]),
     ('devices', ["DeviceConstants",
                  "DeviceSettings"]),
]

# Format stoqlib_%s_seq, see get_sequences()
_sequences = [
    'abstract_bookentry',
    'branch_identifier',
    'branch_station',
    'payment_identifier',
    'purchase_ordernumber',
    'purchasereceiving_number',
    'sale_ordernumber',
    'sellable_code',
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
    """
    Gets a table by name.

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

def get_sequence_names():
    """
    @returns: a list of sequence names
    """
    global _sequences
    return ['stoqlib_%s_seq' % seq for seq in _sequences]

def create_tables(delete_only=False):
    trans = new_transaction()

    log.info('Dropping tables')
    table_types = get_table_types()
    for table in table_types:
        table_name = db_table_name(table)
        if trans.tableExists(table_name):
            trans.dropTable(table_name, cascade=True)

    log.info('Dropping sequences')
    for seq_name in get_sequence_names():
        if trans.sequenceExists(seq_name):
            trans.dropSequence(seq_name)

    if not delete_only:
        log.info('Creating tables')
        for table in table_types:
            table_name = db_table_name(table)
            if delete_only:
                continue
            try:
                table.createTable(connection=trans)
            except ProgrammingError, e:
                raise StoqlibError(
                    "An error occurred when creating %s table:\n"
                    "=========\n"
                    "%s\n" % (table_name, e))

        log.info('Creating sequences')
        for seq_name in get_sequence_names():
            trans.createSequence(seq_name)

    trans.commit()
