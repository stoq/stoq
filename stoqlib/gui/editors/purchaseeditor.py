# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Kussumoto        <george@async.com.br>
##
""" Purchase editors """


import datetime
from decimal import Decimal
import sys

import gtk

from kiwi.datatypes import ValidationError, currency
from kiwi.enums import ListType
from kiwi.ui.listdialog import ListDialog
from kiwi.ui.objectlist import Column

from stoqlib.database.orm import AND
from stoqlib.database.runtime import get_current_branch
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.views import (SoldItemView, ReturnedItemView,
                                  ConsignedItemAndStockView)
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PurchaseItemEditor(BaseEditor):
    gladefile = 'PurchaseItemEditor'
    model_type = PurchaseItem
    model_name = _("Purchase Item")
    proxy_widgets = ['cost',
                     'expected_receival_date',
                     'quantity',
                     'quantity_sold',
                     'quantity_returned',
                     'total',]

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        order = self.model.order
        if order.status == PurchaseOrder.ORDER_CONFIRMED:
            self._set_not_editable()

    def _setup_widgets(self):
        self.order.set_text("%04d" %  self.model.order.id)
        for widget in [self.quantity, self.cost, self.quantity_sold,
                       self.quantity_returned]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=sys.maxint,
                                                 step_incr=1))
        self.description.set_text(self.model.sellable.get_description())
        if sysparam(self.conn).USE_FOUR_PRECISION_DIGITS:
            self.cost.set_digits(4)
        else:
            self.cost.set_digits(DECIMAL_PRECISION)

    def _set_not_editable(self):
        self.cost.set_sensitive(False)
        self.quantity.set_sensitive(False)

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, PurchaseItemEditor.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_expected_receival_date__validate(self, widget, value):
        if value < datetime.date.today():
            return ValidationError(_(u'The expected receival date should be '
                                     'a future date or today.'))

    def on_cost__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The cost should be greater than zero.'))

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The quantity should be greater than '
                                     'zero.'))



class SaleItemsDialog(ListDialog):
    columns = [
        Column('code', title=_(u'Code'), data_type=str, sorted=True),
        #Column('sale_id', title=_(u'Sale #'), data_type=int, format='%05d'),
        Column('description', title=_(u'Description'), data_type=str,
                expand=True),
        Column('quantity', title=_(u'Quantity'), data_type=Decimal),
        Column('total_cost', title=_(u'Total (avg.)'), data_type=currency),
    ]
    list_type = ListType.READONLY
    size = (650, 300)
    title = _(u'View Sale Items')

    def __init__(self, items):
        self._sale_items = items
        ListDialog.__init__(self)
        self.set_list_type(self.list_type)
        self.set_size_request(*self.size)
        self.set_title(self.title)

    def populate(self):
        return self._sale_items


class InConsignmentItemEditor(PurchaseItemEditor):

    def __init__(self, conn, model):
        self._original_sold_qty = model.quantity_sold
        self._original_returned_qty = model.quantity_returned
        self._allowed_sold = None
        self._allowed_returned = None
        PurchaseItemEditor.__init__(self, conn, model)
        order = self.model.order
        assert order.status == PurchaseOrder.ORDER_CONSIGNED
        self._set_not_editable()
        self._set_constraints()
        # enable consignment fields
        self.sold_lbl.show()
        self.returned_lbl.show()
        self.quantity_sold.show()
        self.quantity_returned.show()
        self.sold_items_button.show()
        self.returned_items_button.show()

    def _set_constraints(self):
        consigned_items = self._get_consigned_items()
        sold = sum([i.quantity for i in self._get_sale_items()], 0)
        sold_consigned = sum([i.sold for i in consigned_items], 0)
        self._allowed_sold = min(sold - sold_consigned,
                                 self.model.quantity_received)
        if self._allowed_sold < 0:
            self._allowed_sold = 0

        returned_items = self._get_sale_items(returned=True)
        returned = sum([i.quantity for i in returned_items], 0)
        returned_consigned = sum([i.returned for i in consigned_items], 0)
        self._allowed_returned = min(returned - returned_consigned,
                                     self.model.quantity_received)
        if self._allowed_returned < 0:
            self._allowed_returned = 0

    def _get_sale_items(self, returned=False):
        if returned:
            view_class = ReturnedItemView
        else:
            view_class = SoldItemView

        branch = get_current_branch(self.conn)
        sellable = self.model.sellable
        start_date = self.model.order.open_date
        end_date = datetime.date.today()
        query = AND(view_class.q.id == sellable.id)

        return view_class.select_by_branch_date(query, branch=branch,
                                                date=(start_date, end_date),
                                                connection=self.conn)

    def _get_consigned_items(self):
        branch = get_current_branch(self.conn)
        start_date = self.model.order.open_date
        product = self.model.sellable.product
        query = AND(ConsignedItemAndStockView.q.product_id == product.id,
                    ConsignedItemAndStockView.q.branch==branch.id,
                    ConsignedItemAndStockView.q.purchased_date>=start_date)
        return ConsignedItemAndStockView.select(query, connection=self.conn)

    def _view_sale_items(self, returned=False):
        retval = run_dialog(SaleItemsDialog, self.get_toplevel(),
                            self._get_sale_items(returned=returned))

    #
    # Kiwi Callbacks
    #

    def on_quantity_sold__validate(self, widget, value):
        if value < self._original_sold_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))
        if self._allowed_sold is None:
            return

        if value and value > self._allowed_sold:
            return ValidationError(_(u'Invalid sold quantity.'))

    def on_quantity_returned__validate(self, widget, value):
        if value < self._original_returned_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))
        if self._allowed_returned is None:
            return

        if value and value > self._allowed_returned:
            return ValidationError(_(u'Invalid returned quantity'))

    def on_sold_items_button__clicked(self, widget):
        self._view_sale_items()

    def on_returned_items_button__clicked(self, widget):
        self._view_sale_items(returned=True)
