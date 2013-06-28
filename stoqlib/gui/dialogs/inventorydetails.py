# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
""" Classes for inventory details """

import decimal

import gtk
from kiwi.currency import currency
from kiwi.ui.widgets.list import Column

from stoqlib.reporting.inventory import InventoryReport
from stoqlib.domain.inventory import Inventory
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.utils.printing import print_report

_ = stoqlib_gettext


class InventoryDetailsDialog(BaseEditor):
    """This class is for Inventory Details Dialog. This dialog display
    general informations about the selected inventory item on InventoryApp
    and about items related on the inventory.

    This dialog have six widgets. They will display the informations of the
    inventory selected. The |status_str| show dialog status string,
    the |identifier| show identifier, |branch_name| show the branch of the
    inventory, |open_date| is the open date of the inventory, |close_date|
    is the close date of the inventory if it was closed, and
    |invoice_number| show the invoice number of the current inventory.
    """
    gladefile = "InventoryDetailsDialog"
    model_type = Inventory
    title = _(u"Inventory Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('status_str',
                     'identifier',
                     'branch_name',
                     'open_date',
                     'close_date',
                     'invoice_number', )

    def __init__(self, store, model=None, visual_mode=False):
        """ Creates a new InventoryDetailsDialog object

        :param store: a store
        :param model: a :class:`stoqlib.domain.inventory.InventoryView` object
        """
        BaseEditor.__init__(self, store, model,
                            visual_mode=visual_mode)

    def _setup_widgets(self):
        self.items_list.set_columns(self._get_items_columns())

        self.items_list.add_list(self.model.get_items())

    def _get_items_columns(self):
        return [Column('code', _("Code"), sorted=True,
                       data_type=str, justify=gtk.JUSTIFY_CENTER),
                Column('description',
                       _("Description"), data_type=str, width=200,
                       expand=True, justify=gtk.JUSTIFY_LEFT),
                Column('recorded_quantity',
                       _("Recorded"), data_type=decimal.Decimal,
                       justify=gtk.JUSTIFY_LEFT),
                Column('actual_quantity',
                       _("Actual"), data_type=decimal.Decimal,
                       justify=gtk.JUSTIFY_LEFT),
                Column('is_adjusted', _("Adjusted"), data_type=bool,
                       justify=gtk.JUSTIFY_CENTER),
                Column('product_cost', _("Cost"), data_type=currency,
                       justify=gtk.JUSTIFY_LEFT, visible=False)]

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, InventoryDetailsDialog.proxy_widgets)

    #
    # Kiwi handlers
    #

    def on_print_button__clicked(self, button):
        print_report(InventoryReport, self.model)
