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
from kiwi.python import Settable
from kiwi.ui.listdialog import ListDialog
from kiwi.ui.objectlist import Column

from stoqlib.database.orm import AND
from stoqlib.database.runtime import get_current_branch
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.views import SoldItemView, ConsignedItemAndStockView
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


class InConsignmentItemDetails(BaseEditor):
    model_type = Settable
    model_name = _(u'Consignment Item')
    title = _(u'Consigment Item Details')
    gladefile = 'InConsignmentItemDetails'
    proxy_widgets = ['code', 'description',
                     'from_date', 'to_date',
                     'current_sold', 'total_sold',
                     'marked_sold', 'stocked',
                     'total_consigned', 'consignments_number',
                     'current_returned', 'to_return',]

    def _build_model(self):
        item = self.model.item
        sellable = item.sellable
        order = self.model.item.order
        total_consigned = 0
        marked_sold = 0
        stocked = 0
        for consigned_item in self.model.consigned_items:
            total_consigned += consigned_item.received
            marked_sold += consigned_item.sold
            stocked = consigned_item.stocked

        return Settable(code=sellable.code,
                        description=sellable.get_description(),

                        from_date=order.open_date,
                        to_date=datetime.date.today(),

                        current_sold=item.quantity_sold,
                        total_sold=sum([s.quantity for s in
                                        self.model.sold_items], Decimal(0)),
                        total_consigned=total_consigned,
                        consignments_number=int(
                                        self.model.consigned_items.count()),
                        marked_sold=marked_sold,
                        stocked=stocked,

                        current_returned=item.quantity_returned,
                        to_return=(item.quantity_received - item.quantity_sold
                                   - item.quantity_returned))

    def setup_proxies(self):
        model = self._build_model()
        self.add_proxy(model, self.proxy_widgets)


class InConsignmentItemEditor(PurchaseItemEditor):

    def __init__(self, conn, model):
        self._original_sold_qty = model.quantity_sold
        self._original_returned_qty = model.quantity_returned
        self._allowed_sold = None
        PurchaseItemEditor.__init__(self, conn, model)
        order = self.model.order
        assert order.status == PurchaseOrder.ORDER_CONSIGNED
        self._set_not_editable()
        self._set_constraints()
        # disable expected_receival_date (the items was already received)
        self.expected_receival_date.set_sensitive(False)
        # enable consignment fields
        self.sold_lbl.show()
        self.returned_lbl.show()
        self.quantity_sold.show()
        self.quantity_returned.show()
        self.details_button.show()

    def _set_constraints(self):
        # the allowed sold value consider:
        #     the quantity sold of the sellable
        #     the quantity set as sold in all the consignments opened since
        #     the current consignment
        #     the total quantity received in the current consignment
        #
        # So, the quantity sold is constrained by:
        #     the quantity sold of the sellable - the quantity set as sold in
        #     other consignments, or
        #     the total quantity received in the current consignment
        consigned_items = self._get_consigned_items()
        consigned_sold = sum([c.sold for c in consigned_items], 0)
        sold = sum([s.quantity for s in self._get_sold_items()], 0)

        self._allowed_sold = min(sold - consigned_sold,
                                 self.model.quantity_received)
        if self._allowed_sold < 0:
            self._allowed_sold = 0
        if self.model.quantity_sold > 0:
            self._allowed_sold += self.model.quantity_sold

    def _get_sold_items(self):
        """Returns the sold items of the sellable we are editing (through
        purchase_item) since the date of the current consignment
        (purchase_order) was opened. This is usefull because we need to know
        how many of this item was sold in the meantime.
        """
        branch = get_current_branch(self.conn)
        sellable = self.model.sellable
        start_date = self.model.order.open_date.date()
        end_date = datetime.date.today()
        query = AND(SoldItemView.q.id == sellable.id)
        return SoldItemView.select_by_branch_date(query, branch=branch,
                                                  date=(start_date, end_date),
                                                  connection=self.conn)

    def _get_consigned_items(self):
        """Returns the consigned items of the same sellable we are editing
        (through purchase_item), since date of the current consignment (purchase_order)
        was opened. This is usefull because we need to know how many of this
        item was consigned in the meantime.
        """
        branch = get_current_branch(self.conn)
        # use date() to ignore the time part of the datetime.
        start_date = self.model.order.open_date.date()
        product = self.model.sellable.product
        query = AND(ConsignedItemAndStockView.q.product_id == product.id,
                    ConsignedItemAndStockView.q.branch==branch.id,
                    ConsignedItemAndStockView.q.purchased_date>=start_date)
        return ConsignedItemAndStockView.select(query, connection=self.conn)

    def _view_sold_items(self):
        consignment_details = Settable(item=self.model,
                                       sold_items=self._get_sold_items(),
                                       consigned_items=self._get_consigned_items(),)

        retval = run_dialog(InConsignmentItemDetails, self.get_toplevel(),
                            self.conn, consignment_details)

    #
    # Kiwi Callbacks
    #

    def on_expected_receival_date__validate(self, widget, value):
        # Override the signal handler in PurchaseItemEditor, this is the
        # simple way to disable this validation, since we dont have the
        # handler_id to call self.expected_receival_date.disconnect() method.
        pass

    def on_quantity_sold__validate(self, widget, value):
        if value < self._original_sold_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))

        if self._allowed_sold is None:
            return

        total = self.quantity_returned.read() + value
        if value and total > self.model.quantity_received:
            return ValidationError(_(u'Sold and returned quantity does '
                                      'not match.'))

        if value and value > self._allowed_sold:
            return ValidationError(_(u'Invalid sold quantity.'))

    def on_quantity_returned__validate(self, widget, value):
        if value < self._original_returned_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))

        max_returned = self.model.quantity_received - self.quantity_sold.read()
        if value and value > max_returned:
            return ValidationError(_(u'Invalid returned quantity'))

    def on_details_button__clicked(self, widget):
        self._view_sold_items()
