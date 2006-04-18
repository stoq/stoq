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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Ariqueli Tejada Fonseca     <aritf@async.com.br>
##
""" Main interface definition for pos application.  """

import gettext
import decimal

import gtk
from kiwi.ui.dialogs import warning, messagedialog
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel
from kiwi.python import Settable
from stoqdrivers.constants import UNIT_WEIGHT
from stoqlib.database import rollback_and_begin, finish_transaction
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.runtime import new_transaction
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.drivers import (FiscalCoupon, read_scale_info,
                              get_current_scale_settings)
from stoqlib.domain.sellable import (AbstractSellable, FancySellable,
                                     SellableView)
from stoqlib.domain.service import ServiceSellableItem
from stoqlib.domain.product import ProductSellableItem, Product
from stoqlib.domain.person import Person
from stoqlib.domain.till import get_current_till_operation
from stoqlib.domain.interfaces import (ISellable, IClient, IDelivery,
                                       IStorable)
from stoqlib.gui.base.dialogs import notify_dialog
from stoqlib.gui.editors.person import ClientEditor
from stoqlib.gui.editors.delivery import DeliveryEditor
from stoqlib.gui.editors.service import ServiceItemEditor
from stoqlib.gui.wizards.sale import SaleWizard
from stoqlib.gui.wizards.person import run_person_role_dialog
from stoqlib.gui.search.sellable import SellableSearch
from stoqlib.gui.search.person import ClientSearch
from stoqlib.gui.search.sale import SaleSearch
from stoqlib.gui.search.product import ProductSearch
from stoqlib.gui.search.service import ServiceSearch
from stoqlib.gui.search.giftcertificate import GiftCertificateSearch
from stoqlib.gui.slaves.price import PriceSlave
from stoqlib.reporting.sale import SaleOrderReport

from stoq.gui.application import AppWindow
from stoq.gui.pos.neworder import NewOrderEditor

_ = gettext.gettext


