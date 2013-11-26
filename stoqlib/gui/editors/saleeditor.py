# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
""" Sale editors """

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.api import api
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.credentialsdialog import CredentialsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.taxslave import SaleItemICMSSlave, SaleItemIPISlave
from stoqlib.gui.widgets.calculator import CalculatorPopup
from stoqlib.lib.defaults import MAX_INT, quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SaleQuoteItemEditor(BaseEditor):
    gladefile = 'SaleQuoteItemEditor'
    model_type = SaleItem
    model_name = _("Sale Quote Item")
    proxy_widgets = ['price',
                     'cfop']

    #: The manager is someone who can allow a bigger discount for a sale item.
    manager = None

    def __init__(self, store, model):
        manager = get_plugin_manager()
        self.nfe_is_active = manager.is_active('nfe')
        self.proxy = None
        self.icms_slave = None
        self.ipi_slave = None

        # Use a temporary object to edit the quantities, so we can delay the
        # database constraint checks
        self.quantity_model = Settable(quantity=model.quantity,
                                       reserved=model.quantity_decreased)

        BaseEditor.__init__(self, store, model)

        sale = self.model.sale
        if sale.status == Sale.STATUS_CONFIRMED:
            self._set_not_editable()

    def _setup_widgets(self):
        self._calc = CalculatorPopup(self.price,
                                     CalculatorPopup.MODE_SUB)

        self.sale.set_text(unicode(self.model.sale.identifier))
        self.description.set_text(self.model.sellable.get_description())
        self.original_price.update(self.model.base_price)
        for widget in [self.quantity, self.price]:
            widget.set_adjustment(gtk.Adjustment(lower=1, upper=MAX_INT,
                                                 step_incr=1, page_incr=10))
        self.reserved.set_adjustment(gtk.Adjustment(lower=0,
                                                    upper=self.quantity_model.quantity,
                                                    step_incr=1, page_incr=10))
        first_page = self.tabs.get_nth_page(0)
        self.tabs.set_tab_label_text(first_page, _(u'Basic'))

        if self.nfe_is_active:
            self.cfop_label.hide()
            self.cfop.hide()

        if not self._can_reserve():
            self.reserved.hide()
            self.reserved_lbl.hide()

        # We populate this even if it's hidden because we need a default value
        # selected to add to the sale item
        cfop_items = [(item.get_description(), item)
                      for item in self.store.find(CfopData)]
        self.cfop.prefill(cfop_items)

        self._setup_taxes()
        self._update_total()

    def _can_reserve(self):
        # It is only possible to reserver for products with storable
        product = self.model.sellable.product
        if not product or not product.storable:
            return False

        # If the storable is has batches, but the sale item still dont have, its
        # not possible to reserve.
        storable = product.storable
        if storable.is_batch and not self.model.batch:
            return False

        return True

    def _setup_taxes(self):
        # This taxes are only for products, not services
        if not self.model.sellable.product:
            return

        if self.nfe_is_active:
            self.icms_slave = SaleItemICMSSlave(self.store,
                                                self.model.icms_info)
            self.add_tab(_('ICMS'), self.icms_slave)

            self.ipi_slave = SaleItemIPISlave(self.store, self.model.ipi_info)
            self.add_tab(_('IPI'), self.ipi_slave)

    def _update_total(self):
        # We need to update the total manually, since the model quantity update
        # is delayed
        total = self.model.price * self.quantity_model.quantity
        if self.model.ipi_info:
            total += self.model.ipi_info.v_ipi
        self.total.update(currency(quantize(total)))

    def _validate_quantity(self, new_quantity, allow_zero=False):
        if not allow_zero and new_quantity <= 0:
            return ValidationError(_(u"The quantity should be "
                                     u"greater than zero."))

        sellable = self.model.sellable
        if not sellable.is_valid_quantity(new_quantity):
            return ValidationError(_(u"This product unit (%s) does not "
                                     u"support fractions.") %
                                   sellable.unit_description)

    def add_tab(self, name, slave):
        event_box = gtk.EventBox()
        event_box.set_border_width(6)
        event_box.show()
        self.tabs.append_page(event_box, gtk.Label(name))
        self.attach_slave(name, slave, event_box)

    def _set_not_editable(self):
        self.price.set_sensitive(False)
        self.quantity.set_sensitive(False)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

        # Quantity is not in the proxy above so that it doen't get updated
        # before quantity_reserved in the database
        self.reserved_proxy = self.add_proxy(self.quantity_model,
                                             ['quantity', 'reserved'])

    def on_confirm(self):
        if not self._can_reserve():
            return

        decreased = self.model.quantity_decreased
        to_reserve = self.quantity_model.reserved
        diff = to_reserve - decreased
        if diff > 0:
            # Update quantity first, so that the db constraint does not break
            self.model.quantity = self.quantity_model.quantity
            # We need to decrease a few more from the stock
            self.model.reserve(diff)
        elif diff < 0:
            # We need to return some items to the stock
            self.model.return_to_stock(abs(diff))
            # Update quantity last, so that the db constraint does not break
            self.model.quantity = self.quantity_model.quantity
        else:
            # even if there is no products to reserve, we still need to set the
            # quantity value.
            self.model.quantity = self.quantity_model.quantity

    #
    # Kiwi callbacks
    #

    def after_price__changed(self, widget):
        if self.icms_slave:
            self.icms_slave.update_values()
        if self.ipi_slave:
            self.ipi_slave.update_values()

        self._update_total()

    def after_quantity__changed(self, widget):
        self._update_total()

        reserved = min(self.quantity_model.quantity,
                       self.quantity_model.reserved)
        self.reserved.get_adjustment().set_upper(self.quantity_model.quantity)
        self.reserved.update(reserved)

    def on_price__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u"The price must be greater than zero."))

        if (not sysparam.get_bool('ALLOW_HIGHER_SALE_PRICE') and
            value > self.model.base_price):
            return ValidationError(_(u'The sell price cannot be greater '
                                   'than %s.') % self.model.base_price)

        sellable = self.model.sellable
        self.manager = self.manager or api.get_current_user(self.store)

        if api.sysparam.get_bool('REUTILIZE_DISCOUNT'):
            extra_discount = self.model.sale.get_available_discount_for_items(
                user=self.manager, exclude_item=self.model)
        else:
            extra_discount = None

        valid_data = sellable.is_valid_price(
            value, category=self.model.sale.client_category,
            user=self.manager, extra_discount=extra_discount)

        if not valid_data['is_valid']:
            return ValidationError(
                _(u'Max discount for this product is %.2f%%.' %
                  valid_data['max_discount']))

    def on_quantity__validate(self, widget, value):
        return self._validate_quantity(value)

    def on_reserved__validate(self, widget, value):
        if not self._can_reserve():
            return

        # Do some pre-validation
        valid = self._validate_quantity(value, allow_zero=True)
        if valid:
            return valid

        storable = self.model.sellable.product.storable
        decreased = self.model.quantity_decreased
        to_reserve = value - decreased
        # There is no need to reserve more products
        if to_reserve <= 0:
            return

        stock_item = storable.get_stock_item(self.model.sale.branch,
                                             self.model.batch)
        if to_reserve > stock_item.quantity:
            return ValidationError('Not enought stock to reserve.')

    def on_price__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_PRIMARY:
            return

        # Ask for the credentials of a different user that can possibly allow a
        # bigger discount.
        self.manager = run_dialog(CredentialsDialog, self, self.store)
        if self.manager:
            self.price.validate(force=True)
