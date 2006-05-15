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
##      Author(s):  Evandro Vale Miquelito
##
##
""" Domain classes to manage fiscal informations.

Note that this whole module is Brazil-specific.
"""

from datetime import datetime

from sqlobject import UnicodeCol, DateTimeCol, ForeignKey, IntCol, SQLObject
from zope.interface import implements

from stoqlib.domain.base import Domain, BaseSQLView
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.columns import PriceCol, AutoIncCol


class CfopData(Domain):
    """A Brazil-specific class wich defines a fiscal code of operations.
    In Brazil it means 'Codigo fiscal de operacoes e prestacoes'
    """
    implements(IDescribable)

    code = UnicodeCol()
    description = UnicodeCol()

    def get_description(self):
        return u"%s %s" % (self.code, self.description)


class InvoiceInfo(Domain):
    date = DateTimeCol(default=datetime.now)
    invoice_number = IntCol()
    cfop = ForeignKey("CfopData")
    branch = ForeignKey("PersonAdaptToBranch")
    drawee = ForeignKey("Person")
    payment_group = ForeignKey("AbstractPaymentGroup")


class IcmsIpiBookEntry(Domain):
    identifier = AutoIncCol("stoqlib_icmsbook_identifier_seq")
    icms_value = PriceCol()
    ipi_value = PriceCol()
    invoice_data = ForeignKey("InvoiceInfo")


class IssBookEntry(Domain):
    identifier = AutoIncCol("stoqlib_issbook_identifier_seq")
    iss_value = PriceCol()
    invoice_data = ForeignKey("InvoiceInfo")

#
# Views
#

class AbstractFiscalView(SQLObject, BaseSQLView):
    """Stores general informations about fiscal entries"""

    identifier = IntCol()
    date = DateTimeCol()
    invoice_number = IntCol()
    cfop_code = UnicodeCol()
    cfop_data_id = IntCol()
    invoice_data_id = IntCol()
    drawee_name = UnicodeCol()
    branch_id = IntCol()
    payment_group_id = IntCol()


class IcmsIpiView(AbstractFiscalView):
    """Stores general informations about ICMS/IPI book entries"""

    icms_value = PriceCol()
    ipi_value = PriceCol()


class IssView(AbstractFiscalView):
    """Stores general informations about ISS book entries"""

    iss_value = PriceCol()
