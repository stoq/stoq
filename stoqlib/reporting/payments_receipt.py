# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##


from stoqlib.api import api
from stoqlib.domain.interfaces import ICompany
from stoqlib.lib.cardinal_formatters import get_price_cardinal
from stoqlib.lib.formatters import get_formatted_price
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.reporting.base.tables import (TableColumn as TC, HIGHLIGHT_NEVER)
from stoqlib.reporting.template import BaseStoqReport

_ = stoqlib_gettext


class BasePaymentReceipt(BaseStoqReport):
    """ Base account receipt
    """

    def __init__(self, filename, payment, order, date, *args, **kwargs):
        self.payment = payment
        self.order = order
        self.receipt_date = date
        BaseStoqReport.__init__(self, filename, self.report_name,
                                do_footer=False, landscape=False, *args,
                                **kwargs)
        self.identify_payer()
        self.add_blank_space()
        self.identify_drawee()
        self.add_signature()

        # Create separator to cut the receipt copy.
        self.add_line(dash_pattern=1)

        # Duplicate data to generate a copy of receipt in same page.
        self.add_title(self.get_title())
        self.identify_payer()
        self.add_blank_space()
        self.identify_drawee()
        self.add_signature()

    def get_payer(self):
        """This should be implemented in subclasses"""
        raise NotImplementedError

    def get_drawee(self):
        """This should be implemented in subclasses"""
        raise NotImplementedError

    def identify_payer(self):
        payer = self.get_payer()
        data = []
        if payer:
            data.extend([
                [_("I/We Received from:"), payer.name],
                [_("Address:"), payer.get_address_string()],
            ])
        value = self.payment.value
        cols = [TC('', style='Normal-Bold', width=150),
                TC('', expand=True, truncate=True)]

        data.extend([
            [_("The importance of:"), get_price_cardinal(value).upper()],
            [_("Referring to:"), self.payment.description],
        ])

        self.add_paragraph(_('Payer'), style='Normal-Bold')
        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    def identify_drawee(self):
        drawee = self.get_drawee()
        company = ICompany(drawee, None)
        document = company.cnpj
        address = drawee.get_address_string()
        drawee_name = drawee.name

        cols = [TC('', style='Normal-Bold', width=150),
                TC('', expand=True, truncate=True)]

        self.add_paragraph(_('Drawee'), style='Normal-Bold')
        data = [
            [_("Drawee:"), drawee_name],
            [_("CPF/CNPJ/RG:"), document],
            [_("Address:"), address],
        ]

        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    def add_signature(self):
        self.add_signatures([_("Drawee")])

    #
    # BaseReportTemplate hooks
    #

    def get_title(self):
        total_value = get_formatted_price(self.payment.value)
        return _('Receipt: %s - Value: %s - Date: %s') % (
                 self.payment.get_payment_number_str(),
                 get_formatted_price(total_value),
                 self.receipt_date.strftime('%x'))


class InPaymentReceipt(BasePaymentReceipt):
    """ Accounts receivable receipt
    """
    report_name = _("Receival receipt")

    def __init__(self, filename, payment, sale, date, *args, **kwargs):
        self.sale = sale
        BasePaymentReceipt.__init__(self, filename, payment, order=sale,
                                    date=date, *args, **kwargs)

    def get_payer(self):
        return self.payment.group.payer

    def get_drawee(self):
        if self.sale:
            drawee = self.sale.branch.person
        else:
            conn = self.payment.get_connection()
            drawee = api.get_current_branch(conn).person
        return drawee


class OutPaymentReceipt(BasePaymentReceipt):
    """ Accounts payable receipt
    """
    report_name = _("Payment receipt")

    def __init__(self, filename, payment, purchase, date, *args, **kwargs):
        self.purchase = purchase
        BasePaymentReceipt.__init__(self, filename, payment, order=purchase,
                                    date=date, *args, **kwargs)

    def get_payer(self):
        if self.purchase:
            payer = self.purchase.branch.person
        else:
            conn = self.payment.get_connection()
            payer = api.get_current_branch(conn).person
        return payer

    def get_drawee(self):
        if self.purchase:
            drawee = self.purchase.supplier.person
        else:
            drawee = self.payment.group.recipient
        return drawee
