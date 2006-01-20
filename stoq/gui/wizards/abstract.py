# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/wizards/abstract.py:

    Abstract wizard steps definition
"""

import gettext

from kiwi.ui.widgets.list import SummaryLabel
from kiwi.python import Settable
from stoqlib.gui.wizards import BaseWizardStep
from stoqlib.gui.lists import AdditionListSlave

from stoq.lib.validators import get_price_format_str
from stoq.domain.product import Product
from stoq.domain.interfaces import ISellable

_ = gettext.gettext


#
# Wizard Steps
#


class AbstractProductStep(BaseWizardStep):
    """An abstract product step for purchases and receiving orders."""
    gladefile = 'AbstractProductStep'
    product_widgets = ('product',)
    proxy_widgets = ('quantity',
                     'unit_label',
                     'cost')
    model_type = None
    table = Product.getAdapterClass(ISellable)
    item_table = None
    summary_label_text = None

    def __init__(self, wizard, previous, conn, model):
        BaseWizardStep.__init__(self, conn, wizard, model, previous)
        self._update_widgets()
        self.unit_label.set_bold(True)

    def _refresh_next(self, validation_value):
        if not len(self.slave.klist):
            validation_value = False
        self.wizard.refresh_next(validation_value)

    def _setup_product_entry(self):
        products = self.table.get_available_sellables(self.conn)
        descriptions = [p.base_sellable_info.description for p in products]
        self.product.set_completion_strings(descriptions, list(products))

    def get_columns(self):
        raise NotImplementedError('This method must be defined on child')

    def _update_widgets(self):
        has_product_str = self.product.get_text() != ''
        self.add_item_button.set_sensitive(has_product_str)
        if self.add_item_button.get_property('visible'):
            has_product = (self.product_proxy.model and
                           self.product_proxy.model.product is not None)
            if has_product:
                text = _('Edit Product...')
            else:
                text = _('Add Product...')
            self.add_product_button.set_label(text)

    def _product_notify(self, msg):
        self.product.set_invalid(msg)

    def _get_sellable(self):
        if self.proxy.model:
            sellable = self.product_proxy.model.product
        else:
            sellable = None
        if not sellable:
            code = self.product.get_text()
            table = self.table
            sellable = table.get_availables_and_sold_by_code(self.conn, code,
                                                             self._product_notify)
            if sellable:
                # Waiting for a select method on kiwi entry using entry
                # completions
                self.product.set_text(sellable.get_short_description())
        self.add_item_button.set_sensitive(sellable is not None)
        return sellable

    def _update_total(self, *args):
        self.summary.update_total()
        self.force_validation()

    def _update_list(self, product):
        products = [s.sellable for s in self.slave.klist]
        if product in products:
            msg = (_("The product '%s' was already added to the order")
                     % product.base_sellable_info.description)
            self.product.set_invalid(msg)
            return
        if self.product_proxy.model.product is product:
            cost = self.proxy.model.cost
        else:
            cost = product.cost
        quantity = self.proxy.model and self.proxy.model.quantity or 1.0
        order_item = self.get_order_item(product, cost, quantity)
        self.slave.klist.append(order_item)
        self._update_total()
        self.proxy.new_model(None, relax_type=True)
        self.product.set_text('')
        self.product.grab_focus()

    def get_order_item(self):
        raise NotImplementedError('This method must be defined on child')

    def _add_item(self):
        if not self.add_item_button.get_property('sensitive'):
            return
        self.add_item_button.set_sensitive(False)
        product = self._get_sellable()
        if not product:
            return
        self._update_list(product)

    def get_saved_items(self):
        raise NotImplementedError('This method must be defined on child')

    #
    # WizardStep hooks
    #

    def next_step(self):
        raise NotImplementedError('This method must be defined on child')

    def post_init(self):
        self.product.grab_focus()
        self.product_hbox.set_focus_chain([self.product, 
                                           self.quantity, self.cost,
                                           self.add_item_button,
                                           self.product_button])
        self.register_validate_function(self._refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self.cost.set_data_format(get_price_format_str())
        self._setup_product_entry()
        self.proxy = self.add_proxy(None,
                                    AbstractProductStep.proxy_widgets)
        widgets = AbstractProductStep.product_widgets
        self.product_proxy = self.add_proxy(Settable(product=None), widgets)

    def setup_slaves(self):
        items = self.get_saved_items()
        self.slave = AdditionListSlave(self.conn, self.get_columns(), 
                                       klist_objects=items)
        self.slave.hide_add_button()
        self.slave.hide_edit_button()
        self.slave.connect('before-delete-items', self._before_delete_items)
        self.slave.connect('after-delete-items', self._update_total)
        self.slave.connect('on-edit-item', self._update_total)
        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary = SummaryLabel(klist=self.slave.klist, column='total',
                                    label=self.summary_label_text,
                                    value_format=value_format)
        self.summary.show()
        self.slave.list_vbox.pack_start(self.summary, expand=False)
        self.attach_slave('list_holder', self.slave)

    #
    # callbacks
    #

    def _before_delete_items(self, slave, items):
        for item in items:
            self.item_table.delete(item.id, connection=self.conn)

    def on_product_button__clicked(self, *args):
        raise NotImplementedError('This method must be defined on child')

    def on_add_product_button__clicked(self, *args):
        raise NotImplementedError('This method must be defined on child')

    def on_add_item_button__clicked(self, *args):
        self._add_item()

    def on_product__activate(self, *args):
        self._get_sellable()
        self.quantity.grab_focus()

    def on_product__changed(self, *args):
        self.product.set_valid()

    def after_product__changed(self, *args):
        self._update_widgets()
        product = self.product_proxy.model.product
        if not (product and self.product.get_text()):
            self.proxy.new_model(None, relax_type=True)
            return
        cost = product.cost
        model = Settable(quantity=1.0, cost=cost, product=product)
        self.proxy.new_model(model)

    def on_quantity__activate(self, *args):
        self._add_item()

    def on_cost__activate(self, *args):
        self._add_item()
