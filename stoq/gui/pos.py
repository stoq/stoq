# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Main interface definition for pos application.  """

import gettext
from decimal import Decimal

import pango
import gtk
from kiwi.datatypes import currency, converter
from kiwi.argcheck import argcheck
from kiwi.datatypes import ValidationError
from kiwi.environ import environ
from kiwi.log import Logger
from kiwi.python import Settable
from kiwi.ui.widgets.list import Column
from kiwi.ui.widgets.contextmenu import ContextMenu, ContextMenuItem
from stoqdrivers.enum import UnitType
from stoqlib.api import api
from stoqlib.domain.interfaces import IDelivery, ISalesPerson
from stoqlib.domain.devices import DeviceSettings
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.product import IStorable
from stoqlib.domain.sale import Sale, DeliveryItem
from stoqlib.domain.sellable import Sellable
from stoqlib.drivers.scale import read_scale_info
from stoqlib.exceptions import StoqlibError, TaxError
from stoqlib.lib.barcode import parse_barcode, BarcodeInfo
from stoqlib.lib.defaults import quantize
from stoqlib.lib.message import warning, info, yesno, marker
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.gui.base.dialogs import push_fullscreen, pop_fullscreen
from stoqlib.gui.base.gtkadds import button_set_image_with_label
from stoqlib.gui.editors.deliveryeditor import DeliveryEditor
from stoqlib.gui.editors.serviceeditor import ServiceItemEditor
from stoqlib.gui.fiscalprinter import FiscalPrinterHelper
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.salesearch import (SaleSearch, DeliverySearch,
                                           SoldItemsByBranchSearch)
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.search.servicesearch import ServiceSearch

from stoq.gui.application import AppWindow

_ = gettext.gettext
log = Logger('stoq.pos')


class _SaleItem(object):
    def __init__(self, sellable, quantity, price=None, notes=None):
        # Use only 3 decimal places for the quantity
        self.quantity = Decimal('%.3f' % quantity)
        self.sellable = sellable
        self.description = sellable.description
        self.unit = sellable.get_unit_description()
        self.code = sellable.code

        if not price:
            price = sellable.price
        self.price = price
        self.deliver = False
        self.estimated_fix_date = None
        self.notes = notes

    @property
    def total(self):
        # Sale items are suposed to have only 2 digits, but the value price
        # * quantity may have more than 2, so we need to round it.
        return quantize(currency(self.price * self.quantity))

    @property
    def quantity_unit(self):
        qtd_string = ''
        if (self.quantity * 100 % 100) == 0:
            qtd_string = '%.0f' % self.quantity
        else:
            qtd_string = '%s' % self.quantity.normalize()

        return '%s %s' % (qtd_string, self.unit)


LOGO_WIDTH = 91
LOGO_HEIGHT = 32


