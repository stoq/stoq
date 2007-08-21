# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Main interface definition for pos application.  """

import datetime
import gettext
from decimal import Decimal

import pango
import gtk
from kiwi.datatypes import currency, converter
from kiwi.argcheck import argcheck
from kiwi.log import Logger
from kiwi.python import Settable
from kiwi.ui.widgets.list import Column
from stoqdrivers.enum import UnitType
from stoqlib.database.runtime import (new_transaction,
                                      finish_transaction,
                                      get_current_user,
                                      get_current_branch)
from stoqlib.domain.interfaces import (IDelivery, IPaymentGroup, ISalesPerson,
                                       IProduct, IService)
from stoqlib.domain.devices import DeviceSettings
from stoqlib.domain.product import ProductAdaptToSellable, IStorable
from stoqlib.domain.person import PersonAdaptToClient
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.till import Till
from stoqlib.drivers.cheque import print_cheques_for_payment_group
from stoqlib.drivers.scale import read_scale_info
from stoqlib.exceptions import StoqlibError, TillError
from stoqlib.lib.message import info, yesno
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.parameters import sysparam
from stoqlib.gui.base.gtkadds import button_set_image_with_label
from stoqlib.gui.editors.serviceeditor import ServiceItemEditor
from stoqlib.gui.fiscalprinter import FiscalPrinterHelper
from stoqlib.gui.search.giftcertificatesearch import GiftCertificateSearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.salesearch import SaleSearch
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard

from stoq.gui.application import AppWindow
from stoq.gui.pos.deliveryeditor import DeliveryEditor

_ = gettext.gettext
log = Logger('stoq.pos')

class _SaleItem(object):
    def __init__(self, sellable, quantity, price=None):
        self.sellable = sellable
        self.description = sellable.base_sellable_info.description
        self.unit = sellable.get_unit_description()
        self.code = sellable.code
        self.quantity = quantity
        if not price:
            price = sellable.price
        self.price = price
        self.deliver = False
        self.estimated_fix_date = None
        self.notes = None

    @property
    def total(self):
        return currency(self.price * self.quantity)


