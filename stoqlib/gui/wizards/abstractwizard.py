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

from kiwi.ui.widgets.list import SummaryLabel
from kiwi.datatypes import currency
from kiwi.python import Settable

from stoqlib.exceptions import BarcodeDoesNotExists
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.wizards import WizardEditorStep
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.giftcertificate import GiftCertificate

_ = stoqlib_gettext



#
# Abstract Wizards for items
#


class SellableItemStep(WizardEditorStep):
    """
    A wizard item step for sellable orders.

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
    table = ASellable
    item_table = None
    summary_label_text = None
    list_slave_class = AdditionListSlave

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self._update_widgets()
        self.unit_label.set_bold(True)

    # Public API

    def hide_add_and_edit_buttons(self):
        """
        Hides the add and edit buttons
        """
        self.slave.hide_add_button()
        self.slave.hide_edit_button()

    def get_quantity(self):
        """
        Returns the quantity of the current model or 1 if there is no model
        @returns: the quantity
        """
        return self.proxy.model and self.proxy.model.quantity or Decimal(1)

    #
    # Hooks
    #

    def setup_sellable_entry(self):
        result = ASellable.get_unblocked_sellables(self.conn)
        self.sellable.prefill([(sellable.get_description(), sellable)
                               for sellable in result
                                   if not isinstance(sellable.get_adapted(),
                                                     GiftCertificate)])

    def get_order_item(self):
        raise NotImplementedError('This method must be defined on child')

    def get_saved_items(self):
        raise NotImplementedError('This method must be defined on child')

    def get_columns(self):
        raise NotImplementedError('This method must be defined on child')

    def on_product_button__clicked(self, button):
        raise NotImplementedError('This method must be defined on child')

    def validate(self, sellable, cost, quantity):
        # A subclass must redefine this method to perform some
        # validation before the sellable be added/updated in the list
        return True

    #
    # WizardStep hooks
    #

    def next_step(self):
        raise NotImplementedError('This method must be defined on child')

    def post_init(self):
        self.sellable.grab_focus()
        self.sellable_hbox.set_focus_chain([self.sellable,
                                        self.quantity, self.cost,
                                        self.add_sellable_button,
                                        self.product_button])
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self.setup_sellable_entry()
        self.proxy = self.add_proxy(None, SellableItemStep.proxy_widgets)
        model = Settable(quantity=Decimal(1), price=currency(0),
                         sellable=None)
        self.sellable_proxy = self.add_proxy(model,
                                             SellableItemStep.sellable_widgets)

    def setup_slaves(self):
        self.slave = self.list_slave_class(
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

    def _setup_summary(self):
        # FIXME: Move this into AdditionListSlave
        self.summary = SummaryLabel(klist=self.slave.klist, column='total',
                                    label=self.summary_label_text,
                                    value_format='<b>%s</b>')
        self.summary.show()
        self.slave.list_vbox.pack_start(self.summary, expand=False)

    def _refresh_next(self):
        self.wizard.refresh_next(len(self.slave.klist))

    def _get_sellable(self):
        if self.proxy.model:
            sellable = self.sellable_proxy.model.sellable
        else:
            sellable = None
        if not sellable:
            barcode = self.sellable.get_text()
            try:
                sellable = ASellable.get_availables_and_sold_by_barcode(
                    self.conn, barcode)
            except BarcodeDoesNotExists, e:
                self.sellable.set_invalid(str(e))
                sellable = None

            if sellable:
                # Waiting for a select method on kiwi entry using entry
                # completions
                self.sellable.set_text(sellable.get_short_description())
        self.add_sellable_button.set_sensitive(sellable is not None)
        return sellable

    def _add_sellable(self):
        if not self.add_sellable_button.get_property('sensitive'):
            return
        self.add_sellable_button.set_sensitive(False)
        sellable = self._get_sellable()
        if not sellable:
            return
        self._update_list(sellable)

    def _update_list(self, sellable):
        if self.sellable_proxy.model.sellable is sellable:
            cost = self.proxy.model.cost
        else:
            cost = sellable.cost
        quantity = self.get_quantity()

        # For sellables already present in the list, increase the quantity of the
        # existing sellable. If the sellable is not in the list, just add it.
        sellables = [s.sellable for s in self.slave.klist]
        if sellable in sellables:
            item = self.slave.klist[sellables.index(sellable)]
            if not self.validate(item, cost, quantity):
                return
            item.quantity += quantity
            self.slave.klist.update(item)
        else:
            item = self.get_order_item(sellable, cost, quantity)
            if not self.validate(item, cost, quantity):
                return
            self.slave.klist.append(item)
        self._update_total()
        self.proxy.set_model(None, relax_type=True)
        self.sellable.set_text('')
        self.sellable.grab_focus()

    def _update_total(self):
        if self.summary:
            self.summary.update_total()
        self._refresh_next()
        self.force_validation()

    def _update_widgets(self):
        has_sellable_str = self.sellable.get_text() != ''
        self.add_sellable_button.set_sensitive(has_sellable_str)

    #
    # callbacks
    #

    def _on_list_slave__before_delete_items(self, slave, items):
        for item in items:
            self.item_table.delete(item.id, connection=self.conn)
        self._refresh_next()

    def _on_list_slave__after_delete_items(self, slave):
        self._update_total()

    def _on_list_slave__add_item(self, slave, item):
        self._update_total()

    def _on_list_slave__edit_item(self, slave, item):
        self._update_total()

    def on_add_sellable_button__clicked(self, button):
        self._add_sellable()
        self.quantity.update(self.get_quantity())

    def on_sellable__activate(self, combo):
        self._get_sellable()
        self.quantity.grab_focus()

    def after_sellable__content_changed(self, combo):
        self.sellable.set_valid()
        self._update_widgets()
        sellable = self.sellable_proxy.model.sellable
        if not (sellable and self.sellable.get_text()):
            self.proxy.set_model(None, relax_type=True)
            return
        model = Settable(quantity=self.quantity.read(), cost=sellable.cost,
                         sellable=sellable)
        self.proxy.set_model(model)

    def on_quantity__activate(self, entry):
        self._add_sellable()

    def on_cost__activate(self, entry):
        self._add_sellable()
