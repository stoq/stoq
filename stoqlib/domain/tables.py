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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):    Evandro Vale Miquelito <evandro@async.com.br>
##
"""A list of all tables in database and a way to get them.

 Add new tables here:
 ('domain.módulo') : ['classA', 'classB', ...],

 module is the domain module which lives the classes in the list
 (classA, classB, ...).
"""

import sys
import gettext

from stoqlib.exceptions import DatabaseError
from stoqlib.lib.runtime import get_connection

_ = lambda msg: gettext.dgettext('stoqlib', msg)


TABLES = [
     ('stoqlib.domain.system',             ("SystemTable",
                                           )),
     ('stoqlib.domain.base',               ("InheritableModelAdapter",
                                            "InheritableModel",
                                            )),
     ('stoqlib.lib.parameters',            ("ParameterData",
                                            )),
     ('stoqlib.domain.account',            ("BankAccount",
                                            "Bank",
                                            )),
     ('stoqlib.domain.profile',            ("UserProfile",
                                            "ProfileSettings",
                                            )),
     ('stoqlib.domain.person',             ("CityLocation", 
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
     ('stoqlib.domain.till',               ("Till",
                                            "TillAdaptToPaymentGroup",
                                            )),
     ('stoqlib.domain.payment.destination',("PaymentDestination",
                                            "StoreDestination",
                                            "BankDestination",
                                            )),
     ('stoqlib.domain.payment.operation',  ("PaymentOperation",
                                            "POAdaptToPaymentDevolution",
                                            "POAdaptToPaymentDeposit",
                                            )),
    # XXX Unfortunately we must add 'methods.py' module in two places
    # here since the class Payment needs one of its classes. This will
    # be fixed in bug 2036.
     ('stoqlib.domain.payment.methods',    ("PaymentMethod",
                                            "AbstractPaymentMethodAdapter",
                                            "PaymentMethodDetails",
                                            )),
     ('stoqlib.domain.renegotiation',      ("RenegotiationData",
                                            "RenegotiationAdaptToGiftCertificate",
                                            "RenegotiationAdaptToOutstandingValue",
                                            )),
     ('stoqlib.domain.payment.base',       ("AbstractPaymentGroup",
                                            "Payment",
                                            "PaymentAdaptToInPayment",
                                            "PaymentAdaptToOutPayment",
                                            "CashAdvanceInfo",
                                            )),
     ('stoqlib.domain.renegotiation',      ("RenegotiationAdaptToSaleReturnMoney",
                                            )),
     ('stoqlib.domain.payment.methods',    ("BillCheckGroupData",
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
     ('stoqlib.domain.sellable',           ("OnSaleInfo",
                                            "BaseSellableInfo",
                                            )),
     ('stoqlib.domain.giftcertificate',    ("GiftCertificate",
                                            "GiftCertificateAdaptToSellable",
                                            "GiftCertificateItem",
                                            "GiftCertificateType",
                                            )),
     ('stoqlib.domain.sale',               ("Sale",
                                            "SaleAdaptToPaymentGroup")),
     ('stoqlib.domain.sellable',           ("SellableUnit",
                                            "AbstractSellableCategory",
                                            "BaseSellableCategory",
                                            "SellableCategory", 
                                            "AbstractSellable",
                                            "AbstractSellableItem",
                                            )),
     ('stoqlib.domain.stock',              ("AbstractStockItem",
                                            )),
     ('stoqlib.domain.service',            ("Service",
                                            "ServiceAdaptToSellable",
                                            "ServiceSellableItem",
                                            "ServiceSellableItemAdaptToDelivery",
                                            "DeliveryItem",
                                            )),
     ('stoqlib.domain.product',            ("Product",
                                            "ProductSupplierInfo",
                                            "ProductSellableItem",
                                            "ProductStockReference",
                                            "ProductAdaptToSellable",
                                            "ProductAdaptToStorable",
                                            "ProductStockItem",
                                            )),
     ('stoqlib.domain.purchase',           ("PurchaseOrder",
                                            "PurchaseOrderAdaptToPaymentGroup",
                                            "PurchaseItem",
                                            )),
     ('stoqlib.domain.receiving',          ("ReceivingOrder",
                                            "ReceivingOrderItem",
                                            )),
     ('stoqlib.domain.devices',            ("DeviceSettings",
                                            ))
]


#
# Auxiliar routines
#


def check_tables():
    # We must check if all the tables are already in the database.
    table_types = get_table_types()
    conn = get_connection()

    for table_type in table_types:
        classname = table_type.get_db_table_name()
        try:
            if not conn.tableExists(classname):
                msg = _("Outdated schema. Table %s doesn't exist.\n"
                        "Run init-database script to fix this problem."
                        % classname)
                raise DatabaseError, msg
        except:
            type, value, trace = sys.exc_info()
            # TODO Raise a proper error if the database doesn't exist.
            msg = _("An error ocurred trying to access the database\n"
                    "This is the database error:\n%s. Error type is %s")
            raise DatabaseError(msg % (value, type))


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

