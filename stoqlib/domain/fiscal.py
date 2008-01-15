# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
                       BoolCol)
from sqlobject.sqlbuilder import AND, LEFTJOINOn
from sqlobject.viewable import Viewable
from zope.interface import implements

from stoqlib.database.columns import PriceCol
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable, IReversal
from stoqlib.domain.person import Person


class CfopData(Domain):
    """A Brazil-specific class wich defines a fiscal code of operations.
    In Brazil it means 'Codigo fiscal de operacoes e prestacoes'
    """
    implements(IDescribable)

    code = UnicodeCol()
    description = UnicodeCol()

    def get_description(self):
        return u"%s %s" % (self.code, self.description)


class FiscalBookEntry(Domain):
    implements(IReversal)

    (TYPE_PRODUCT,
     TYPE_SERVICE) = range(2)

    date = DateTimeCol(default=datetime.datetime.now)
    is_reversal = BoolCol(default=False)
    invoice_number = IntCol()
    cfop = ForeignKey("CfopData")
    branch = ForeignKey("PersonAdaptToBranch")
    drawee = ForeignKey("Person")
    payment_group = ForeignKey("AbstractPaymentGroup")
    iss_value = PriceCol()
    icms_value = PriceCol()
    ipi_value = PriceCol()
    entry_type = IntCol()


    #
    # Classmethods
    #

    @classmethod
    def has_entry_by_payment_group(cls, conn, payment_group, entry_type):
        return bool(cls.get_entry_by_payment_group(
            conn, payment_group, entry_type))

    @classmethod
    def get_entry_by_payment_group(cls, conn, payment_group, entry_type):
        return cls.selectOneBy(payment_group=payment_group,
                               is_reversal=False,
                               entry_type=entry_type,
                               connection=conn)

    def reverse_entry(self, invoice_number):
        conn = self.get_connection()
        return FiscalBookEntry(
            entry_type=self.entry_type,
            iss_value=self.iss_value,
            icms_value=self.icms_value,
            ipi_value=self.ipi_value,
            cfop=sysparam(conn).DEFAULT_RETURN_SALES_CFOP,
            branch=self.branch,
            invoice_number=invoice_number,
            drawee=self.drawee,
            is_reversal=True,
            payment_group=self.payment_group,
            connection=conn)


class _FiscalBookEntryView(object):

    columns = dict(
        id=FiscalBookEntry.q.id,
        date=FiscalBookEntry.q.date,
        invoice_number=FiscalBookEntry.q.invoice_number,
        cfop_id=FiscalBookEntry.q.cfopID,
        branch_id=FiscalBookEntry.q.branchID,
        drawee_id=FiscalBookEntry.q.draweeID,
        payment_group_id=FiscalBookEntry.q.payment_groupID,
        cfop_code=CfopData.q.code,
        )

    clause = CfopData.q.id == FiscalBookEntry.q.cfopID

    joins = [
        LEFTJOINOn(None, Person,
                   Person.q.id == FiscalBookEntry.q.draweeID),
        ]


    @property
    def book_entry(self):
        return FiscalBookEntry.get(self.id,
                                   connection=self.get_connection())

    @property
    def drawee_name(self):
        if not self.drawee_id:
            return u""
        drawee = Person.get(self.drawee_id,
                            connection=self.get_connection())
        return drawee.name

class IcmsIpiView(_FiscalBookEntryView, Viewable):
    """
    Stores information about the taxes (ICMS and IPI) related to a
    certain product.
    This view is used to query the product tax information.

    @param id: the id of the fiscal_book_entry
    @param icms_value: the total value of icms
    @param ipi_value: the total value of ipi
    @param date: the date when the entry was created
    @param invoice_number: the invoice number
    @param cfop_data_id: the cfop
    @param cfop_code: the code of the cfop
    @param drawee_name: the drawee name
    @param drawee_id: the person
    @param branch_id: the branch
    @param payment_group_id: the payment group
    """

    columns = _FiscalBookEntryView.columns
    columns['icms_value'] = FiscalBookEntry.q.icms_value
    columns['ipi_value'] = FiscalBookEntry.q.ipi_value

    clause = AND(
        _FiscalBookEntryView.clause,
        FiscalBookEntry.q.entry_type == FiscalBookEntry.TYPE_PRODUCT,
        )
    joins = _FiscalBookEntryView.joins


class IssView(_FiscalBookEntryView, Viewable):
    """
    Stores information related to a service tax (ISS).
    This view is used to query the service tax information.

    @param id: the id of the fiscal_book_entry
    @param iss_value: the total value of ipi
    @param date: the date when the entry was created
    @param invoice_number: the invoice number
    @param cfop_data_id: the if of the cfop_data table
    @param cfop_code: the code of the cfop
    @param drawee_name: the drawee name
    @param drawee_id: the person
    @param branch_id: the branch
    @param payment_group_id: the payment group
    """

    columns = _FiscalBookEntryView.columns
    columns['iss_value'] = FiscalBookEntry.q.iss_value

    clause = AND(
        _FiscalBookEntryView.clause,
        FiscalBookEntry.q.entry_type == FiscalBookEntry.TYPE_SERVICE,
        )
    joins = _FiscalBookEntryView.joins
