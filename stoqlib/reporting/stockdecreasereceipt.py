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
from stoqlib.lib.formatters import format_quantity
from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           TableColumn as TC, HIGHLIGHT_NEVER)
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.reporting.template import BaseStoqReport

_ = stoqlib_gettext


class StockDecreaseReceipt(BaseStoqReport):
    """Stock Decrease receipt
        This class builds the namespace used in template
    """
    report_name = _("Manual Stock Decrease Receipt")

    def __init__(self, filename, order, *args, **kwargs):
        self.order = order
        BaseStoqReport.__init__(self, filename, self.report_name,
                                do_footer=True, landscape=True, *args,
                                **kwargs)

        self._identify_removed_by()
        self._add_reason()
        self._add_cfop()
        self.add_blank_space()
        self._setup_items_table()
        self._add_signatures()

    def _identify_removed_by(self):
        branch = self.order.branch
        employee = self.order.removed_by.person
        user = self.order.responsible.person

        cols = [TC('', style='Normal-Bold', width=130),
                TC('', expand=True, truncate=True),
                TC('', style='Normal-Bold', width=130),
                TC('', expand=True)]

        data = [
            [_(u'Branch:'), branch.get_description(), '', ''],
            [_(u'Responsible:'), user.name, _(u'Removed By:'), employee.name],
        ]

        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    def _add_reason(self):
        details_str = self.order.reason

        self.add_paragraph(_(u'Reason'), style='Normal-Bold')
        self.add_preformatted_text(details_str, style='Normal-Notes')

    def _add_cfop(self):
        details_str = self.order.cfop.get_description()

        self.add_paragraph(_('C.F.O.P.'), style='Normal-Bold')
        self.add_preformatted_text(details_str, style='Normal-Notes')

    def _get_table_columns(self):
        return [OTC(_("Code"), lambda obj: obj.sellable.code,
                    truncate=True, width=100),
                OTC(_("Item"),
                    lambda obj: obj.sellable.get_description(),
                    truncate=True, expand=True),
                OTC(_("Quantity"), lambda obj: obj.get_quantity_unit_string(),
                    width=80, align=RIGHT),
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

    def _add_signatures(self):
        self.add_signatures([_(u"Responsible"), _(u'Removed By')])

    def get_title(self):
        return _(u'Number: %s - Manual stock decrease on %s') % (
                    self.order.get_order_number_str(),
                    self.order.confirm_date.strftime('%x'))
