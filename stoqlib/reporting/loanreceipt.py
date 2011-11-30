# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

""" A Manual stock decrease receipt implementation """

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity, get_formatted_price
from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           TableColumn as TC, HIGHLIGHT_NEVER)
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.reporting.template import BaseStoqReport

_ = stoqlib_gettext


class LoanReceipt(BaseStoqReport):
    """Loan receipt
    """
    report_name = _("Loan Receipt")

    def __init__(self, filename, order, *args, **kwargs):
        self.order = order
        BaseStoqReport.__init__(self, filename, self.report_name,
                                do_footer=True, landscape=True, *args,
                                **kwargs)

        self._identify_client()
        self.add_blank_space()
        self._setup_items_table()
        self._add_notes()
        self._add_loan_notice()
        self._add_signatures()

    def _identify_client(self):
        branch = self.order.branch
        client = self.order.client.person
        user = self.order.responsible.person
        removed_by = self.order.removed_by or client.name

        cols = [TC('', style='Normal-Bold', width=130),
                TC('', expand=True, truncate=True),
                TC('', style='Normal-Bold', width=130),
                TC('', expand=True)]

        if self.order.close_date:
            date_str = _(u'Confirm Date:')
            date_obj = self.order.close_date.strftime('%x')
        else:
            date_str = _(u'Open Date:')
            date_obj = self.order.open_date.strftime('%x')

        # At first, it was an optional field.
        expire_date = u''
        if self.order.expire_date:
            expire_date = self.order.expire_date.strftime('%x')

        data = [
            [date_str, date_obj, _(u'Expire Date:'), expire_date],
            [_(u'Responsible:'), user.name, _(u'Client:'), client.name],
            [_(u'Branch:'), branch.get_description(),
             _(u'Removed By:'), removed_by],
        ]

        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    def _add_notes(self):
        details_str = self.order.notes
        if details_str:
            self.add_paragraph(_(u'Notes'), style='Normal-Bold')
            self.add_preformatted_text(details_str, style='Normal-Notes')

    def _get_table_columns(self):
        return [OTC(_("Code"), lambda obj: obj.sellable.code,
                    truncate=True, width=100),
                OTC(_("Category"), lambda obj:
                    obj.sellable.get_category_description(), width=100),
                OTC(_("Item"),
                    lambda obj: obj.sellable.get_description(),
                    truncate=True, expand=True),
                OTC(_("Quantity"), lambda obj: obj.get_quantity_unit_string(),
                    width=80, align=RIGHT),
                OTC(_("Price"), lambda obj: obj.price,
                    width=80, align=RIGHT)
            ]

    def _setup_items_table(self):
        items = list(self.order.get_items())
        items_qty = len(items)
        if items_qty > 1:
            items_text = _("%s items") % format_quantity(items_qty)
        else:
            items_text = _("%s item") % format_quantity(items_qty)

        summary = ["", "", items_text]
        self.add_object_table(items,
                              self._get_table_columns(),
                              summary_row=summary)

        # sale details
        cols = [TC('', expand=True),
                TC('', width=100, align='RIGHT'),
                TC('', width=100, style='Normal-Bold', align='RIGHT')]

        total = get_formatted_price(self.order.get_total_amount())
        data = [['', _(u'Total:'), total]]

        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    def _add_loan_notice(self):
        loan_notice = _(u'I inform and sign up to receive the items in full '
                         'working order and I am aware of the responsability '
                         'that I have for returning them, as well as the '
                         'return of the amounts involved, in case of loss, '
                         'damage or any event that make the product unusable.')
        self.add_paragraph(_(u'Loan Notice'), style='Normal-Bold')
        self.add_paragraph(loan_notice, style='Normal-Notes', ellipsize=False)

    def _add_signatures(self):
        if self.order.removed_by:
            name = self.order.removed_by
        else:
            name = self.order.client.person.name
        self.add_signatures([name])
        cols = [TC('', width=500, align=RIGHT), TC('', width=200, align=RIGHT)]
        data = [[_(u'RG:'), ''], [_(u'CPF:'), '']]
        self.add_column_table(data, cols, do_header=False, align=RIGHT,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    #
    # BaseReportTemplate hooks
    #

    def get_title(self):
        return _(u'Number: %s - Loan on %s') % (
                    self.order.get_order_number_str(),
                    self.order.open_date.strftime('%x'))
