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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Classes for Transfer Order Details Dialog """

import gtk
from kiwi.datatypes import currency
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.list import SummaryLabel

from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TransferOrderDetailsDialog(BaseEditor):
    """This dialog shows some important details about transfer orders
    like:
        - The source and destination branches
        - The transfer quantity of each item
        - The cost of each item
    """

    title = _(u"Transfer Order Details")
    hide_footer = True
    size = (700, 400)
    model_type = TransferOrder
    gladefile = "TransferOrderDetails"
    proxy_widgets = ('open_date',
                     'receival_date',
                     'source_branch_name',
                     'destination_branch_name',
                     'source_responsible_name',
                     'destination_responsible_name')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_list.set_columns(self._get_product_columns())
        products = TransferOrderItem.selectBy(transfer_order=self.model,
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
                       data_type=str, expand=True),
                Column("quantity", title=_("Quantity"),
                        data_type=int, justify=gtk.JUSTIFY_RIGHT),
                Column("sellable.cost", title=_("Cost"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT),
                Column("total", title=_(u"Total Cost"), width=100,
                        data_type=currency, justify=gtk.JUSTIFY_RIGHT)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
