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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Classes for Stock Decrease Details Dialog """

import gtk
from kiwi.ui.objectlist import Column

from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class StockDecreaseDetailsDialog(BaseEditor):
    title = _(u"Manual Stock Decrease Details")
    hide_footer = True
    size = (700, 400)
    model_type = StockDecrease
    gladefile = "StockDecreaseDetails"
    proxy_widgets = ('confirm_date',
                     'branch_name',
                     'responsible_name',
                     'removed_by_name',
                     'cfop_description',
                     'reason')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_list.set_columns(self._get_product_columns())
        products = StockDecreaseItem.selectBy(stock_decrease=self.model,
                                              connection=self.conn)
        self.product_list.add_list(list(products))

    def _get_product_columns(self):
        return [Column("sellable.code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=130),
                Column("sellable.description", title=_("Description"),
                       data_type=str, expand=True),
                Column("quantity", title=_("Quantity"),
                        data_type=int, justify=gtk.JUSTIFY_RIGHT),
                ]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
