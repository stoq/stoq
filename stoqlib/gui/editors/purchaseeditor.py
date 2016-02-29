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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Purchase editors """


import gtk
from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.lib.defaults import QUANTITY_PRECISION, MAX_INT
from stoqlib.lib.dateutils import localtoday
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
                     'total']

    def __init__(self, store, model, visual_mode=False):
        self.proxy = None
        BaseEditor.__init__(self, store, model, visual_mode)
        order = self.model.order
        if order.status == PurchaseOrder.ORDER_CONFIRMED:
            self._set_not_editable()

        self.sold_lbl.hide()
        self.returned_lbl.hide()
        self.quantity_sold.hide()
        self.quantity_returned.hide()

        if model.parent_item:
            # We should not allow the user to edit the children
            self._set_not_editable()
            parent_expected = model.parent_item.expected_receival_date
            self.expected_receival_date.update(parent_expected)
            self.expected_receival_date.set_sensitive(False)

    def _setup_widgets(self):
        self.order.set_text(unicode(self.model.order.identifier))
        for widget in [self.quantity, self.cost, self.quantity_sold,
                       self.quantity_returned]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=MAX_INT,
                                                 step_incr=1))

        unit = self.model.sellable.unit
        digits = QUANTITY_PRECISION if unit and unit.allow_fraction else 0
        for widget in [self.quantity,
                       self.quantity_sold,
                       self.quantity_returned]:
            widget.set_digits(digits)

        self.description.set_text(self.model.sellable.get_description())
        self.cost.set_digits(sysparam.get_int('COST_PRECISION_DIGITS'))

    def _set_not_editable(self):
        self.cost.set_sensitive(False)
        self.quantity.set_sensitive(False)

    def _maybe_update_children_quantity(self):
        for child in self.model.children_items:
            child_qty = child.get_component_quantity(self.model)
            child.quantity = self.model.quantity * child_qty

    #
    # Public API
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def on_confirm(self):
        self._maybe_update_children_quantity()

    #
    # Kiwi callbacks
    #

    def after_cost__changed(self, widget):
        if self.proxy:
            self.proxy.update('total')

    def after_quantity__changed(self, widget):
        if self.proxy:
            self.proxy.update('total')

    def on_expected_receival_date__validate(self, widget, value):
        if value < localtoday().date():
            return ValidationError(_(u'The expected receival date should be '
                                     'a future date or today.'))

    def on_cost__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The cost should be greater than zero.'))

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The quantity should be greater than '
                                     'zero.'))


class InConsignmentItemEditor(PurchaseItemEditor):
    proxy_widgets = PurchaseItemEditor.proxy_widgets[:]
    proxy_widgets.extend(['quantity_sold',
                          'quantity_returned'])

    def __init__(self, store, model):
        self._original_sold_qty = model.quantity_sold
        self._original_returned_qty = model.quantity_returned
        self._allowed_sold = None

        PurchaseItemEditor.__init__(self, store, model)
        order = self.model.order
        assert order.status == PurchaseOrder.ORDER_CONSIGNED
        self._set_not_editable()

        # disable expected_receival_date (the items was already received)
        self.expected_receival_date.set_sensitive(False)

        # enable consignment fields
        self.sold_lbl.show()
        self.returned_lbl.show()
        self.quantity_sold.show()
        self.quantity_returned.show()

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

        total = self.quantity_returned.read() + value
        if value and total > self.model.quantity_received:
            return ValidationError(_(u'Sold and returned quantity does '
                                     'not match.'))

    def on_quantity_returned__validate(self, widget, value):
        if value < self._original_returned_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))

        max_returned = self.model.quantity_received - self.quantity_sold.read()
        if value and value > max_returned:
            return ValidationError(_(u'Invalid returned quantity'))


class PurchaseQuoteItemEditor(PurchaseItemEditor):
    proxy_widgets = PurchaseItemEditor.proxy_widgets[:]
    proxy_widgets.remove('cost')

    def __init__(self, store, model):
        PurchaseItemEditor.__init__(self, store, model)
        self.cost.hide()
        self.cost_lbl.hide()
