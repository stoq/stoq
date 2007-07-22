# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
##
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##             Johan Dahlin             <jdahlin@async.com.br>
##
""" Domain classes to manage fiscal informations.

Note that this whole module is Brazil-specific.
"""

import datetime

from sqlobject import (UnicodeCol, DateTimeCol, ForeignKey, IntCol,
                       SQLObject, BoolCol)
from zope.interface import implements

from stoqlib.database.columns import PriceCol
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.base import Domain, BaseSQLView, InheritableModel
from stoqlib.domain.interfaces import IDescribable, IReversal


class CfopData(Domain):
    """A Brazil-specific class wich defines a fiscal code of operations.
    In Brazil it means 'Codigo fiscal de operacoes e prestacoes'
    """
    implements(IDescribable)

    code = UnicodeCol()
    description = UnicodeCol()

    def get_description(self):
        return u"%s %s" % (self.code, self.description)


class AbstractFiscalBookEntry(InheritableModel):
    implements(IReversal)

    date = DateTimeCol(default=datetime.datetime.now)
    is_reversal = BoolCol(default=False)
    invoice_number = IntCol()
    cfop = ForeignKey("CfopData")
    branch = ForeignKey("PersonAdaptToBranch")
    drawee = ForeignKey("Person")
    payment_group = ForeignKey("AbstractPaymentGroup")

    def reverse_entry(self, invoice_number):
        raise NotImplementedError(
            "This method must be implemented in a subclass")

    #
    # Classmethods
    #

    @classmethod
    def has_entry_by_payment_group(cls, conn, payment_group):
        return bool(cls.get_entry_by_payment_group(conn, payment_group))

    @classmethod
    def get_entry_by_payment_group(cls, conn, payment_group):
        return cls.selectOneBy(payment_group=payment_group, 
                               is_reversal=False,
                               connection=conn)

class IcmsIpiBookEntry(AbstractFiscalBookEntry):

    _inheritable = False
    icms_value = PriceCol()
    ipi_value = PriceCol()

    def reverse_entry(self, invoice_number):
        conn = self.get_connection()
        return IcmsIpiBookEntry(
            icms_value=self.icms_value,
            ipi_value=self.ipi_value,
            cfop=sysparam(conn).DEFAULT_RETURN_SALES_CFOP,
            branch=self.branch,
            invoice_number=invoice_number,
            drawee=self.drawee,
            is_reversal=True,
            payment_group=self.payment_group,
            connection=conn)

class IssBookEntry(AbstractFiscalBookEntry):

    _inheritable = False
    iss_value = PriceCol()

    def reverse_entry(self, invoice_number):
        conn = self.get_connection()
        return IssBookEntry(
            iss_value=self.iss_value,
            cfop=sysparam(conn).DEFAULT_RETURN_SALES_CFOP,
            branch=self.branch,
            invoice_number=invoice_number,
            drawee=self.drawee,
            is_reversal=True,
            payment_group=self.payment_group,
            connection=conn)

#
# Views
#

class AbstractFiscalView(SQLObject, BaseSQLView):
    """Stores general informations about fiscal entries"""

    date = DateTimeCol()
    invoice_number = IntCol()
    cfop_code = UnicodeCol()
    cfop_data_id = IntCol()
    drawee_name = UnicodeCol()
    drawee_id = IntCol()
    branch_id = IntCol()
    payment_group_id = IntCol()

class IcmsIpiView(AbstractFiscalView):
    """Stores general informations about ICMS/IPI book entries"""

    icms_value = PriceCol()
    ipi_value = PriceCol()


class IssView(AbstractFiscalView):
    """Stores general informations about ISS book entries"""

    iss_value = PriceCol()
