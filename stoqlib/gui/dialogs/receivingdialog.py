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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Classes for Receiving Order Details Dialog """


import gtk
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.list import SummaryLabel
from kiwi.datatypes import currency

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.receivingslave import ReceivingInvoiceSlave
from stoqlib.domain.receiving import (ReceivingOrderItem,
                                      ReceivingOrder)

_ = stoqlib_gettext


class ReceivingOrderDetailsDialog(BaseEditor):
    """This dialog shows some important details about purchase receiving
    orders like:
     - history of received products
     - Invoice Details
     - Order details such transporter, supplier, etc.
    """

    title = _("Receiving Order Details")
    hide_footer = True
    size = (700, 400)
    model_type = ReceivingOrder
    gladefile = "ReceivingOrderDetailsDialog"

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_list.set_columns(self._get_product_columns())
        products = ReceivingOrderItem.selectBy(receiving_orderID=self.model.id,
                                               connection=self.conn)
        self.product_list.add_list(list(products))

        value_format = '<b>%s</b>'
        total_label = value_format % _("Total:")
        products_summary_label = SummaryLabel(klist=self.product_list,
                                              column='total',
                                             label=total_label,
                                              value_format=value_format)

        products_summary_label.show()
        self.products_vbox.pack_start(products_summary_label, False)

    def _get_product_columns(self):
        return [Column("sellable.code", title=_("Code"), data_type=str,
                        justify=gtk.JUSTIFY_RIGHT, width=130),
                Column("sellable.description", title=_("Description"),
                       data_type=str, width=80, expand=True),
                Column("quantity_unit_string", title=_("Quantity"),
                       data_type=str, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("cost", title=_("Cost"), width=80,
                       format_func=get_formatted_cost, data_type=currency,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("total", title=_("Total"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        receiving_date = self.model.get_receival_date_str()
        branch_name = self.model.get_branch_name()
        text = _('Received in <b>%s</b> for branch <b>%s</b>')
        header_text = text % (receiving_date, branch_name)
        self.header_label.set_markup(header_text)
        self.add_proxy(self.model, ['notes'])

    def setup_slaves(self):
        self.invoice_slave = ReceivingInvoiceSlave(self.conn, self.model,
                                                   visual_mode=True)
        self.attach_slave("details_holder", self.invoice_slave)
