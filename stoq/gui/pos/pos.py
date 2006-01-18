# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
##              Henrique Romano             <henrique@async.com.br>
##              Ariqueli Tejada Fonseca     <aritf@async.com.br>
##
"""
stoq/gui/pos/pos.py:

    Main interface definition for pos application.
"""

import gettext

import gtk
from kiwi.ui.dialogs import warning
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.database import rollback_and_begin
from stoqlib.gui.dialogs import notify_dialog
from stoqlib.gui.search import get_max_search_results
from stoqdrivers.constants import UNIT_WEIGHT

from stoq.gui.application import AppWindow
from stoq.lib.validators import format_quantity, get_price_format_str
from stoq.lib.parameters import sysparam
from stoq.lib.drivers import FiscalCoupon, read_scale_info
from stoq.domain.sellable import AbstractSellable, FancySellable
from stoq.domain.service import ServiceSellableItem
from stoq.domain.product import ProductSellableItem, FancyProduct
from stoq.domain.person import Person
from stoq.domain.till import get_current_till_operation
from stoq.domain.interfaces import ISellable, IClient
from stoq.gui.editors.person import ClientEditor
from stoq.gui.editors.delivery import DeliveryEditor
from stoq.gui.editors.service import ServiceItemEditor
from stoq.gui.wizards.sale import SaleWizard
from stoq.gui.wizards.person import run_person_role_dialog
from stoq.gui.search.sellable import SellableSearch
from stoq.gui.search.person import ClientSearch
from stoq.gui.search.sale import SaleSearch
from stoq.gui.pos.neworder import NewOrderEditor
from stoq.gui.slaves.price import PriceSlave

_ = gettext.gettext


