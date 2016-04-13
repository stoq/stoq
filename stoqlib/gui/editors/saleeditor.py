# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009-2016 Async Open Source <http://www.async.com.br>
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

import collections

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.forms import TextField

from stoqlib.api import api
from stoqlib.domain.event import Event
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.person import Client, SalesPerson
from stoqlib.domain.sale import Sale, SaleItem, SaleToken
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.credentialsdialog import CredentialsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor, BaseEditorSlave
from stoqlib.gui.editors.invoiceitemeditor import InvoiceItemEditor
from stoqlib.gui.fields import PersonField, PersonQueryField, DateTextField
from stoqlib.gui.widgets.calculator import CalculatorPopup
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.defaults import quantize, QUANTITY_PRECISION, MAX_INT
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SaleQuoteItemEditor(InvoiceItemEditor):
    model_type = SaleItem
    model_name = _("Sale Quote Item")

    def setup_slaves(self):
        self.item_slave = SaleQuoteItemSlave(self.store, self.model, parent=self)
        self.attach_slave('item-holder', self.item_slave)


class SaleQuoteItemSlave(BaseEditorSlave):
    gladefile = 'SaleQuoteItemSlave'
    model_type = SaleItem
    proxy_widgets = ['price', 'cfop']

    #: The manager is someone who can allow a bigger discount for a sale item.
    manager = None

    def __init__(self, store, model, parent):
        self.model = model
        self.icms_slave = parent.icms_slave
        self.ipi_slave = parent.ipi_slave
        # Use a temporary object to edit the quantities, so we can delay the
        # database constraint checks
        self.quantity_model = Settable(quantity=model.quantity,
                                       reserved=model.quantity_decreased)

        self.proxy = None
        BaseEditorSlave.__init__(self, store, self.model)

        sale = self.model.sale
        if sale.status == Sale.STATUS_CONFIRMED:
            self._set_not_editable()
        if model.parent_item:
            # We should not allow the user to edit the children
            self._set_not_editable()
            self.reserved.set_sensitive(False)

        sellable = model.sellable
        if sellable.product and sellable.product.is_package:
            # Do not allow the user to edit the price of the package
            self.price.set_sensitive(False)

    def _setup_widgets(self):
        self._calc = CalculatorPopup(self.price, CalculatorPopup.MODE_SUB)

        self.sale.set_text(unicode(self.model.sale.identifier))
        self.description.set_text(self.model.sellable.get_description())
        self.original_price.update(self.model.base_price)

        self.price.set_adjustment(gtk.Adjustment(lower=0, upper=MAX_INT,
                                                 step_incr=1, page_incr=10))
        unit = self.model.sellable.unit
        digits = QUANTITY_PRECISION if unit and unit.allow_fraction else 0
        for widget in [self.quantity, self.reserved]:
            widget.set_digits(digits)
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=MAX_INT,
                                                 step_incr=1, page_incr=10))

        manager = get_plugin_manager()
        self.nfe_is_active = manager.is_active('nfe')

        if not self.nfe_is_active:
            self.cfop_label.hide()
            self.cfop.hide()

        if not self._can_reserve():
            self.reserved.hide()
            self.reserved_lbl.hide()

        # We populate this even if it's hidden because we need a default value
        # selected to add to the sale item
        cfop_items = CfopData.get_for_sale(self.store)
        self.cfop.prefill(api.for_combo(cfop_items))

        self._update_total()
        self.reserved.get_adjustment().set_upper(self.quantity_model.quantity)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

        # Quantity is not in the proxy above so that it doen't get updated
        # before quantity_reserved in the database
        self.reserved_proxy = self.add_proxy(self.quantity_model,
                                             ['quantity', 'reserved'])

    def _set_not_editable(self):
        self.price.set_sensitive(False)
        self.quantity.set_sensitive(False)

    def _maybe_log_discount(self):
        # If not authorized to apply a discount or the CredentialsDialog is
        # cancelled, dont generate the log
        if not self.manager:
            return

        price = self.model.sellable.get_price_for_category(self.model.sale.client_category)
        new_price = self.price.read()

        if new_price >= price:
            return

        discount = 100 - new_price * 100 / price

        Event.log_sale_item_discount(
            store=self.store,
            sale_number=self.model.sale.identifier,
            user_name=self.manager.username,
            discount_value=discount,
            product=self.model.sellable.description,
            original_price=price,
            new_price=new_price)

    def _maybe_update_children_quantity(self):
        qty = self.model.quantity
        for child in self.model.children_items:
            component = child.get_component(self.model)
            child.quantity = qty * component.quantity

    def _maybe_reserve_products(self):
        if not self._can_reserve():
            # Not reserve products. But allow to edit sale item quantity,
            # if the batch is not informed or sale item has no
            # storable.
            self.model.quantity = self.quantity_model.quantity
            return

        decreased = self.model.quantity_decreased
        to_reserve = self.quantity_model.reserved
        diff = to_reserve - decreased

        for sale_item in self.model.children_items:
            component = sale_item.get_component(self.model)
            component_qty = component.quantity * diff
            if diff > 0:
                sale_item.reserve(component_qty)
            elif diff < 0:
                sale_item.return_to_stock(abs(component_qty))

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

    def _can_reserve(self):
        product = self.model.sellable.product
        # We cant reserve services
        if not product:
            return False

        storable = product.storable
        # Cant reserve products without storable, except if it is a package
        if not storable and not product.is_package:
            return False

        # If the storable is has batches, but the sale item still dont have, its
        # not possible to reserve.
        if storable and storable.is_batch and not self.model.batch:
            return False

        # No stock item means we cannot reserve any quantity yet
        if storable:
            stock_item = storable.get_stock_item(self.model.sale.branch,
                                                 self.model.batch)
            if stock_item is None:
                return False

        return True

    def _update_total(self):
        # We need to update the total manually, since the model quantity
        # update is delayed
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

    def on_confirm(self):
        self._maybe_log_discount()
        self._maybe_reserve_products()
        self._maybe_update_children_quantity()

    #
    # Kiwi callbacks
    #

    def after_price__changed(self, widget):
        if self.ipi_slave:
            self.ipi_slave.update_values()
        if self.icms_slave:
            self.icms_slave.update_values()

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
        manager = self.manager or api.get_current_user(self.store)

        if api.sysparam.get_bool('REUTILIZE_DISCOUNT'):
            extra_discount = self.model.sale.get_available_discount_for_items(
                user=manager, exclude_item=self.model)
        else:
            extra_discount = None
        valid_data = sellable.is_valid_price(
            value, category=self.model.sale.client_category,
            user=manager, extra_discount=extra_discount)

        if not valid_data['is_valid']:
            return ValidationError(
                (_(u'Max discount for this product is %.2f%%.') %
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

        if not self.model.has_children():
            storable = self.model.sellable.product.storable
            decreased = self.model.quantity_decreased
            to_reserve = value - decreased
            # There is no need to reserve more products
            if to_reserve <= 0:
                return

            stock_item = storable.get_stock_item(self.model.sale.branch,
                                                 self.model.batch)
            if to_reserve > stock_item.quantity:
                return ValidationError('Not enough stock to reserve.')
        else:
            for child in self.model.children_items:
                component = child.get_component(self.model)
                storable = child.sellable.product_storable
                decreased = child.quantity_decreased
                to_reserve = (value * component.quantity) - decreased
                if to_reserve <= 0:
                    return
                # XXX Should I keep child.batch here? Since batch is not
                # available as component yet
                stock_item = storable.get_stock_item(child.sale.branch, child.batch)
                if stock_item.quantity < to_reserve:
                    return ValidationError(_("One or more components for this package "
                                             "doesn't have enough of stock to reserve"))

    def on_price__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_PRIMARY:  # pragma no cover
            return

        # Ask for the credentials of a different user that can possibly allow a
        # bigger discount.
        self.manager = run_dialog(CredentialsDialog, self, self.store)
        self.price.validate(force=True)


class _BaseSalePersonChangeEditor(BaseEditor):
    model_type = Sale
    model_name = _('Sale')

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            identifier=TextField(_("Sale #"), proxy=True, editable=False),
            open_date=DateTextField(_("Open date"), proxy=True, editable=False),
            status_str=TextField(_("Status"), proxy=True, editable=False),
            salesperson_id=PersonField(_("Salesperson"), proxy=True,
                                       can_add=False, can_edit=False,
                                       person_type=SalesPerson),
            client=PersonQueryField(_("Client"), proxy=True,
                                    person_type=Client),
        )

    def on_confirm(self):
        self.model.group.payer = self.model.client and self.model.client.person


class SaleClientEditor(_BaseSalePersonChangeEditor):

    def setup_proxies(self):
        self.fields['salesperson_id'].set_sensitive(False)

    def on_client__content_changed(self, widget):
        client = widget.read()
        if client is not None and client.status != Client.STATUS_SOLVENT:
            self.fields['client'].gadget.update_edit_button(
                gtk.STOCK_DIALOG_WARNING)


class SalesPersonEditor(_BaseSalePersonChangeEditor):
    title = _('Salesperson change')

    def setup_proxies(self):
        field = self.fields['client']
        # TODO: Maybe kiwi should have an api to hide the whole field, just
        # like it has a set_sensitive on the field
        for widget in [field.widget, field.label_widget,
                       field.add_button, field.edit_button, field.delete_button]:
            if widget:
                widget.hide()


class SaleTokenEditor(BaseEditor):
    gladefile = 'SaleToken'
    model_type = SaleToken
    model_name = _('Sale token')
    proxy_widgets = ['code']
    confirm_widgets = ['code']

    def __init__(self, store, model=None, visual_mode=False):
        BaseEditor.__init__(self, store, model, visual_mode)
        if model:
            self.set_description(model.code)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, SaleTokenEditor.proxy_widgets)

    def create_model(self, store):
        return SaleToken(store=self.store, code=u'')

    def on_code__validate(self, widget, value):
        if self.model.check_unique_value_exists(self.model_type.code, value):
            return ValidationError(_("Code already in use"))