class PosApp(AppWindow):

    app_name = _('Point of Sales')
    gladefile = "pos"
    embedded = True

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self._delivery = None
        self.param = api.sysparam(self.conn)
        self.max_results = self.param.MAX_SEARCH_RESULTS
        self._coupon = None
        # Cant use self._coupon to verify if there is a sale, since
        # CONFIRM_SALES_ON_TILL doesnt create a coupon
        self._sale_started = False
        self._scale_settings = DeviceSettings.get_scale_settings(self.conn)

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.pos')
        actions = [
            # File
            ("TillOpen", None, _("Open Till..."),
             group.get('till_open')),
            ("TillClose", None, _("Close Till..."),
             group.get('till_close')),

            # Order
            ("OrderMenu", None, _("Order")),
            ('ConfirmOrder', None, _('Confirm...'),
             group.get('order_confirm')),
            ('CancelOrder', None, _('Cancel...'),
             group.get('order_cancel')),
            ('NewDelivery', None, _('Create delivery...'),
             group.get('order_create_delivery')),

            # Search
            ("Sales", None, _("Sales..."),
             group.get('search_sales')),
            ("SoldItemsByBranchSearch", None, _("Sold Items by Branch..."),
             group.get('search_sold_items')),
            ("Clients", None, _("Clients..."),
             group.get('search_clients')),
            ("ProductSearch", None, _("Products..."),
             group.get('search_products')),
            ("ServiceSearch", None, _("Services..."),
             group.get('search_services')),
            ("DeliverySearch", None, _("Deliveries..."),
             group.get('search_deliveries')),
        ]
        self.pos_ui = self.add_ui_actions('', actions,
                                          filename='pos.xml')
        self.set_help_section(_("POS help"), 'app-pos')

    def create_ui(self):
        self.sale_items.set_columns(self.get_columns())
        self.sale_items.set_selection_mode(gtk.SELECTION_BROWSE)
        # Setting up the widget groups
        self.main_vbox.set_focus_chain([self.pos_vbox])

        self.pos_vbox.set_focus_chain([self.list_header_hbox, self.list_vbox])
        self.list_vbox.set_focus_chain([self.footer_hbox])
        self.footer_hbox.set_focus_chain([self.toolbar_vbox])

        # Setting up the toolbar area
        self.toolbar_vbox.set_focus_chain([self.toolbar_button_box])
        self.toolbar_button_box.set_focus_chain([self.checkout_button,
                                                 self.delivery_button,
                                                 self.edit_item_button,
                                                 self.remove_item_button])

        # Setting up the barcode area
        self.item_hbox.set_focus_chain([self.barcode, self.quantity,
                                        self.item_button_box])
        self.item_button_box.set_focus_chain([self.add_button,
                                              self.advanced_search])
        self._setup_printer()
        self._setup_widgets()
        self._setup_proxies()
        self._clear_order()

    def activate(self, params):
        # Admin app doesn't have anything to print/export
        for widget in (self.app.launcher.Print, self.app.launcher.ExportCSV):
            widget.set_visible(False)

        # Hide toolbar specially for pos
        self.uimanager.get_widget('/toolbar').hide()
        self.uimanager.get_widget('/menubar/ViewMenu/ToggleToolbar').hide()

        self.check_open_inventory()
        self._update_parameter_widgets()
        self._update_widgets()
        # This is important to do after the other calls, since
        # it emits signals that disable UI which might otherwise
        # be enabled.
        self._printer.check_till()

    def deactivate(self):
        self.uimanager.remove_ui(self.pos_ui)

        # Re enable toolbar
        self.uimanager.get_widget('/toolbar').show()
        self.uimanager.get_widget('/menubar/ViewMenu/ToggleToolbar').show()

    def setup_focus(self):
        self.barcode.grab_focus()

    def can_change_application(self):
        # Block POS application if we are in the middle of a sale.
        can_change_application = not self._sale_started
        if not can_change_application:
            if yesno(_('You must finish the current sale before you change to '
                       'another application.'),
                     gtk.RESPONSE_NO, _("Cancel sale"), _("Finish sale")):
                self._cancel_order(show_confirmation=False)
                return True

        return can_change_application

    def can_close_application(self):
        can_close_application = not self._sale_started
        if not can_close_application:
            if yesno(_('You must finish or cancel the current sale before you '
                       'can close the POS application.'),
                     gtk.RESPONSE_NO, _("Cancel sale"), _("Finish sale")):
                self._cancel_order(show_confirmation=False)
                return True
        return can_close_application

    def get_columns(self):
        return [Column('code', title=_('Reference'),
                       data_type=str, width=130, justify=gtk.JUSTIFY_RIGHT),
                Column('description',
                       title=_('Description'), data_type=str, expand=True,
                       searchable=True, ellipsize=pango.ELLIPSIZE_END),
                Column('price', title=_('Price'), data_type=currency,
                       width=110, justify=gtk.JUSTIFY_RIGHT),
                Column('quantity_unit', title=_('Quantity'), data_type=unicode,
                       width=110, justify=gtk.JUSTIFY_RIGHT),
                Column('total', title=_('Total'), data_type=currency,
                       justify=gtk.JUSTIFY_RIGHT, width=100)]

    def set_open_inventory(self):
        self.set_sensitive(self._inventory_widgets, False)

    #
    # Private
    #

    def _setup_printer(self):
        self._printer = FiscalPrinterHelper(self.conn,
                                            parent=self)
        self._printer.connect('till-status-changed',
                              self._on_PrinterHelper__till_status_changed)
        self._printer.connect('ecf-changed',
                              self._on_PrinterHelper__ecf_changed)
        self._printer.setup_midnight_check()

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

    def _update_parameter_widgets(self):
        self.delivery_button.props.visible = self.param.HAS_DELIVERY_MODE

        window = self.get_toplevel()
        if self.param.POS_FULL_SCREEN:
            window.fullscreen()
            push_fullscreen(window)
        else:
            pop_fullscreen(window)
            window.unfullscreen()

        for widget in (self.TillOpen, self.TillClose):
            widget.set_visible(not self.param.POS_SEPARATE_CASHIER)

        if self.param.CONFIRM_SALES_ON_TILL:
            confirm_label = _("_Close")
        else:
            confirm_label = _("_Checkout")
        button_set_image_with_label(self.checkout_button,
                                    gtk.STOCK_APPLY, confirm_label)

    def _setup_widgets(self):
        self._inventory_widgets = [self.Sales, self.barcode, self.quantity,
                                   self.sale_items, self.advanced_search,
                                   self.checkout_button]
        self.register_sensitive_group(self._inventory_widgets,
                                      lambda: not self.has_open_inventory())

        logo_file = environ.find_resource('pixmaps', 'stoq_logo.svg')
        logo = gtk.gdk.pixbuf_new_from_file_at_size(logo_file, LOGO_WIDTH,
                                                    LOGO_HEIGHT)
        self.stoq_logo.set_from_pixbuf(logo)

        self.till_status_label.set_size('xx-large')
        self.till_status_label.set_bold(True)

        self.order_total_label.set_size('xx-large')
        self.order_total_label.set_bold(True)
        self._create_context_menu()

        self.quantity.set_digits(3)

    def _create_context_menu(self):
        menu = ContextMenu()

        item = ContextMenuItem(gtk.STOCK_ADD)
        item.connect('activate', self._on_context_add__activate)
        menu.append(item)

        item = ContextMenuItem(gtk.STOCK_REMOVE)
        item.connect('activate', self._on_context_remove__activate)
        item.connect('can-disable', self._on_context_remove__can_disable)
        menu.append(item)

        self.sale_items.set_context_menu(menu)
        menu.show_all()

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

    @argcheck(Sellable, bool)
    def _update_list(self, sellable, notify_on_entry=False):
        try:
            sellable.check_taxes_validity()
        except TaxError as strerr:
            # If the sellable icms taxes are not valid, we cannot sell it.
            warning(strerr)
            return

        quantity = self.sellableitem_proxy.model.quantity

        is_service = sellable.service
        if is_service and quantity > 1:
            # It's not a common operation to add more than one item at
            # a time, it's also problematic since you'd have to show
            # one dialog per service item. See #3092
            info(_("It's not possible to add more than one service "
                   "at a time to an order. So, only one was added."))

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

        fmt = api.sysparam(self.conn).SCALE_BARCODE_FORMAT

        # Check if this barcode is from a scale
        info = parse_barcode(barcode, fmt)
        if info:
            barcode = info.code
            weight = info.weight

        sellable = Sellable.selectOneBy(barcode=barcode,
                                        status=Sellable.STATUS_AVAILABLE,
                                        connection=self.conn)

        # If the barcode has the price information, we need to calculate the
        # corresponding weight.
        if info and sellable and info.mode == BarcodeInfo.MODE_PRICE:
            weight = info.price / sellable.price

        if info and sellable:
            self.quantity.set_value(weight)

        return sellable

    def _select_first_item(self):
        if len(self.sale_items):
            # XXX Probably kiwi should handle this for us. Waiting for
            # support
            self.sale_items.select(self.sale_items[0])

    def _set_sale_sensitive(self, value):
        # Enable/disable the part of the ui that is used for sales,
        # usually manipulated when printer information changes.
        widgets = [self.barcode, self.quantity, self.sale_items,
                   self.advanced_search]
        self.set_sensitive(widgets, value)

        if value:
            self.barcode.grab_focus()

    def _disable_printer_ui(self):
        self._set_sale_sensitive(False)

        # It's possible to do a Sangria from the Sale search,
        # disable it for now
        widgets = [self.TillOpen, self.TillClose, self.Sales]
        self.set_sensitive(widgets, False)

        text = _(u"POS operations requires a connected fiscal printer.")
        self.till_status_label.set_text(text)

    def _till_status_changed(self, closed, blocked):
        if closed:
            text = _(u"Till closed")
        elif blocked:
            text = _(u"Till blocked")
        else:
            text = _(u"Till open")
        self.till_status_label.set_text(text)

        self.set_sensitive([self.TillOpen], closed)
        self.set_sensitive([self.TillClose], not closed or blocked)

        self._set_sale_sensitive(not closed and not blocked)

    def _update_widgets(self):
        has_sale_items = len(self.sale_items) >= 1
        self.set_sensitive((self.checkout_button, self.remove_item_button,
                            self.NewDelivery,
                            self.ConfirmOrder), has_sale_items)
        # We can cancel an order whenever we have a coupon opened.
        self.set_sensitive([self.CancelOrder], self._sale_started)
        has_products = False
        has_services = False
        for sale_item in self.sale_items:
            if sale_item and sale_item.sellable.product:
                has_products = True
            if sale_item and sale_item.sellable.service:
                has_services = True
            if has_products and has_services:
                break
        self.set_sensitive([self.delivery_button], has_products)
        self.set_sensitive([self.NewDelivery], has_sale_items)
        sale_item = self.sale_items.get_selected()
        can_edit = bool(
            sale_item is not None and
            sale_item.sellable.service and
            sale_item.sellable.service != self.param.DELIVERY_SERVICE)
        self.set_sensitive([self.edit_item_button], can_edit)

        self.set_sensitive((self.checkout_button,
                            self.ConfirmOrder), has_products or has_services)
        self.till_status_box.props.visible = not self._sale_started
        self.sale_items.props.visible = self._sale_started

        self._update_totals()
        self._update_buttons()

    def _has_barcode_str(self):
        return self.barcode.get_text().strip() != ''

    def _update_buttons(self):
        has_barcode = self._has_barcode_str()
        has_quantity = self._read_quantity() > 0
        self.set_sensitive([self.add_button], has_barcode and has_quantity)
        self.set_sensitive([self.advanced_search], has_quantity)

    def _read_quantity(self):
        try:
            quantity = self.quantity.read()
        except ValidationError:
            quantity = 0

        return quantity

    def _read_scale(self, sellable):
        data = read_scale_info(self.conn)
        self.quantity.set_value(data.weight)

    def _run_advanced_search(self, search_str=None, message=None):
        sellable_view_item = self.run_dialog(
            SellableSearch,
            self.conn,
            selection_mode=gtk.SELECTION_BROWSE,
            search_str=search_str,
            sale_items=self.sale_items,
            quantity=self.sellableitem_proxy.model.quantity,
            double_click_confirm=True,
            info_message=message)
        if not sellable_view_item:
            self.barcode.grab_focus()
            return

        sellable = Sellable.get(sellable_view_item.id, connection=self.conn)
        self._update_list(sellable)
        self.barcode.grab_focus()

    def _reset_quantity_proxy(self):
        self.sellableitem_proxy.model.quantity = Decimal(1)
        self.sellableitem_proxy.update('quantity')
        self.sellableitem_proxy.model.price = None

    def _get_deliverable_items(self):
        """Returns a list of sale items which can be delivered"""
        return [item for item in self.sale_items
                        if item.sellable.product is not None]

    def _check_delivery_removed(self, sale_item):
        # If a delivery was removed, we need to remove all
        # the references to it eg self._delivery
        if sale_item.sellable == self.param.DELIVERY_SERVICE.sellable:
            self._delivery = None

    #
    # Sale Order operations
    #

    def _add_sale_item(self, search_str=None):
        quantity = self._read_quantity()
        if quantity == 0:
            return

        sellable = self._get_sellable()
        if not sellable:
            message = (_("The barcode '%s' does not exist. "
                         "Searching for a product instead...")
                       % self.barcode.get_text())
            self._run_advanced_search(search_str, message)
            return

        if not sellable.is_valid_quantity(quantity):
            warning(_(u"You cannot sell fractions of this product. "
                      u"The '%s' unit does not allow that") %
                      sellable.get_unit_description())
            return

        if sellable.product:
            # If the sellable has a weight unit specified and we have a scale
            # configured for this station, go and check what the scale says.
            if (sellable and sellable.unit and
                sellable.unit.unit_index == UnitType.WEIGHT and
                self._scale_settings):
                self._read_scale(sellable)

        storable = IStorable(sellable.product, None)
        if storable is not None:
            if not self._check_available_stock(storable, sellable):
                info(_("You cannot sell more items of product %s. "
                       "The available quantity is not enough." %
                        sellable.get_description()))
                self.barcode.set_text('')
                self.barcode.grab_focus()
                return

        self._update_list(sellable, notify_on_entry=True)
        self.barcode.grab_focus()

    def _check_available_stock(self, storable, sellable):
        branch = api.get_current_branch(self.conn)
        available = storable.get_full_balance(branch)
        added = sum([sale_item.quantity
                     for sale_item in self.sale_items
                         if sale_item.sellable == sellable])
        added += self.sellableitem_proxy.model.quantity
        return available - added >= 0

    def _clear_order(self):
        log.info("Clearing order")
        self._sale_started = False
        self.sale_items.clear()

        widgets = [self.search_box, self.list_vbox, self.CancelOrder]
        self.set_sensitive(widgets, True)

        self._delivery = None

        self._reset_quantity_proxy()
        self.barcode.set_text('')
        self._update_widgets()

    def _edit_sale_item(self, sale_item):
        if sale_item.sellable.service:
            delivery_service = self.param.DELIVERY_SERVICE
            if sale_item.sellable.service == delivery_service:
                self._edit_delivery()
                return
            model = self.run_dialog(ServiceItemEditor, self.conn, sale_item)
            if model:
                self.sale_items.update(sale_item)
        else:
            # Do not raise any exception here, since this method can be called
            # when the user activate a row with product in the sellables list.
            return

    def _cancel_order(self, show_confirmation=True):
        """
        Cancels the currently opened order.
        @returns: True if the order was canceled, otherwise false
        """
        if len(self.sale_items) and show_confirmation:
            if yesno(_("This will cancel the current order. Are you sure?"),
                     gtk.RESPONSE_NO, _("Don't cancel"), _(u"Cancel order")):
                return False

        log.info("Cancelling coupon")
        if not self.param.CONFIRM_SALES_ON_TILL:
            if self._coupon:
                self._coupon.cancel()
        self._coupon = None
        self._clear_order()

        return True

    def _create_delivery(self):
        delivery_sellable = self.param.DELIVERY_SERVICE.sellable
        if delivery_sellable in self.sale_items:
            self._delivery = delivery_sellable

        delivery = self._edit_delivery()
        if delivery:
            self._add_delivery_item(delivery, delivery_sellable)
            self._delivery = delivery

    def _edit_delivery(self):
        """Edits a delivery, but do not allow the price to be changed.
        If there's no delivery, create one.
        @returns: The delivery
        """
        #FIXME: Canceling the editor still saves the changes.
        return self.run_dialog(DeliveryEditor, self.conn,
                               self._delivery,
                               sale_items=self._get_deliverable_items())

    def _add_delivery_item(self, delivery, delivery_service):
        for sale_item in self.sale_items:
            if sale_item.sellable == delivery_service:
                sale_item.price = delivery.price
                sale_item.notes = delivery.notes
                delivery_item = sale_item
                new_item = False
                break
        else:
            delivery_item = _SaleItem(sellable=delivery_service,
                                      quantity=1,
                                      notes=delivery.notes,
                                      price=delivery.price)
            delivery_item.estimated_fix_date = delivery.estimated_fix_date
            new_item = True

        self._update_added_item(delivery_item,
                                new_item=new_item)

    def _create_sale(self, trans):
        user = api.get_current_user(trans)
        branch = api.get_current_branch(trans)
        salesperson = ISalesPerson(user.person)
        cfop = api.sysparam(trans).DEFAULT_SALES_CFOP
        group = PaymentGroup(connection=trans)
        sale = Sale(connection=trans,
                    branch=branch,
                    salesperson=salesperson,
                    group=group,
                    cfop=cfop,
                    coupon_id=None,
                    operation_nature=api.sysparam(trans).DEFAULT_OPERATION_NATURE)

        if self._delivery:
            address_string = self._delivery.address.get_address_string()
            sale.client = self._delivery.client

        for fake_sale_item in self.sale_items:
            sale_item = sale.add_sellable(fake_sale_item.sellable,
                                          price=fake_sale_item.price,
                                          quantity=fake_sale_item.quantity)
            sale_item.notes = fake_sale_item.notes
            sale_item.estimated_fix_date = fake_sale_item.estimated_fix_date

            if self._delivery and fake_sale_item.deliver:
                item = sale_item.addFacet(IDelivery,
                                          connection=trans)
                item.address = address_string
                DeliveryItem(sellable=fake_sale_item.sellable,
                             quantity=fake_sale_item.quantity,
                             delivery=item,
                             connection=trans)
        return sale

    def _checkout(self):
        assert len(self.sale_items) >= 1

        trans = api.new_transaction()
        sale = self._create_sale(trans)
        if self.param.CONFIRM_SALES_ON_TILL:
            sale.order()
            trans.commit(close=True)
        else:
            assert self._coupon

            ordered = self._coupon.confirm(sale, trans)
            if not api.finish_transaction(trans, ordered):
                # FIXME: Move to TEF plugin
                manager = get_plugin_manager()
                if manager.is_active('tef'):
                    self._cancel_order(show_confirmation=False)
                trans.close()
                return

            log.info("Checking out")
            trans.close()

            # self.conn is infact a transaction, do a commit to bring
            # the objects from trans into self.conn
            self.conn.commit()
        self._coupon = None
        self._clear_order()

    def _remove_selected_item(self):
        sale_item = self.sale_items.get_selected()
        self._coupon_remove_item(sale_item)
        self.sale_items.remove(sale_item)
        self._check_delivery_removed(sale_item)
        self._select_first_item()
        self._update_widgets()
        self.barcode.grab_focus()

    def _checkout_or_add_item(self):
        search_str = self.barcode.get_text()
        if search_str == '':
            if len(self.sale_items) >= 1:
                self._checkout()
        else:
            self._add_sale_item(search_str)

    #
    # Coupon related
    #

    def _open_coupon(self):
        coupon = self._printer.create_coupon()

        if coupon:
            while not coupon.open():
                if not yesno(
                    _("It is not possible to start a new sale if the "
                      "fiscal coupon cannot be opened."),
                    gtk.RESPONSE_YES, _("Try again"), _("Cancel sale")):
                    self.app.shutdown()
                    break

        return coupon

    def _coupon_add_item(self, sale_item):
        """Adds an item to the coupon.

        Should return -1 if the coupon was not added, but will return None if
        CONFIRM_SALES_ON_TILL is true

        See L{stoqlib.gui.fiscalprinter.FiscalCoupon} for more information
        """
        self._sale_started = True
        if self.param.CONFIRM_SALES_ON_TILL:
            return

        if self._coupon is None:
            coupon = self._open_coupon()
            if not coupon:
                return -1
            self._coupon = coupon

        return self._coupon.add_item(sale_item)

    def _coupon_remove_item(self, sale_item):
        if self.param.CONFIRM_SALES_ON_TILL:
            return

        assert self._coupon
        self._coupon.remove_item(sale_item)

    def _close_till(self):
        if self._sale_started:
            if not yesno(_('You must finish or cancel the current sale before '
                       'you can close the till.'),
                     gtk.RESPONSE_NO, _("Cancel sale"), _("Finish sale")):
                return
            self._cancel_order(show_confirmation=False)
        self._printer.close_till()

    #
    # Actions
    #

    def on_CancelOrder__activate(self, action):
        self._cancel_order()

    def on_Clients__activate(self, action):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    def on_Sales__activate(self, action):
        self.run_dialog(SaleSearch, self.conn)

    def on_SoldItemsByBranchSearch__activate(self, action):
        self.run_dialog(SoldItemsByBranchSearch, self.conn)

    def on_ProductSearch__activate(self, action):
        self.run_dialog(ProductSearch, self.conn, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=True)

    def on_ServiceSearch__activate(self, action):
        self.run_dialog(ServiceSearch, self.conn, hide_toolbar=True,
                        hide_cost_column=True)

    def on_DeliverySearch__activate(self, action):
        self.run_dialog(DeliverySearch, self.conn)

    def on_ConfirmOrder__activate(self, action):
        self._checkout()

    def on_NewDelivery__activate(self, action):
        self._create_delivery()

    def on_TillClose__activate(self, action):
        self._close_till()

    def on_TillOpen__activate(self, action):
        self._printer.open_till()

    #
    # Other callbacks
    #

    def _on_context_add__activate(self, menu_item):
        self._run_advanced_search()

    def _on_context_remove__activate(self, menu_item):
        self._remove_selected_item()

    def _on_context_remove__can_disable(self, menu_item):
        selected = self.sale_items.get_selected()
        if selected:
            return False

        return True

    def on_advanced_search__clicked(self, button):
        self._run_advanced_search()

    def on_add_button__clicked(self, button):
        self._add_sale_item()

    def on_barcode__activate(self, entry):
        marker("enter pressed")
        self._checkout_or_add_item()

    def after_barcode__changed(self, editable):
        self._update_buttons()

    def on_quantity__activate(self, entry):
        self._checkout_or_add_item()

    def on_quantity__validate(self, entry, value):
        self._update_buttons()
        if value == 0:
            return ValidationError(_("Quantity must be a positive number"))

    def on_sale_items__selection_changed(self, sale_items, sale_item):
        self._update_widgets()

    def on_remove_item_button__clicked(self, button):
        self._remove_selected_item()

    def on_delivery_button__clicked(self, button):
        self._create_delivery()

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

    def _on_PrinterHelper__till_status_changed(self, printer, closed, blocked):
        self._till_status_changed(closed, blocked)

    def _on_PrinterHelper__ecf_changed(self, printer, has_ecf):
        # If we have an ecf, let the other events decide what to disable.
        if has_ecf:
            return

        # We dont have an ecf. Disable till related operations
        self._disable_printer_ui()