class POSApp(AppWindow):

    app_name = _('Point of Sales')
    app_icon_name = 'stoq-pos-app'
    gladefile = "pos"
    klist_name = 'sale_items'

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self._delivery = None
        self.param = sysparam(self.conn)
        self.max_results = self.param.MAX_SEARCH_RESULTS
        self.client_table = PersonAdaptToClient
        self._product_table = ProductAdaptToSellable
        self._coupon = None
        self._printer = FiscalPrinterHelper(
            self.conn, parent=self.get_toplevel())
        self._scale_settings = DeviceSettings.get_scale_settings(self.conn)
        self._check_till()
        self._setup_widgets()
        self._setup_proxies()
        self._clear_order()
        self._update_widgets()

    #
    # AppWindow Hooks
    #

    def setup_focus(self):
        # Setting up the widget groups
        self.main_vbox.set_focus_chain([self.pos_vbox])

        self.pos_vbox.set_focus_chain([self.list_header_hbox, self.list_vbox])
        self.list_vbox.set_focus_chain([self.footer_hbox])
        self.footer_hbox.set_focus_chain([self.toolbar_vbox])

        # Setting up the toolbar area
        self.toolbar_vbox.set_focus_chain([self.toolbar_button_box])
        self.toolbar_button_box.set_focus_chain([self.remove_item_button,
                                                 self.delivery_button,
                                                 self.checkout_button])

        # Setting up the barcode area
        self.list_header_hbox.set_focus_chain([self.search_box,
                                               self.stoq_logo])
        self.item_hbox.set_focus_chain([self.barcode, self.quantity,
                                        self.item_button_box])
        self.item_button_box.set_focus_chain([self.barcode, self.quantity,
                                              self.add_button,
                                              self.advanced_search])

    def get_columns(self):
        return [Column('code', title=_('Reference'),
                       data_type=int, width=95, justify=gtk.JUSTIFY_RIGHT,
                       format='%05d'),
                Column('description',
                       title=_('Description'), data_type=str, expand=True,
                       searchable=True, ellipsize=pango.ELLIPSIZE_END),
                Column('price', title=_('Price'), data_type=currency,
                       width=110, justify=gtk.JUSTIFY_RIGHT),
                Column('quantity', title=_('Quantity'), data_type=Decimal,
                       width=110, format_func=format_quantity,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('unit', title=_('Unit'),
                       data_type=str, width=70,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('total', title=_('Total'), data_type=currency,
                       justify=gtk.JUSTIFY_RIGHT, width=100)]

    #
    # Private
    #

    def _set_product_on_sale(self):
        sellable = self._get_sellable()
        # If the sellable has a weight unit specified and we have a scale
        # configured for this station, go and check out what the printer says.
        if (sellable and sellable.unit and
            sellable.unit.unit_index == UnitType.WEIGHT and
            self._scale_settings):
            self._read_scale()

    def _setup_proxies(self):
        self.sellableitem_proxy = self.add_proxy(
            Settable(quantity=Decimal(1)), ['quantity'])

    def _setup_widgets(self):
        if not self.param.HAS_DELIVERY_MODE:
            self.delivery_button.hide()
        if self.param.POS_FULL_SCREEN:
            self.get_toplevel().fullscreen()
        if self.param.POS_SEPARATE_CASHIER:
            for proxy in self.TillMenu.get_proxies():
                proxy.hide()
        if self.param.CONFIRM_SALES_ON_TILL:
            button_set_image_with_label(self.checkout_button,
                                        'confirm24px.png', _('Close'))

        self.order_total_label.set_size('xx-large')
        self.order_total_label.set_bold(True)

    def _update_totals(self):
        subtotal = currency(sum([item.total for item in self.sale_items]))
        text = _(u"Total: %s") % converter.as_string(currency, subtotal)
        self.order_total_label.set_text(text)

    def _update_added_item(self, sale_item, new_item=True):
        """Insert or update a klist item according with the new_item
        argument
        """
        if new_item:
            if self._coupon_add_item(sale_item) == -1:
                return
            self.sale_items.append(sale_item)
        else:
            self.sale_items.update(sale_item)
        self.sale_items.select(sale_item)
        self.barcode.set_text('')
        self.barcode.grab_focus()
        self._reset_quantity_proxy()
        self._update_totals()

    @argcheck(ASellable, bool)
    def _update_list(self, sellable, notify_on_entry=False):
        quantity = self.sellableitem_proxy.model.quantity

        is_service = IService(sellable, None)
        if is_service and quantity > 1:
            # It's not a common operation to add more than one item at
            # a time, it's also problematic since you'd have to show
            # one dialog per service item. See #3092
            info(_(u"Only one service was added since its not possible to"
                   "add more than one service to an order at a time."))

        sale_item = _SaleItem(sellable=sellable,
                              quantity=quantity)
        if is_service:
            rv = self.run_dialog(ServiceItemEditor, self.conn, sale_item)
            if not rv:
                return
        self._update_added_item(sale_item)

    def _get_sellable(self):
        barcode = self.barcode.get_text()
        if not barcode:
            raise StoqlibError("_get_sellable needs a barcode")

        return ASellable.selectOneBy(barcode=barcode,
                                     status=ASellable.STATUS_AVAILABLE,
                                     connection=self.conn)

    def _select_first_item(self):
        if len(self.sale_items):
            # XXX Probably kiwi should handle this for us. Waiting for
            # support
            self.sale_items.select(self.sale_items[0])

    def _update_widgets(self):
        try:
            has_till = Till.get_current(self.conn) is not None
            till_close = has_till
            till_open = not has_till
        except TillError:
            has_till = False
            till_close = True
            till_open = False
        self.TillOpen.set_sensitive(till_open)
        self.TillClose.set_sensitive(till_close)
        self.barcode.set_sensitive(not till_open)
        self.quantity.set_sensitive(not till_open)
        self.sale_items.set_sensitive(not till_open)
        self.advanced_search.set_sensitive(not till_open)

        has_sale_items = len(self.sale_items) >= 1
        self.set_sensitive((self.checkout_button, self.remove_item_button,
                            self.PrintOrder, self.NewDelivery,
                            self.OrderCheckout), has_sale_items)
        self.CancelOrder.set_sensitive(has_sale_items)
        has_products = False
        for sale_item in self.sale_items:
            if sale_item and IProduct(sale_item.sellable, None):
                has_products = True
                break
        self.delivery_button.set_sensitive(has_products)
        self.NewDelivery.set_sensitive(has_sale_items)
        sale_item = self.sale_items.get_selected()
        can_edit = bool(
            sale_item is not None and
            IService(sale_item.sellable, None) and
            sale_item.sellable != sysparam(self.conn).DELIVERY_SERVICE)
        self.edit_item_button.set_sensitive(can_edit)
        if (len(self.sale_items) == 1 and
            self.sale_items[0].sellable == sysparam(self.conn).DELIVERY_SERVICE):
            self.set_sensitive((self.checkout_button,
                                self.OrderCheckout), False)
        self._update_totals()
        self._update_add_button()

    def _has_barcode_str(self):
        return self.barcode.get_text().strip() != ''

    def _update_add_button(self):
        has_barcode = self._has_barcode_str()
        self.add_button.set_sensitive(has_barcode)

    def _read_scale(self, sellable):
        data = read_scale_info(self.conn)
        self.quantity.set_value(data.weight)
        if self.param.USE_SCALE_PRICE:
            self.sellableitem_proxy.model.price = data.price_per_kg

    def _run_advanced_search(self, search_str=None):
        sellable_view_item = self.run_dialog(
            SellableSearch,
            self.conn,
            selection_mode=gtk.SELECTION_BROWSE,
            search_str=search_str,
            sale_items=self.sale_items,
            quantity=self.sellableitem_proxy.model.quantity,
            double_click_confirm=True)
        if not sellable_view_item:
            return

        sellable = ASellable.get(sellable_view_item.id, connection=self.conn)
        self._update_list(sellable)
        self.barcode.grab_focus()

    def _reset_quantity_proxy(self):
        self.sellableitem_proxy.model.quantity = Decimal(1)
        self.sellableitem_proxy.update('quantity')
        self.sellableitem_proxy.model.price = None

    #
    # Sale Order operations
    #

    def _add_sale_item(self, search_str=None):
        if not self.add_button.get_property('sensitive'):
            return
        sellable = self._get_sellable()
        self.add_button.set_sensitive(sellable is not None)
        if not sellable:
            self._run_advanced_search(search_str)
            return

        if IProduct(sellable, None):
            # If the sellable has a weight unit specified and we have a scale
            # configured for this station, go and check what the scale says.
            if (sellable and sellable.unit and
                sellable.unit.unit_index == UnitType.WEIGHT and
                self._scale_settings):
                self._read_scale(sellable)

        storable = IStorable(sellable, None)
        if storable:
            if not self._check_available_stock(storable, sellable):
                info(_("You cannot sell more items of product %s, "
                       "it's out of stock." % (sellable.get_description())))
                self.barcode.set_text('')
                self.barcode.grab_focus()
                return

        self._update_list(sellable, notify_on_entry=True)
        self.barcode.grab_focus()

    def _check_available_stock(self, storable, sellable):
        branch = get_current_branch(self.conn)
        available = storable.get_full_balance(branch)
        added = len([sale_item
                     for sale_item in self.sale_items
                         if sale_item.sellable == sellable])
        return available - added > 0

    def _clear_order(self):
        log.info("Clearing order")
        self.sale_items.clear()
        for widget in (self.search_box, self.list_vbox,
                       self.CancelOrder):
            widget.set_sensitive(True)
        self._coupon = None
        self._delivery = None

        self._reset_quantity_proxy()
        self.barcode.set_text('')
        self._update_widgets()

    def _cancel_coupon(self):
        log.info("Cancelling coupon")
        if not self.param.CONFIRM_SALES_ON_TILL:
            if self._coupon:
                self._coupon.cancel()
        self._coupon = None

    def _edit_sale_item(self, sale_item):
        if IService(sale_item.sellable, None):
            model = self.run_dialog(ServiceItemEditor, self.conn, sale_item)
            if model:
                self.sale_items.update(sale_item)
        else:
            # Do not raise any exception here, since this method can be called
            # when the user activate a row with product in the sellables list.
            return

    def _cancel_order(self):
        """
        Cancels the currently opened order.
        @returns: True if the order was canceled, otherwise false
        """
        if len(self.sale_items):
            if yesno(_(u'The current order will be canceled, Confirm?'),
                         gtk.RESPONSE_NO,_(u"Go Back"), _(u"Cancel Order")):
                return False

        self._cancel_coupon()
        self._clear_order()

        return True

    def _add_delivery(self):
        assert len(self.sale_items)

        delivery_service = sysparam(self.conn).DELIVERY_SERVICE
        sale_items = []
        delivery = None
        for sale_item in self.sale_items:
            if sale_item.sellable == delivery_service:
                delivery = self._delivery
            elif IService(sale_item.sellable, None):
                continue
            else:
                sale_items.append(sale_item)

        delivery = self.run_dialog(DeliveryEditor, self.conn,
                                   delivery,
                                   sale_items=sale_items)
        if delivery:
            self._add_delivery_item(delivery, delivery_service)
            self._delivery = delivery

    def _add_delivery_item(self, delivery, delivery_service):
        for sale_item in self.sale_items:
            if sale_item.sellable == delivery_service:
                sale_item.price = delivery.price
                delivery_item = sale_item
                new_item = False
                break
        else:
            delivery_item = _SaleItem(sellable=delivery_service,
                                      quantity=1,
                                      price=delivery.price)
            new_item = True

        self._update_added_item(delivery_item,
                                new_item=new_item)

    def _till_opened_previously(self):
        till = Till.get_last_opened(self.conn)
        if till:
            return till.opening_date.date() == datetime.date.today()
        else:
            return False

    def _check_till(self):
        if self._printer.needs_closing():
            if not self._close_till(self._till_opened_previously()):
                return False
        return True

    def _open_till(self):
         if self._printer.open_till():
             self._update_widgets()

    def _close_till(self, previous_day=False):
        retval = self._printer.close_till(previous_day)
        if retval:
            self._update_widgets()
        return retval

    def _create_sale(self, trans):
        user = get_current_user(trans)
        branch = get_current_branch(trans)
        salesperson = ISalesPerson(user.person)
        cfop = sysparam(trans).DEFAULT_SALES_CFOP
        sale = Sale(connection=trans,
                    branch=branch,
                    salesperson=salesperson,
                    cfop=cfop,
                    coupon_id=None)

        if self._delivery:
            address_string = self._delivery.address.get_address_string()
            sale.client = self._delivery.client

        for fake_sale_item in self.sale_items:
            sale_item = sale.add_sellable(fake_sale_item.sellable,
                                          price=fake_sale_item.price,
                                          quantity=fake_sale_item.quantity)
            sale_item.notes = fake_sale_item.notes
            sale_item.estimated_fix_date = fake_sale_item.estimated_fix_date

            if fake_sale_item.deliver:
                assert self._delivery
                item = sale_item.addFacet(IDelivery,
                                          connection=sale.get_connection())
                item.address = address_string

        return sale

    def _checkout(self):
        assert len(self.sale_items) >= 1

        trans = new_transaction()
        sale = self._create_sale(trans)
        if self.param.CONFIRM_SALES_ON_TILL:
            sale.order()
            trans.commit(close=True)
        else:
            ordered = self._confirm_order(trans, sale)
            if not finish_transaction(trans, ordered):
                trans.close()
                return

            log.info("Checking out")
            trans.close()

            # self.conn is infact a transaction, do a commit to bring
            # the objects from trans into self.conn
            self.conn.commit()
        self._clear_order()

    def _confirm_order(self, trans, sale):
        model = self.run_dialog(ConfirmSaleWizard, trans, sale)
        if not model:
            return False
        if sale.client:
            self._coupon.identify_customer(sale.client.person)

        if not self._coupon.totalize(sale):
            return False
        if not self._coupon.setup_payments(sale):
            return False
        if not self._coupon.close(sale):
            return False
        sale.confirm()

        if sale.paid_with_money():
            sale.set_paid()

        print_cheques_for_payment_group(trans, IPaymentGroup(sale))

        return True

    #
    # Coupon related
    #

    def _open_coupon(self):
        self._coupon = self._printer.create_coupon()
        while not self._coupon.open():
            if not yesno(_(u"It is not possible to start a new sale if the "
                           "fiscal coupon cannot be opened."),
                         gtk.RESPONSE_YES, _(u"Try Again"), _(u"Cancel")):
                self.app.shutdown()
                break

    def _coupon_add_item(self, sale_item):
        if self.param.CONFIRM_SALES_ON_TILL:
            return
        if self._coupon is None:
            self._open_coupon()
        return self._coupon.add_item(sale_item)

    def _coupon_remove_item(self, sale_item):
        if self.param.CONFIRM_SALES_ON_TILL:
            return

        self._coupon.remove_item(sale_item)

    #
    # Actions
    #

    def on_CancelOrder__activate(self, action):
        self._cancel_order()

    def on_Clients__activate(self, action):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    def on_Sales__activate(self, action):
        self.run_dialog(SaleSearch, self.conn)

    def on_ProductSearch__activate(self, action):
        self.run_dialog(ProductSearch, self.conn, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=True)

    def on_ServiceSearch__activate(self, action):
        self.run_dialog(ServiceSearch, self.conn, hide_toolbar=True,
                        hide_cost_column=True)

    def on_GiftCertificateSearch__activate(self, action):
        self.run_dialog(GiftCertificateSearch, self.conn, hide_footer=True,
                        hide_toolbar=True)

    def on_OrderCheckout__activate(self, action):
        self._checkout()

    def on_NewDelivery__activate(self, action):
        self._add_delivery()

    def on_TillClose__activate(self, action):
        if not yesno(_(u"You can only close the till once per day. "
                       "\n\nClose the till?"),
                     gtk.RESPONSE_NO, _(u"Not now"), _("Close Till")):
            self._close_till(self._till_opened_previously())

    def on_TillOpen__activate(self, action):
         self._open_till()

    #
    # Other callbacks
    #

    def on_advanced_search__clicked(self, button):
        self._run_advanced_search()

    def on_add_button__clicked(self, button):
        self._add_sale_item()

    def on_barcode__activate(self, entry):
        if not self._has_barcode_str():
            return
        search_str = self.barcode.get_text()
        self._add_sale_item(search_str)

    def after_barcode__changed(self, editable):
        self._update_add_button()

    def on_quantity__activate(self, entry):
        self._add_sale_item()

    def on_sale_items__selection_changed(self, sale_items, sale_item):
        self._update_widgets()

    def on_remove_item_button__clicked(self, button):
        sale_item = self.sale_items.get_selected()
        self._coupon_remove_item(sale_item)
        self.sale_items.remove(sale_item)
        self._select_first_item()
        self._update_widgets()

    def on_delivery_button__clicked(self, button):
        self._add_delivery()

    def on_checkout_button__clicked(self, button):
        self._checkout()

    def on_edit_item_button__clicked(self, button):
        item = self.sale_items.get_selected()
        if item is None:
            raise StoqlibError("You should have a item selected "
                               "at this point")
        self._edit_sale_item(item)

    def on_sale_items__row_activated(self, sale_items, sale_item):
        self._edit_sale_item(sale_item)

