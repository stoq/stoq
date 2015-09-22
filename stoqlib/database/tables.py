# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
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

import collections
import logging
import os

from kiwi.python import namedAny

from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = logging.getLogger(__name__)


_tables = [
    ('system', ["SystemTable", "TransactionEntry"]),
    ('parameter', ["ParameterData"]),
    ('account', ['Account',
                 'AccountTransaction',
                 'BankAccount',
                 'BillOption']),
    ('profile', ["UserProfile", "ProfileSettings"]),
    ('person', ["Person"]),
    ('address', ["CityLocation", "Address"]),
    ('person', ["EmployeeRole",
                "WorkPermitData",
                "MilitaryData",
                "VoterData",
                "ContactInfo",
                "LoginUser",
                "Calls",
                "Individual",
                "Company",
                "Client",
                "Supplier",
                "Employee",
                "Branch",
                "SalesPerson",
                "Transporter",
                "EmployeeRoleHistory",
                "ClientCategory",
                "ClientSalaryHistory",
                "CreditCheckHistory",
                "UserBranchAccess"]),
    ('synchronization', ["BranchSynchronization"]),
    ('station', ["BranchStation"]),
    ('till', ["Till", "TillEntry"]),
    ('payment.card', ["CreditProvider", "CreditCardData", 'CardPaymentDevice',
                      'CardOperationCost']),
    ('payment.category', ["PaymentCategory"]),
    ('payment.comment', ["PaymentComment"]),
    ('payment.group', ["PaymentGroup"]),
    ('payment.method', ["PaymentMethod", "CheckData"]),
    ('payment.payment', ["Payment", "PaymentChangeHistory"]),
    ('payment.renegotiation', ["PaymentRenegotiation"]),
    ('fiscal', ["CfopData", "FiscalBookEntry",
                "Invoice"]),
    ('sale', ["SaleItem",
              "Delivery",
              "Sale",
              'SaleComment',
              'SaleToken']),
    ('returnedsale', ["ReturnedSale",
                      "ReturnedSaleItem"]),
    ('sellable', ["SellableUnit",
                  "SellableTaxConstant",
                  "SellableCategory",
                  'ClientCategoryPrice',
                  "Sellable"]),
    ('service', ["Service"]),
    ('product', ["Product",
                 "ProductComponent",
                 "ProductHistory",
                 'ProductManufacturer',
                 'ProductQualityTest',
                 "ProductSupplierInfo",
                 'StockTransactionHistory',
                 "ProductStockItem",
                 "GridGroup",
                 "GridAttribute",
                 "GridOption",
                 "ProductAttribute",
                 "ProductOptionMap",
                 "Storable",
                 'StorableBatch']),
    ('purchase', ["PurchaseOrder",
                  "Quotation",
                  "PurchaseItem",
                  "QuoteGroup"]),
    ('receiving', ["ReceivingOrder", "ReceivingOrderItem",
                   'PurchaseReceivingMap']),
    ('devices', ["DeviceSettings",
                 "FiscalDayHistory",
                 "FiscalDayTax"]),
    ('commission', ["CommissionSource", "Commission"]),
    ('transfer', ["TransferOrder", "TransferOrderItem"]),
    ('inventory', ["Inventory", "InventoryItem"]),
    ('image', ["Image"]),
    ('attachment', ["Attachment"]),
    ('stockdecrease', ["StockDecrease", "StockDecreaseItem"]),
    ('production', ["ProductionOrder",
                    "ProductionItem",
                    "ProductionItemQualityResult",
                    "ProductionMaterial",
                    "ProductionService",
                    "ProductionProducedItem"]),
    ('loan', ['Loan', 'LoanItem']),
    ('invoice', ['InvoiceField', 'InvoiceLayout',
                 'InvoicePrinter']),
    ('taxes', ['ProductIcmsTemplate',
               'ProductIpiTemplate',
               'ProductPisTemplate',
               'ProductCofinsTemplate',
               'ProductTaxTemplate',
               'InvoiceItemIcms',
               'InvoiceItemIpi',
               'InvoiceItemPis',
               'InvoiceItemCofins']),
    ('uiform', ['UIForm', 'UIField']),
    ('plugin', ['InstalledPlugin',
                'PluginEgg']),
    ('costcenter', ['CostCenter', 'CostCenterEntry']),
    ('stockdecrease', ['StockDecrease',
                       'StockDecreaseItem']),
    ('workorder', ['WorkOrder',
                   'WorkOrderItem',
                   'WorkOrderCategory',
                   'WorkOrderPackage',
                   'WorkOrderPackageItem',
                   'WorkOrderHistory']),
    ('event', ['Event']),
]

# table name (e.g. "Person") -> class
_tables_cache = collections.OrderedDict()


def _get_tables_cache():
    if _tables_cache:
        return _tables_cache

    for path, table_names in _tables:
        for table_name in table_names:
            klass = namedAny('stoqlib.domain.%s.%s' % (path, table_name))
            _tables_cache[table_name] = klass

    p_manager = get_plugin_manager()
    for p_name in p_manager.installed_plugins_names:
        plugin = p_manager.get_plugin(p_name)
        for path, table_names in plugin.get_tables():
            for table_name in table_names:
                desc = p_manager.get_description_by_name(p_name)
                basepath = os.path.basename(desc.dirname)
                klass = namedAny('.'.join([basepath, path, table_name]))
                _tables_cache[table_name] = klass

    return _tables_cache


def get_table_type_by_name(table_name):
    """Gets a table by name.

    :param table_name: name of the table
    """
    return _get_tables_cache()[table_name]


def get_table_types():
    return _get_tables_cache().values()