class POSApp(AppWindow):

    app_name = _('Point of Sales')
    app_icon_name = 'stoq-pos-app'
    gladefile = "pos"
    order_widgets =  ('client',
                      'order_number',
                      'salesperson')
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
        self.max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        self.client_table = Person.getAdapterClass(IClient)
        self.coupon = None
        self._setup_widgets()
        self._setup_proxies()
        self._clear_order()
        self._update_widgets()
        self._product_table = Product.getAdapterClass(ISellable)

    def _clear_order(self):
        self.sellables.clear()
        for widget in (self.search_box, self.order_details_hbox,
                       self.list_vbox, self.CancelOrder):
            widget.set_sensitive(False)
        self.ResetOrder.set_sensitive(True)
        self.sale = None
        self.order_proxy.set_model(None, relax_type=True)
        self.product.grab_focus()
        self._update_widgets()

    def _delete_sellable_item(self, item):
        self.sellables.remove(item)
        if isinstance(item, ServiceSellableItem):
            delivery = IDelivery(item, connection=self.conn)
            if delivery:
                delivery.remove_items(delivery.get_items())
                table = type(delivery)
                table.delete(delivery.id, connection=self.conn)
        table = type(item)
        table.delete(item.id, connection=self.conn)

    def _set_product_on_sale(self):
        sellable = self._get_sellable()
        # If the sellable has a weight unit specified and we have a scale
        # configured for this station, go and check out what the printer says.
        if (sellable and sellable.unit and sellable.unit.index == UNIT_WEIGHT
            and get_current_scale_settings(self.conn)):
            self._read_scale()

    def _setup_proxies(self):
        self.order_proxy = self.add_proxy(widgets=POSApp.order_widgets)
        model = FancySellable(quantity=decimal.Decimal('1.0'),
                              price=currency(0))
        self.sellable_proxy = self.add_proxy(model,
                                             widgets=POSApp.sellable_widgets)
        self.price_slave.set_model(model)
        self.product_proxy = self.add_proxy(Settable(product=None),
                                            POSApp.product_widgets)

    def _setup_sellables(self):
        # TODO Waiting for improvements in kiwi entry completion. We need a
        # better way to query strings immediately when typing in the
        # entry
        # Force synchronization here. This is not a problem since the sale
        # instance will not be available until we finish the sale through
        # SaleWizard.
        self.conn.commit()
        sellables = AbstractSellable.get_available_sellables(self.conn)
        sellables = sellables[:self.max_results]
        items = [(s.get_short_description(), s) for s in sellables]
        # XXX Waiting for a bug fix in kiwi comboentry, we can not search by
        # description on the combo
        self.product.prefill(items)

    def _setup_widgets(self):
        can_edit = sysparam(self.conn).EDIT_SELLABLE_PRICE
        self.price_slave = PriceSlave(can_edit=can_edit)
        self.attach_slave("price_holder", self.price_slave)
        if can_edit:
            widget = self.price_slave.get_widget()
            widget.connect("activate", self.on_price_activate)

        value_format = '<b>%s</b>'
        self.summary_label = SummaryLabel(klist=self.sellables,
                                          column='total',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)
        if not sysparam(self.conn).HAS_DELIVERY_MODE:
            self.delivery_button.hide()
        self._setup_sellables()
        self.sellable_unit_label.set_size("small")
        self.sellable_unit_label.set_bold(True)
        self.warning_label.set_size("small")
        self.warning_box.hide()

    def _update_totals(self, *args):
        self.summary_label.update_total()

    def _product_notify(self, msg):
        self.product.set_invalid(msg)

    def _coupon_add_item(self, sellable_item):
        if sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            return
        self.coupon.add_item(sellable_item)

    def _update_list(self, item, notify_on_entry=False):
        if not isinstance(item, SellableView):
            raise TypeError("The object me be of type SellableView, got %r "
                            "instead." % type(item))
        sellables = [s.sellable.id for s in self.sellables]
        if item.id in sellables:
            if notify_on_entry:
                msg = _("The item '%s' was already added to the order"
                        % item.description)
                self.product.set_invalid(msg)
            return
        else:
            sellable = AbstractSellable.get(item.id, connection=self.conn)
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
            barcode = self.product.get_text()
            table = AbstractSellable
            sellable = table.get_availables_by_barcode(self.conn, barcode,
                                                       self._product_notify)
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

        if isinstance(sellable, self._product_table):
            adapted = sellable.get_adapted()
            storable = IStorable(adapted, connection=self.conn)
            # XXX Probably we could get rid of this check using a view and
            # not allowing products without stocks for a certain branch in
            # the pos item list. Waiting for bug 2339
            if not storable.has_stock_by_branch(self.sale.get_till_branch()):
                msg = _("There is no stock of this product in this branch, "
                        "please, select another item.")
                warning(_("Can not sell this product"), long=msg,
                        parent=self.get_toplevel())
                return
        item = SellableView.get(sellable.id, connection=self.conn)
        self._update_list(item, notify_on_entry=True)
        self._setup_sellables()
        self.warning_box.hide()
        self.product.grab_focus()

    def select_first_item(self):
        if len(self.sellables):
            # XXX Probably kiwi should handle this for us. Waiting for
            # support
            self.sellables.select(self.sellables[0])

    def _new_order(self):
        if self.coupon is not None:
            self._cancel_order()
        rollback_and_begin(self.conn)
        self.sale = self.run_dialog(NewOrderEditor, self.conn)
        if self.sale:
            self.sellables.clear()
            self.order_proxy.set_model(self.sale)
            self._update_widgets()
            self._update_totals()
            for widget in (self.search_box, self.order_details_hbox,
                           self.list_vbox, self.footer_hbox,
                           self.CancelOrder):
                widget.set_sensitive(True)
            self.ResetOrder.set_sensitive(False)
            self.product.grab_focus()
        else:
            rollback_and_begin(self.conn)
            return
        if sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            return
        self.coupon = FiscalCoupon(self.conn, self.sale)
        if self.sale.client:
            self.coupon.identify_customer(self.sale.client.get_adapted())
        while not self.coupon.open():
            if warning(
                _("It is not possible open a fiscal coupon"),
                _("It is not possible to start a new sale if the "
                  "fiscal coupon cannot be opened."),
                buttons=((_("Cancel"), gtk.RESPONSE_CANCEL),
                         (_("Try Again"), gtk.RESPONSE_OK))) != gtk.RESPONSE_OK:
                self.app.shutdown()

    def _update_widgets(self):
        has_sellables = len(self.sellables) >= 1
        widgets = [self.checkout_button, self.remove_item_button,
                   self.PrintOrder]
        for widget in widgets:
            widget.set_sensitive(has_sellables)
        has_client = self.sale is not None and self.sale.client is not None
        self.EditClient.set_sensitive(has_client)
        self.ClientDetails.set_sensitive(has_client)
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
        if scale_price != 0 and current_price != scale_price:
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

    def _run_search_dialog(self, dialog_type, **kwargs):
        # Save the current state of order before calling a search dialog
        self.conn.commit()
        self.run_dialog(dialog_type, self.conn, **kwargs)

    def _cancel_order(self):
        if self.sale is not None:
            msg = _('The current order will be canceled, Confirm?')
            default=gtk.RESPONSE_YES
            if not messagedialog(gtk.MESSAGE_QUESTION, msg,
                                 parent=self.get_toplevel(),
                                 buttons=gtk.BUTTONS_YES_NO,
                                 default=default) == default:
                return
        self._clear_order()
        if not sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            self.coupon.cancel()

    #
    # AppWindow Hooks
    #

    def setup_focus(self):
        self.search_box.set_focus_chain([self.product, self.quantity,
                                         self.add_button])

    def get_columns(self):
        return [Column('sellable.code_str', title=_('Code'), sorted=True,
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

    #
    # Callbacks
    #

    def on_price_activate(self, *args):
        self.add_sellable_item()

    def on_edit_current_client_action_clicked(self, *args):
        if not (self.sale and self.sale.client):
            raise ValueError('You must have a client defined at this point')
        if run_person_role_dialog(ClientEditor, self, self.conn,
                                  self.sale.client):
            self.conn.commit()

    def on_client_details_action_clicked(self, *args):
        # Waiting for bug 2319
        pass

    #
    # Kiwi callbacks
    #


    def on_product__changed(self, *args):
        self.product.set_valid()
        self._set_product_on_sale()

    def on_advanced_search__clicked(self, *args):
        # Ouch!, commit now ? yes, because SearchDialog synchronizes self.conn
        # internally. Actually this is not a problem since our sale object
        # is not valid (_is_valid_model defaults to False) until we finish the
        # whole process trough SaleWizard.
        self.conn.commit()
        items = self.run_dialog(SellableSearch, self.conn)
        if not items:
            return
        for item in items:
            self._update_list(item)
        self.select_first_item()
        self._update_totals()

    def on_add_button__clicked(self, *args):
        self.add_sellable_item()

    def on_product__activate(self, *args):
        self._set_product_on_sale()
        self.quantity.grab_focus()

    def on_quantity__activate(self, *args):
        if sysparam(self.conn).EDIT_SELLABLE_PRICE:
            self.price_slave.get_widget().grab_focus()
        else:
            self.add_sellable_item()

    def on_sellables__selection_changed(self, *args):
        self._update_widgets()

    def after_product__changed(self, *args):
        self._update_widgets()
        sellable = self.product_proxy.model.product
        if not (sellable and self.product.get_text()):
            model = FancySellable(quantity=decimal.Decimal('1.0'),
                                  price=currency(0))
            self.sellable_proxy.set_model(model)
            self.price_slave.set_model(model)
            return
        sellable_item = FancySellable(price=sellable.get_price(),
                                      quantity=decimal.Decimal('1.0'),
                                      unit=sellable.unit)
        self.price_slave.set_model(sellable_item)
        self.sellable_proxy.set_model(sellable_item)

    def on_remove_item_button__clicked(self, *args):
        item = self.sellables.get_selected()
        if (not sysparam(self.conn).CONFIRM_SALES_ON_TILL
            and not self.coupon.remove_item(item)):
            return
        self._delete_sellable_item(item)
        self.select_first_item()
        self._update_widgets()


    def _on_cancel_order_action_clicked(self, *args):
        self._cancel_order()

    def _on_resetorder_action__clicked(self, *args):
        self._new_order()

    def _on_clients_action__clicked(self, *args):
        self._run_search_dialog(ClientSearch, hide_footer=True)

    def _on_sales_action__clicked(self, *args):
        self._run_search_dialog(SaleSearch)

    def _on_products_action__clicked(self, *args):
        self._run_search_dialog(ProductSearch, hide_footer=True,
                                hide_toolbar=True, hide_cost_column=True)

    def _on_services_action__clicked(self, *args):
        self._run_search_dialog(ServiceSearch, hide_toolbar=True,
                                hide_cost_column=True)

    def _on_giftcertificates_action__clicked(self, *args):
        self._run_search_dialog(GiftCertificateSearch, hide_footer=True,
                                hide_toolbar=True)

    def on_delivery_button__clicked(self, *args):
        if not self.sellables:
            notify_dialog(_("You don't have products to delivery."),
                          _("Error"))
            return
        products = [obj for obj in self.sellables
                        if isinstance(obj, ProductSellableItem)
                           and not obj.has_been_totally_delivered()]
        if not products:
            notify_dialog(_("All the products already have delivery "
                            "instructions"), _("Error"))
            return

        # We must commit now since we would like to have some of the
        # instances created in self.conn in a new transaction
        self.conn.commit()
        conn = new_transaction()
        service = self.run_dialog(DeliveryEditor, conn, self.sale,
                                  products)
        if not finish_transaction(conn, service):
            return
        # Synchronize self.conn and bring the new delivery instances to it
        self.conn.commit()
        service = type(service).get(service.id, connection=self.conn)
        self.sellables.append(service)
        self.sellables.select(service)
        self._coupon_add_item(service)

    def _finish_coupon(self):
        totalize = self.coupon.totalize()
        has_payments = self.coupon.setup_payments()
        close = self.coupon.close()
        return totalize and has_payments and close

    def _sale_checkout(self, *args):
        param = sysparam(self.conn)
        skip_payment_step = (param.CONFIRM_SALES_ON_TILL and
                             param.SET_PAYMENT_METHODS_ON_TILL)
        if self.run_dialog(SaleWizard, self.conn, self.sale,
                           skip_payment_step=skip_payment_step):
            if not skip_payment_step and not param.CONFIRM_SALES_ON_TILL:
                if not self._finish_coupon():
                    return
            self.coupon = self.sale = None
            self.conn.commit()
            self._clear_order()

    def on_checkout_button__clicked(self, *args):
        self._sale_checkout()

    def on_new_order_button__clicked(self, *args):
        self._new_order()

    def _on_print_order_action__clicked(self, *args):
        self.print_report(SaleOrderReport, self.sale)
