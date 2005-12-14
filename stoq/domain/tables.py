# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):    Evandro Vale Miquelito <evandro@async.com.br>
##
"""
stoq/domain/tables.py:

    A list of all tables in database and a way to get them.

 Add new tables here:
 ('domain.módulo') : ['classA', 'classB', ...],

 module is the domain module which lives the classes in the list
 (classA, classB, ...).

"""

import gettext

from stoqlib.exceptions import DatabaseError
# XXX This is postgres specific. We should use a better approach which
# could accept many other databases. Waiting for SQLObject suport.
from psycopg import OperationalError

from stoq.lib.runtime import get_connection

_ = gettext.gettext



TABLES = [
     ('stoq.domain.base',                  ("InheritableModelAdapter",
                                            "InheritableModel",
                                            )),
     ('stoq.lib.parameters',               ("ParameterData",
                                            )),
     ('stoq.domain.account',               ("BankAccount",
                                            "Bank",
                                            )),
     ('stoq.domain.profile',               ("UserProfile",
                                            "ProfileSettings",
                                            )),
     ('stoq.domain.person',                ("CityLocation", 
                                            "EmployeeRole",
                                            "WorkPermitData",
                                            "MilitaryData",
                                            "VoterData",
                                            "Person",
                                            "Address",
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
                                            "EmployeeRoleHistory",
                                            )),
     ('stoq.domain.till',                  ("Till",
                                            "TillAdaptToPaymentGroup",
                                            )),
     ('stoq.domain.payment.destination',   ("PaymentDestination",
                                            "StoreDestination",
                                            "BankDestination",
                                            )),
     ('stoq.domain.payment.operation',     ("PaymentOperation",
                                            "POAdaptToPaymentDevolution",
                                            "POAdaptToPaymentDeposit",
                                            )),
    # XXX Unfortunately we must add 'methods.py' module in two places 
    # here since the class Payment needs one of its classes. This will
    # be fixed in bug 2036.
     ('stoq.domain.payment.methods',       ("PaymentMethod",
                                            "PaymentMethodAdapter",
                                            "PaymentMethodDetails",
                                            )),
     ('stoq.domain.payment.base',          ("AbstractPaymentGroup",
                                            "Payment",
                                            "PaymentAdaptToInPayment",
                                            "PaymentAdaptToOutPayment",
                                            "CashAdvanceInfo",
                                            )),
     ('stoq.domain.payment.methods',       ("BillCheckGroupData",
                                            "PMAdaptToMoneyPM",
                                            "AbstractCheckBillAdapter",
                                            "PMAdaptToCheckPM",
                                            "PMAdaptToBillPM",
                                            "PMAdaptToCardPM",
                                            "PMAdaptToFinancePM",
                                            "CardInstallmentSettings",
                                            "DebitCardDetails",
                                            "CreditCardDetails",
                                            "CardInstallmentsStoreDetails",
                                            "CardInstallmentsProviderDetails",
                                            "FinanceDetails",
                                            "CreditProviderGroupData", 
                                            "CheckData",
                                            )),
     ('stoq.domain.sale',                  ("Sale",
                                           "SaleAdaptToPaymentGroup")),
     ('stoq.domain.sellable',              ("AbstractSellableCategory",
                                            "BaseSellableCategory",
                                            "SellableCategory", 
                                            "AbstractSellable",
                                            "AbstractSellableItem",
                                            )),
     ('stoq.domain.stock',                 ("AbstractStockItem",
                                            )),
     ('stoq.domain.service',               ("Service",
                                            "ServiceAdaptToSellable",
                                            "ServiceSellableItem",
                                            "ServiceSellableItemAdaptToDelivery",
                                            )),
     ('stoq.domain.product',               ("Product",
                                            "ProductSupplierInfo", 
                                            "ProductSellableItem",
                                            "ProductStockReference", 
                                            "ProductAdaptToSellable",
                                            "ProductAdaptToStorable",
                                            "ProductStockItem",
                                            )),
     ('stoq.domain.purchase',              ("PurchaseOrder",
                                            "PurchaseOrderAdaptToPaymentGroup",
                                            "PurchaseItem",
                                            )),
     ('stoq.domain.drivers',               ("PrinterSettings",
                                            ))
]


#
# Auxiliar routines
#


def check_tables():
    # We must check if all the tables are already in the database.
    table_types = get_table_types()
    conn = get_connection()

    try:
        for table_type in table_types:
            classname = table_type.get_db_table_name()
            if not conn.tableExists(classname):
                msg = _("Outdated schema. Table %s doesn't exist.\n" 
                        "Run init-database script to fix this problem."
                        % classname)
                raise DatabaseError, msg

    except OperationalError, e:
        # Raise a proper error if the database doesn't exist.
        msg = _("An error ocurred trying to access the database\n"
                "This is the database error:\n%s")
        raise DatabaseError(msg % str(e))

def get_table_type_by_name(table_name, path=None):
    if not path:
        paths = [t[0] for t in TABLES if table_name in t[1]]
        assert paths and len(paths) == 1, 'Table %s not found' % table_name
        path = paths[0]

    try:
        module = __import__(path, globals(), locals(), table_name)
    except ImportError, reason:
        msg = 'Cannot import module %s: %s' % (table_name, reason)
        raise ImportError, msg

    try:
        klass = getattr(module, table_name)
    except AttributeError, reason:
        raise ImportError, \
              "Cannot import name %s from module %s: %s" \
              % (table_name, module.__name__, reason)
    return klass


def get_table_types():
    table_types = []
    for path, table_names in TABLES:
        for table_name in table_names:
            klass = get_table_type_by_name(table_name, path)
            table_types.append(klass)
    return table_types