class POSApp(AppWindow):
   
    app_name = _('Point of Sales')
    gladefile = "pos"
    client_widgets =  ('client',)
    product_widgets = ('product',)
    sellable_widgets = ('quantity',
                        'sellable_unit_label')
    klist_name = 'sellables'

    def __init__(self, app):
        AppWindow.__init__(self, app)
        if not get_current_till_operation(self.conn):
            notify_dialog(_("You need to open the till before start doing "
                            "sales."), _("Error"))
            self.app.shutdown()
        self.max_results = get_max_search_results()
        self.client_table = Person.getAdapterClass(IClient)
        self.coupon = None
        self._setup_widgets()
        self._setup_proxies()
        self._clear_order()
        self._update_widgets()

    def _clear_order(self):
        self.sellables.clear()
        for widget in (self.search_box, self.client_data_hbox,
                       self.list_vbox, self.CancelOrder):
            widget.set_sensitive(False)
        self.ResetOrder.set_sensitive(True)
        self.new_order_button.set_sensitive(True)
        self.sale = None
        self.client_proxy.new_model(self.sale, relax_type=True)

    def _delete_sellable_item(self, item):
        self.sellables.remove(item)
        table = type(item)
        table.delete(item.id, connection=self.conn)

    def _setup_proxies(self):
        self.client_proxy = self.add_proxy(widgets=POSApp.client_widgets)
        model = FancySellable()
        self.sellable_proxy = self.add_proxy(model, 
                                             widgets=POSApp.sellable_widgets)
        self.price_slave.set_model(model)
        self.product_proxy = self.add_proxy(FancyProduct(),
                                            POSApp.product_widgets)

    def _setup_entry_completion(self):
        # TODO Waiting for improvements in kiwi entry completion. We need a
        # better way to query strings immediately when typing in the
        # entry
        sellables = AbstractSellable.get_available_sellables(self.conn)
        sellables = sellables[:self.max_results]
        strings = [s.get_short_description() for s in sellables]
        self.product.set_completion_strings(strings, list(sellables))

    def _setup_widgets(self):
        can_edit = sysparam(self.conn).EDIT_SELLABLE_PRICE
        self.price_slave = PriceSlave(can_edit=can_edit)
        self.attach_slave("price_holder", self.price_slave)
        if can_edit:
            widget = self.price_slave.get_widget()
            widget.connect("activate", self.on_price_activate)

        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary_label = SummaryLabel(klist=self.sellables,
                                          column='total',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)
        if not sysparam(self.conn).HAS_DELIVERY_MODE:
            self.delivery_button.hide()
        self._setup_entry_completion()
        self.sellable_unit_label.set_size("small")
        self.sellable_unit_label.set_bold(True)
        self.warning_label.set_size("small")
        # Waiting for bug 2319
        self.client_details_button.set_sensitive(False)

    def _update_totals(self, *args):
        self.summary_label.update_total()

    def _get_sellable_by_code(self, code):
        sellable = AbstractSellable.selectBy(code=code,
                                             connection=self.conn)
        qty = sellable.count()
        if not qty:
            msg = _("The item '%s' doesn't exists" % code)
            self.product.set_invalid(msg)
            return
        if qty != 1:
            raise DatabaseInconsistency('You should have only one '
                                        'sellable with code %s' 
                                        % code)
        return sellable[0]

    def _coupon_add_item(self, sellable_item):
        if sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            return
        self.coupon.add_item(sellable_item)

    def _update_list(self, sellable, notify_on_entry=False):
        table = type(sellable)
        if not ISellable.implementedBy(table):
            raise TypeError("The object must implement a sellable facet.")
        sellables = [s.sellable for s in self.sellables]
        if sellable in sellables:
            if notify_on_entry:
                msg = _("The item '%s' was already added to the order" 
                        % sellable.base_sellable_info.description)
                self.product.set_invalid(msg)
            return
        else:
            quantity = self.sellable_proxy.model.quantity
            price = self.sellable_proxy.model.price
            sellable_item = sellable.add_sellable_item(self.sale,
                                                       quantity=quantity, 
                                                       price=price)
        if isinstance(sellable_item, ServiceSellableItem):
            model = self.run_dialog(ServiceItemEditor, self.conn, sellable_item)
            if not model:
                return
        self.sellables.append(sellable_item)
        self.sellables.select(sellable_item)
        self.product.set_text('')
        self._coupon_add_item(sellable_item)

    def _get_sellable(self):
        if self.product_proxy.model:
            sellable = self.product_proxy.model.product
        else:
            sellable = None
        if not sellable:
            code = self.product.get_text()
            sellable = self._get_sellable_by_code(code)
            if sellable:
                # Waiting for a select method on kiwi entry using entry
                # completions
                self.product.set_text(sellable.get_short_description())

        self.add_button.set_sensitive(sellable is not None)
        return sellable

    def add_sellable_item(self):
        if not self.add_button.get_property('sensitive'):
            return
        self.add_button.set_sensitive(False)
        sellable = self._get_sellable()
        if not sellable:
            return
        self._update_list(sellable, notify_on_entry=True)
        self.warning_box.hide()

    def select_first_item(self):
        if self.sellables:
            # XXX Probably kiwi should handle this for us. Waiting for
            # support
            self.sellables.select(self.sellables[0])

    def _new_order(self):
        rollback_and_begin(self.conn)
        self.sale = self.run_dialog(NewOrderEditor, self.conn)
        if self.sale:
            self.sellables.clear()
            self.client_proxy.new_model(self.sale)
            self._update_widgets()
            self._update_totals()
            for widget in (self.search_box, self.client_data_hbox,
                           self.list_vbox, self.footer_hbox,
                           self.CancelOrder):
                widget.set_sensitive(True)
            self.ResetOrder.set_sensitive(False)
            self.product.grab_focus()
            self.new_order_button.set_sensitive(False)
        else:
            rollback_and_begin(self.conn)
            return
        if sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            return
        if not self.coupon:
            self.coupon = FiscalCoupon(self.conn, self.sale)
        if self.sale.client:
            self.coupon.identify_customer(self.sale.client.get_adapted())
        while not self.coupon.open():
            if warning(
                _("It is not possible open a fiscal coupon"),
                _("It is not possible to start a new sale if the "
                  "fiscal coupon cannot be opened."),
                buttons=((_("Confirm later"), gtk.RESPONSE_CANCEL),
                         (_("Try Again"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                self.app.shutdown()

    def _update_widgets(self):
        has_sellables = len(self.sellables) >= 1
        widgets = [self.checkout_button, self.remove_item_button]
        for widget in widgets:
            widget.set_sensitive(has_sellables)
        has_client = self.sale is not None and self.sale.client is not None
        self.client_edit_button.set_sensitive(has_client)
        self.delivery_button.set_sensitive(has_client and has_sellables)
        model = self.sellables.get_selected()
        self._update_totals()
        has_sellable_str = self.product.get_text() != ''
        self.add_button.set_sensitive(has_sellable_str)

    def _read_scale(self):
        data = read_scale_info(self.conn)
        self.quantity.set_value(data.weight)
        sellable = self._get_sellable()
        current_price = sellable.base_sellable_info.price
        scale_price = data.price_per_kg
        if scale_price != 0.0 and current_price != scale_price:
            if not sysparam(self.conn).EDIT_SELLABLE_PRICE:
                msg = _("The price supplied by the scale doesn't match the "
                        "current one registered in the system and will be "
                        "ignored")
            else:
                msg = _("The price supplied by the scale is different that "
                        "the current one registered in the system")
                self.sellable_proxy.model.price = scale_price
                self.price_slave.update()
                self.warning_label.set_text(msg)
                self.warning_box.show()
        else:
            self.warning_box.hide()

    def get_columns(self):
        return [Column('sellable.code', title=_('Code'), sorted=True, 
                       data_type=str, width=90),
                Column('sellable.base_sellable_info.description', 
                       title=_('Description'), data_type=str, expand=True, 
                       searchable=True),
                Column('price', title=_('Price'), data_type=currency, 
                       width=90),
                Column('quantity', title=_('Quantity'), data_type=float,
                       width=90, format_func=format_quantity),
                Column('total', title=_('Total'), data_type=currency,
                       width=100)]
                       
    def _search_clients(self):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    # Not connect by Kiwi, since the 'price' entry widget belongs to
    # PriceSlave
    def on_price_activate(self, *args):
        self.add_sellable_item()

    #
    # AppWindow Hooks
    #

    def setup_focus(self): 
        self.search_box.set_focus_chain([self.product, self.quantity, 
                                         self.add_button])

    #
    # Callbacks
    #

    def key_control_r(self, *args):
        # FIXME Waiting for a bugfix in gazpacho. Accelerators doesn't work
        # for menuitems
        self._new_order()

    def key_control_l(self, *args):
        # FIXME Waiting for a bugfix in gazpacho. Accelerators doesn't work
        # for menuitems
        # Implement a search dialog for sales
        pass
        
    def key_control_p(self, *args):
        # FIXME Waiting for a bugfix in gazpacho. Accelerators doesn't work
        # for menuitems
        self._search_clients()

    def on_product__changed(self, *args):
        self.product.set_valid()

    def on_advanced_search__clicked(self, *args):
        # Ouch!, commit now ? yes, because SearchDialog synchronizes self.conn
        # internally. Actually this is not a problem since our sale object
        # is not valid (_is_valid_model defaults to False) until we finish the 
        # whole process trough SaleWizard.
        self.conn.commit()
        items = self.run_dialog(SellableSearch, self.conn)
        for item in items:
            self._update_list(item)
        self.select_first_item()
        self._update_totals()

    def on_add_button__clicked(self, *args):
        self.add_sellable_item()

    def on_product__activate(self, *args):
        sellable = self._get_sellable()
        if sellable and sellable.unit and sellable.unit.index == UNIT_WEIGHT:
            self._read_scale()
        self.quantity.grab_focus()

    def on_quantity__activate(self, *args):
        if sysparam(self.conn).EDIT_SELLABLE_PRICE:
            self.price_slave.get_widget().grab_focus()
        else:
            self.add_sellable_item()

    def on_sellables__selection_changed(self, *args):
        self._update_widgets()

    def on_client_edit_button__clicked(self, *args):
        if not (self.sale and self.sale.client):
            raise ValueError('You must have a client defined at this point')
        if run_person_role_dialog(ClientEditor, self, self.conn, 
                                  self.sale.client):
            self.conn.commit()

    def _on_clients_action__clicked(self, *args):
        self._search_clients()

    def after_product__changed(self, *args):
        self._update_widgets()
        sellable = self.product_proxy.model.product
        if not (sellable and self.product.get_text()):
            model = FancySellable()
            self.sellable_proxy.new_model(model)
            self.price_slave.set_model(model)
            return
        sellable_item = FancySellable(price=sellable.get_price(),
                                      unit=sellable.unit)
        self.price_slave.set_model(sellable_item)
        self.sellable_proxy.new_model(sellable_item)

    def on_remove_item_button__clicked(self, *args):
        item = self.sellables.get_selected()
        if (not sysparam(self.conn).CONFIRM_SALES_ON_TILL
            and not self.coupon.remove_item(item)):
            return
        self._delete_sellable_item(item)
        self.select_first_item()
        self._update_widgets()

    def _on_cancel_order_action_clicked(self, *args):
        self._clear_order()
        if not sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            self.coupon.cancel()

    def _on_resetorder_action__clicked(self, *args):
        self._new_order()

    def _on_sales_action__clicked(self, *args):
        self.run_dialog(SaleSearch, self.conn)
                      
    def on_delivery_button__clicked(self, *args):
        if not self.sellables:
            notify_dialog(_("You don't have products to delivery."),
                          _("Error"))
            return
        products = [obj for obj in self.sellables
                        if isinstance(obj, ProductSellableItem)
                           and obj.delivery_data is None]
        if not products:
            notify_dialog(_("All the products already have delivery "
                            "instructions"), _("Error"))
            return
        service = self.run_dialog(DeliveryEditor, self.conn, None, 
                                  self.sale, products)
        if not service:
            return
        self.sellables.append(service)
        self.sellables.select(service)
        self._coupon_add_item(service)

    def _sale_checkout(self, *args):
        param = sysparam(self.conn)
        skip_payment_step = (param.CONFIRM_SALES_ON_TILL and
                             param.SET_PAYMENT_METHODS_ON_TILL)
        if self.run_dialog(SaleWizard, self.conn, self.sale,
                           skip_payment_step=skip_payment_step):
            if not skip_payment_step and not param.CONFIRM_SALES_ON_TILL:
                if (not self.coupon.totalize()
                    or not self.coupon.setup_payments()
                    or not self.coupon.close()):
                    return
            self.conn.commit()
            self._clear_order()

    def on_checkout_button__clicked(self, *args):
        self._sale_checkout()

    def on_new_order_button__clicked(self, *args):
        self._new_order()

