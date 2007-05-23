# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##  Author(s):  George Y. Kussumoto         <george@async.com.br>
##
##
""" A receival receipt implementation """

from stoqlib.domain.interfaces import ICompany
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.template import BaseRMLReport

_ = stoqlib_gettext

class ReceivalReceipt(BaseRMLReport):
    """Receival receipt
        This class builds the namespace used in template
    """
    template_name = 'receipt.rml'
    title = _("Receival receipt")

    def __init__(self, filename, payments, sale):
        self.payments = payments
        self.sale = sale
        BaseRMLReport.__init__(self, filename)

    #
    # BaseRMLReport
    #

    def get_namespace(self):
        company = ICompany(self.sale.branch.person, None)
        if company:
            document = company.cnpj
        else:
            document = ""
        return dict(document=document,
                    order=self.sale,
                    drawee=self.sale.branch.person,
                    payer=self.sale.client.person,
                    payments=self.payments)
