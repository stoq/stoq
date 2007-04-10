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

from sqlobject.sqlbuilder import AND
from sqlobject import (UnicodeCol, DateTimeCol, ForeignKey, IntCol,
                       SQLObject, BoolCol)
from zope.interface import implements

from stoqlib.database.columns import PriceCol
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
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
        raise NotImplementedError("This method must be overwrited on child")

    def get_reversal_clone(self, invoice_number, **kwargs):
        conn = self.get_connection()
        cfop = sysparam(conn).DEFAULT_RETURN_SALES_CFOP
        cls = self.__class__
        return cls(connection=conn, cfop=cfop, branch=self.branch,
                   invoice_number=invoice_number, drawee=self.drawee,
                   is_reversal=True, payment_group=self.payment_group,
                   **kwargs)

    #
    # Classmethods
    #

    @classmethod
    def _get_entries_by_payment_group(cls, conn, payment_group):
        q1 = AbstractFiscalBookEntry.q.payment_groupID == payment_group.id
        q2 = AbstractFiscalBookEntry.q.is_reversal == False
        query = AND(q1, q2)
        results = cls.select(query, connection=conn)
        if results.count() > 1:
            raise DatabaseInconsistency("You should have only one fiscal "
                                        "entry for payment group %s"
                                        % payment_group)
        return results

    @classmethod
    def has_entry_by_payment_group(cls, conn, payment_group):
        entries = cls._get_entries_by_payment_group(conn, payment_group)
        if entries:
            return True
        return False

    @classmethod
    def get_entry_by_payment_group(cls, conn, payment_group):
        entries = cls._get_entries_by_payment_group(conn, payment_group)
        if not entries:
            raise StoqlibError("You should have at least one fiscal "
                               "entry for payment group %s"
                               % payment_group)
        return entries[0]


class IcmsIpiBookEntry(AbstractFiscalBookEntry):

    _inheritable = False
    icms_value = PriceCol()
    ipi_value = PriceCol()

    def reverse_entry(self, invoice_number):
        icms = -self.icms_value
        ipi = -self.ipi_value
        return self.get_reversal_clone(invoice_number, icms_value=icms,
                                       ipi_value=ipi)

class IssBookEntry(AbstractFiscalBookEntry):

    _inheritable = False
    iss_value = PriceCol()

    def reverse_entry(self, invoice_number):
        iss = -self.iss_value
        return self.get_reversal_clone(invoice_number, iss_value=iss)

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
