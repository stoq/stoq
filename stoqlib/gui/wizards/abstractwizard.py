# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Abstract wizard and wizard steps definition

Note that a good aproach for all wizards steps defined here is do
not require some specific implementation details for the main wizard. Use
instead signals and interfaces for that.
"""

from decimal import Decimal
import sys

import gtk

from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.list import SummaryLabel
from kiwi.python import Settable

from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.wizards import WizardEditorStep
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.domain.sellable import Sellable

_ = stoqlib_gettext



#
# Abstract Wizards for items
#


class SellableItemStep(WizardEditorStep):
    """A wizard item step for sellable orders.

    It defines the following:

      - sellable combobox
      - quantity spinbutton
      - cost entry
      - add button
      - sellable objectlist

    Optionally buttons to modify the list

      - Add
      - Remove
      - Edit

    """
    # FIXME: Rename to SellableItemStep
    gladefile = 'AbstractItemStep'
    sellable_widgets = ('sellable',)
    proxy_widgets = ('quantity',
                     'unit_label',
                     'cost')
    model_type = None
    table = Sellable
    item_table = None
    summary_label_text = None

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self.unit_label.set_bold(True)
        for widget in [self.quantity, self.cost]:
            widget.set_adjustment(gtk.Adjustment(lower=1, upper=sys.maxint,
                                                 step_incr=1))
        self._reset_sellable()
        if sysparam(conn).USE_FOUR_PRECISION_DIGITS:
            self.cost.set_digits(4)

    # Public API

    def hide_add_button(self):
        """Hides the add button
        """
        self.slave.add_button.hide()

    def hide_edit_button(self):
        """Hides the edit button
        """
        self.slave.hide_edit_button()

    def get_quantity(self):
        """Returns the quantity of the current model or 1 if there is no model
        @returns: the quantity
        """
        return self.proxy.model and self.proxy.model.quantity or Decimal(1)

    def get_model_item_by_sellable(self, sellable):
        """Returns a model instance by the given sellable.
        @returns: a model instance or None if we could not find the model.
        """
        for item in self.slave.klist:
            if item.sellable is sellable:
                return item

    #
    # Hooks
    #

    def setup_sellable_entry(self):
        result = Sellable.get_unblocked_sellables(self.conn)
        self.sellable.prefill([(sellable.get_description(), sellable)
                               for sellable in result])

    def get_order_item(self):
        raise NotImplementedError('This method must be defined on child')

    def get_saved_items(self):
        raise NotImplementedError('This method must be defined on child')

    def get_columns(self):
        raise NotImplementedError('This method must be defined on child')

    def on_product_button__clicked(self, button):
        raise NotImplementedError('This method must be defined on child')

    def sellable_selected(self, sellable):
        """This will be called when a sellable is selected in the combo.
        It can be overriden in a subclass if they wish to do additional
        logic at that point
        @param sellable: the selected sellable
        """
        if sellable:
            cost = sellable.cost
            quantity = Decimal(1)
        else:
            cost = None
            quantity = None

        model = Settable(quantity=quantity,
                         cost=cost,
                         sellable=sellable)

        self.proxy.set_model(model)

        has_sellable = bool(sellable)
        self.add_sellable_button.set_sensitive(has_sellable)
        self.quantity.set_sensitive(has_sellable)
        self.cost.set_sensitive(has_sellable)

    def validate(self, value):
        self.add_sellable_button.set_sensitive(value and bool(self.sellable.read()))
        self.wizard.refresh_next(value and bool(len(self.slave.klist)))

    #
    # WizardStep hooks
    #

    def next_step(self):
        raise NotImplementedError('This method must be defined on child')

    def post_init(self):
        self.sellable.grab_focus()
        self.item_hbox.set_focus_chain([self.sellable,
                                        self.quantity, self.cost,
                                        self.add_sellable_button,
                                        self.product_button])
        self.register_validate_function(self.validate)
        self.force_validation()

    def setup_proxies(self):
        self.setup_sellable_entry()
        self.proxy = self.add_proxy(None, SellableItemStep.proxy_widgets)
        model = Settable(quantity=Decimal(1),
                         cost=None,
                         sellable=None)
        self.sellable_proxy = self.add_proxy(model,
                                             SellableItemStep.sellable_widgets)

    def setup_slaves(self):
        self.slave = AdditionListSlave(
            self.conn, self.get_columns(),
            klist_objects=self.get_saved_items())
        self.slave.connect('before-delete-items',
                           self._on_list_slave__before_delete_items)
        self.slave.connect('after-delete-items',
                           self._on_list_slave__after_delete_items)
        self.slave.connect('on-edit-item', self._on_list_slave__edit_item)
        self.slave.connect('on-add-item', self._on_list_slave__add_item)
        self.attach_slave('list_holder', self.slave)
        self._setup_summary()
        self.sellable.grab_focus()

    def _setup_summary(self):
        # FIXME: Move this into AdditionListSlave
        self.summary = SummaryLabel(klist=self.slave.klist, column='total',
                                    label=self.summary_label_text,
                                    value_format='<b>%s</b>')
        self.summary.show()
        self.slave.list_vbox.pack_start(self.summary, expand=False)

    def _refresh_next(self):
        self.wizard.refresh_next(len(self.slave.klist))

    def _add_sellable(self):
        sellable = self.sellable.get_selected_data()
        assert sellable

        self._update_list(sellable)
        self.proxy.set_model(None)
        self.sellable.grab_focus()

    def _update_list(self, sellable):
        quantity = self.get_quantity()
        cost = sellable.cost
        item = self.get_order_item(sellable, cost, quantity)
        if item in self.slave.klist:
            self.slave.klist.update(item)
        else:
            self.slave.klist.append(item)

        self._update_total()
        self._reset_sellable()

    def _reset_sellable(self):
        self.proxy.set_model(None)
        self.sellable.set_text('')
        self.sellable_selected(None)

    def _update_total(self):
        if self.summary:
            self.summary.update_total()
        self._refresh_next()
        self.force_validation()

    #
    # callbacks
    #

    def _on_list_slave__before_delete_items(self, slave, items):
        for item in items:
            self.model.remove_item(item)
        self._refresh_next()

    def _on_list_slave__after_delete_items(self, slave):
        self._update_total()

    def _on_list_slave__add_item(self, slave, item):
        self._update_total()

    def _on_list_slave__edit_item(self, slave, item):
        self._update_total()

    def on_add_sellable_button__clicked(self, button):
        self._add_sellable()

    def on_sellable__activate(self, combo):
        self.quantity.grab_focus()

    def on_sellable__content_changed(self, combo):
        sellable = self.sellable.get_selected_data()
        self.sellable_selected(sellable)

    def on_quantity__activate(self, entry):
        self._add_sellable()

    def on_quantity__validate(self, entry, value):
        # only support integer quantities
        if value <= 0 or value != int(value):
            return ValidationError(_(u'The quantity must be a positive'
                                     ' integer number'))

    def on_cost__activate(self, entry):
        self._add_sellable()
