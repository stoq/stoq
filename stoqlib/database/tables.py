# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
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
     ('system', ["SystemTable", "TransactionEntry"]),
     ('parameter', ["ParameterData"]),
     ('account', ["BankAccount"]),
     ('profile', ["UserProfile", "ProfileSettings"]),
     ('person', ["Person"]),
     ('address', ["CityLocation", "Address"]),
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
                 "PersonAdaptToCreditProvider",
                 "PersonAdaptToTransporter",
                 "EmployeeRoleHistory"]),
     ('synchronization', ["BranchSynchronization"]),
     ('station', ["BranchStation"]),
     ('till', ["Till", "TillEntry"]),
     ('payment.category', ["PaymentCategory"]),
     ('payment.group', ["PaymentGroup"]),
     ('payment.method', ["PaymentMethod", "CheckData"]),
     ('payment.payment', ["Payment",
                          "PaymentAdaptToInPayment",
                          "PaymentAdaptToOutPayment"]),
     ('fiscal', ["CfopData", "FiscalBookEntry"]),
     ('sale', ["SaleItem",
               "DeliveryItem",
               "SaleItemAdaptToDelivery",
               "Sale"]),
     ('renegotiation', ["RenegotiationData"]),
     ('sellable', ["SellableUnit",
                   "SellableTaxConstant",
                   "SellableCategory",
                   "Sellable"]),
     ('service', ["Service"]),
     ('product', ["Product",
                  "ProductSupplierInfo",
                  "ProductAdaptToStorable",
                  "ProductStockItem"]),
     ('purchase', ["PurchaseOrder",
                   "Quotation",
                   "PurchaseItem",
                   "QuoteGroup"]),
     ('receiving', ["ReceivingOrder", "ReceivingOrderItem"]),
     ('devices', ["DeviceSettings",
                  "FiscalDayHistory",
                  "FiscalDayTax"]),
     ('commission', ["CommissionSource", "Commission"]),
     ('transfer', ["TransferOrder", "TransferOrderItem"]),
     ('inventory', ["Inventory", "InventoryItem"]),
     ('production', ["ProductionOrder",
                     "ProductionItem",
                     "ProductionMaterial",
                     "ProductionService"]),

]

# fullname (eg "stoqlib.domain.person.Person") -> class
_table_cache = {}
# list of classes, used by get_table_types where order is important
_table_list = []


def _import():
    for path, table_names in _tables:
        for table_name in table_names:
            klass = namedAny('stoqlib.domain.%s.%s' % (path, table_name))
            _table_cache[table_name] = klass
            _table_list.append(klass)


def get_table_type_by_name(table_name):
    """Gets a table by name.

    @param table_name: name of the table
    """

    if not _table_cache:
        _import()

    return _table_cache[table_name]


def get_table_types():
    if not _table_list:
        _import()

    return _table_list
