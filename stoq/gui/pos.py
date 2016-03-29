# -*- Mode: Python; coding: utf-8 -*-
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

from decimal import Decimal
import logging

import pango
import gtk
from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.datatypes import converter, ValidationError
from kiwi.python import Settable
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.contextmenu import ContextMenu, ContextMenuItem
from storm.expr import And, Lower

from stoqdrivers.enum import UnitType
from stoqlib.api import api
from stoqlib.domain.devices import DeviceSettings
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.product import StorableBatch
from stoqlib.domain.sale import Sale, Delivery
from stoqlib.domain.sellable import Sellable
from stoqlib.drivers.scale import read_scale_info
from stoqlib.exceptions import StoqlibError, TaxError
from stoqlib.gui.events import POSConfirmSaleEvent, CloseLoanWizardFinishEvent
from stoqlib.lib.barcode import parse_barcode, BarcodeInfo
from stoqlib.lib.decorators import cached_property, public
from stoqlib.lib.defaults import quantize
from stoqlib.lib.formatters import (format_sellable_description,
                                    format_quantity, get_formatted_price)
from stoqlib.lib.message import warning, info, yesno, marker
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.gui.base.dialogs import push_fullscreen, pop_fullscreen
from stoqlib.gui.base.gtkadds import button_set_image_with_label
from stoqlib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoqlib.gui.dialogs.sellableimage import SellableImageViewer
from stoqlib.gui.editors.deliveryeditor import CreateDeliveryEditor
from stoqlib.gui.editors.serviceeditor import ServiceItemEditor
from stoqlib.gui.fiscalprinter import FiscalPrinterHelper
from stoqlib.gui.search.deliverysearch import DeliverySearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.salespersonsearch import SalesPersonSalesSearch
from stoqlib.gui.search.salesearch import (SaleWithToolbarSearch,
                                           SoldItemsByBranchSearch)
from stoqlib.gui.search.sellablesearch import SaleSellableSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.search.paymentreceivingsearch import PaymentReceivingSearch
from stoqlib.gui.search.workordersearch import WorkOrderFinishedSearch
from stoqlib.gui.utils.keybindings import get_accels
from stoqlib.gui.utils.logo import render_logo_pixbuf
from stoqlib.gui.wizards.loanwizard import CloseLoanWizard
from stoqlib.gui.wizards.salereturnwizard import SaleTradeWizard

from stoq.gui.shell.shellapp import ShellApp

log = logging.getLogger(__name__)


@public(since="1.5.0")
class TemporarySaleItem(object):
    def __init__(self, sellable, quantity, price=None,
                 notes=None, can_remove=True, quantity_decreased=0, batch=None,
                 parent_item=None):
        # Use only 3 decimal places for the quantity
        self.quantity = Decimal('%.3f' % quantity)
        self.quantity_decreased = quantity_decreased
        self.batch = batch
        self.sellable = sellable
        self.description = sellable.get_description()
        self.unit = sellable.unit_description
        self.code = sellable.code
        self.can_remove = can_remove

        if price is None:
            price = sellable.price
        self.base_price = sellable.base_price
        self.price = price
        self.deliver = False
        self.estimated_fix_date = None
        self.notes = notes
        self.parent_item = parent_item
        self.children_items = []

    @property
    def full_description(self):
        return format_sellable_description(self.sellable, self.batch)

    # FIXME: Single joins dont cache de value if its None, and we use that a lot
    # here. Add a cache until we fix SingleJoins to cache de value properly.
    @cached_property(ttl=0)
    def service(self):
        return self.sellable.service

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


class PosApp(ShellApp):

    app_title = _('Point of Sales')
    gladefile = "pos"

    def __init__(self, window, store=None):
        self._suggested_client = None
        self._current_store = None
        self._trade = None
        self._trade_infobar = None

        # The sellable and batch selected, in case the parameter
        # CONFIRM_QTY_ON_BARCODE_ACTIVATE is used.
        self._sellable = None
        self._batch = None

        ShellApp.__init__(self, window, store=store)

        self._delivery = None
        self._coupon = None
        # Cant use self._coupon to verify if there is a sale, since
        # CONFIRM_SALES_ON_TILL doesnt create a coupon
        self._sale_started = False
        self._scale_settings = DeviceSettings.get_scale_settings(self.store)

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.pos')
        actions = [
            # File
            ('NewTrade', None, _('Trade...'),
             group.get('new_trade')),
            ('PaymentReceive', None, _('Payment Receival...'),
             group.get('payment_receive')),
            ("TillOpen", None, _("Open Till..."),
             group.get('till_open')),
            ("TillClose", None, _("Close Till..."),
             group.get('till_close')),
            ("TillVerify", None, _("Verify Till..."),
             group.get('till_verify')),
            ("LoanClose", None, _("Close loan...")),
            ("WorkOrderClose", None, _("Close work order...")),

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
            ("SearchSalesPersonSales", None,
             _("Total sales made by salesperson..."), None,
             _("Search for sales by payment method")),
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

        toggle_actions = [
            ('DetailsViewer', None, _('Details viewer'),
             group.get('toggle_details_viewer')),
        ]
        self.add_ui_actions('', toggle_actions, 'ToggleActions', 'toggle')

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

    def activate(self, refresh=True):
        # Admin app doesn't have anything to print/export
        for widget in (self.window.Print, self.window.ExportSpreadSheet):
            widget.set_visible(False)

        # Hides or shows sellable description
        self._confirm_quantity = sysparam.get_bool('CONFIRM_QTY_ON_BARCODE_ACTIVATE')
        self.sellable_description.set_visible(self._confirm_quantity)

        # Hide toolbar specially for pos
        self.uimanager.get_widget('/toolbar').hide()
        self.uimanager.get_widget('/menubar/ViewMenu/ToggleToolbar').hide()

        self.check_open_inventory()
        self._update_parameter_widgets()
        self._update_widgets()
        # This is important to do after the other calls, since
        # it emits signals that disable UI which might otherwise
        # be enabled.
        self._printer.run_initial_checks()

        CloseLoanWizardFinishEvent.connect(self._on_CloseLoanWizardFinishEvent)

    def deactivate(self):
        api.user_settings.set('pos-show-details-viewer',
                              self.DetailsViewer.get_active())

        self.uimanager.remove_ui(self.pos_ui)

        # Re enable toolbar
        self.uimanager.get_widget('/toolbar').show()
        self.uimanager.get_widget('/menubar/ViewMenu/ToggleToolbar').show()

        # one PosApp is created everytime the pos is opened. If we dont
        # disconnect, the callback from this instance would still be called, but
        # its no longer valid.
        CloseLoanWizardFinishEvent.disconnect(self._on_CloseLoanWizardFinishEvent)

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
                Column('full_description',
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

    @public(since="1.5.0")
    def add_sale_item(self, item):
        """Add a TemporarySaleItem item to the sale.

        :param item: a `temporary item <TemporarySaleItem>` to add to the sale.
          If the caller wants to store extra information about the sold items,
          it can create a subclass of TemporarySaleItem and pass that class
          here. This information will propagate when <POSConfirmSaleEvent> is
          emitted.
        """
        assert isinstance(item, TemporarySaleItem)
        self._update_added_item(item)

    #
    # Private
    #

    def _setup_printer(self):
        self._printer = FiscalPrinterHelper(self.store,
                                            parent=self)
        self._printer.connect('till-status-changed',
                              self._on_PrinterHelper__till_status_changed)
        self._printer.connect('ecf-changed',
                              self._on_PrinterHelper__ecf_changed)
        self._printer.setup_midnight_check()

    def _setup_proxies(self):
        self.sellableitem_proxy = self.add_proxy(
            Settable(quantity=Decimal(1)), ['quantity'])

    def _update_parameter_widgets(self):
        self.delivery_button.props.visible = sysparam.get_bool('HAS_DELIVERY_MODE')

        window = self.get_toplevel()
        if sysparam.get_bool('POS_FULL_SCREEN'):
            window.fullscreen()
            push_fullscreen(window)
        else:
            pop_fullscreen(window)
            window.unfullscreen()

        for widget in [self.TillOpen, self.TillClose, self.TillVerify]:
            widget.set_visible(not sysparam.get_bool('POS_SEPARATE_CASHIER'))

        if sysparam.get_bool('CONFIRM_SALES_ON_TILL'):
            confirm_label = _("_Close")
        else:
            confirm_label = _("_Checkout")
        button_set_image_with_label(self.checkout_button,
                                    gtk.STOCK_APPLY, confirm_label)

    def _setup_widgets(self):
        self._inventory_widgets = [self.barcode, self.quantity,
                                   self.sale_items, self.advanced_search,
                                   self.checkout_button, self.NewTrade,
                                   self.LoanClose, self.WorkOrderClose]
        self.register_sensitive_group(self._inventory_widgets,
                                      lambda: not self.has_open_inventory())

        self.stoq_logo.set_from_pixbuf(render_logo_pixbuf('pos'))

        self.order_total_label.set_size('xx-large')
        self.order_total_label.set_bold(True)
        self._create_context_menu()

        self.quantity.set_digits(3)

        self._image_slave = SellableImageViewer(size=(175, 175))
        self.attach_slave('image_holder', self._image_slave)
        self.details_lbl.set_ellipsize(pango.ELLIPSIZE_END)
        self.extra_details_lbl.set_ellipsize(pango.ELLIPSIZE_END)

        self.details_box.set_visible(False)
        self.DetailsViewer.set_active(
            api.user_settings.get('pos-show-details-viewer', True))

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
        subtotal = self._get_subtotal()
        text = _(u"Total: %s") % converter.as_string(currency, subtotal)
        self.order_total_label.set_text(text)

    def _update_added_item(self, sale_item, new_item=True):
        """Insert or update a klist item according with the new_item
        argument
        """
        if new_item:
            if self._coupon_add_item(sale_item) == -1:
                return
            self.sale_items.append(sale_item.parent_item, sale_item)
        else:
            self.sale_items.update(sale_item)
        self.sale_items.select(sale_item)
        # Reset all the widgets for adding a new sellable.
        self.barcode.set_text('')
        self.barcode.grab_focus()
        self._reset_quantity_proxy()
        self._update_totals()
        self._sellable = None
        self._batch = None
        if self._confirm_quantity:
            self.sellable_description.set_text('')

    def _update_list(self, sellable, batch=None):
        assert isinstance(sellable, Sellable)
        try:
            sellable.check_taxes_validity()
        except TaxError as strerr:
            # If the sellable icms taxes are not valid, we cannot sell it.
            warning(str(strerr))
            return

        quantity = self.sellableitem_proxy.model.quantity
        if sellable.product:
            self._add_product_sellable(sellable, quantity, batch=batch)
        elif sellable.service:
            self._add_service_sellable(sellable, quantity)

    def _add_service_sellable(self, sellable, quantity):
        sale_item = TemporarySaleItem(sellable=sellable,
                                      quantity=quantity)
        with api.new_store() as store:
            rv = self.run_dialog(ServiceItemEditor, store, sale_item)

        if not rv:
            return

        self._update_added_item(sale_item)

    def _add_product_sellable(self, sellable, quantity, batch=None):
        product = sellable.product
        if product.storable and not batch and product.storable.is_batch:
            available_batches = list(product.storable.get_available_batches(
                api.get_current_branch(self.store)))
            # The trivial case, where there's just one batch, use it directly
            if len(available_batches) == 1:
                batch = available_batches[0]
                sale_item = TemporarySaleItem(sellable=sellable,
                                              quantity=quantity,
                                              batch=batch)
                self._update_added_item(sale_item)
                return

            rv = self.run_dialog(BatchDecreaseSelectionDialog, self.store,
                                 model=sellable.product_storable,
                                 quantity=quantity)
            if not rv:
                return

            for batch, b_quantity in rv.items():
                sale_item = TemporarySaleItem(sellable=sellable,
                                              quantity=b_quantity,
                                              batch=batch)
                self._update_added_item(sale_item)
        else:
            sale_item = TemporarySaleItem(sellable=sellable,
                                          quantity=quantity,
                                          batch=batch)
            self._update_added_item(sale_item)

        # Making sure we are just adding the children if its a package
        if not sale_item.sellable.product.is_package:
            return
        for child in sale_item.sellable.product.get_components():
            child_quantity = child.quantity * quantity
            temp_child = TemporarySaleItem(sellable=child.component.sellable,
                                           quantity=child_quantity,
                                           price=Decimal('0'),
                                           parent_item=sale_item)
            sale_item.children_items.append(temp_child)
            self._update_added_item(temp_child)

    def _get_subtotal(self):
        return currency(sum([item.total for item in self.sale_items]))

    def _get_sellable_and_batch(self):
        text = self.barcode.get_text()

        # There is already a sellable selected and codebar not changed.
        # Return it instead.
        if self._sellable and not text:
            return self._sellable, self._batch

        if not text:
            raise StoqlibError("_get_sellable_and_batch needs a barcode")
        text = unicode(text)

        fmt = api.sysparam.get_int('SCALE_BARCODE_FORMAT')

        # Check if this barcode is from a scale
        barinfo = parse_barcode(text, fmt)
        if barinfo:
            text = barinfo.code
            weight = barinfo.weight

        batch = None
        query = Sellable.status == Sellable.STATUS_AVAILABLE

        # FIXME: Put this logic for getting the sellable based on
        # barcode/code/batch_number on domain. Note that something very
        # simular is done on abstractwizard.py

        sellable = self.store.find(
            Sellable, And(query, Lower(Sellable.barcode) == text.lower())).one()

        # If the barcode didnt match, maybe the user typed the product code
        if not sellable:
            sellable = self.store.find(
                Sellable, And(query, Lower(Sellable.code) == text.lower())).one()

        # If none of the above found, try to get the batch number
        if not sellable:
            query = Lower(StorableBatch.batch_number) == text.lower()
            batch = self.store.find(StorableBatch, query).one()
            if batch:
                sellable = batch.storable.product.sellable
                if not sellable.is_available:
                    # If the sellable is not available, reset both
                    sellable = None
                    batch = None

        # The user can't add the parent product of a grid directly to the sale.
        # TODO: Display a dialog to let the user choose an specific grid product.
        if sellable and sellable.product and sellable.product.is_grid:
            sellable = None

        # If the barcode has the price information, we need to calculate the
        # corresponding weight.
        if barinfo and sellable and barinfo.mode == BarcodeInfo.MODE_PRICE:
            weight = barinfo.price / sellable.price

        if barinfo and sellable:
            self.quantity.set_value(weight)

        return sellable, batch

    def _select_first_item(self):
        if len(self.sale_items):
            # XXX Probably kiwi should handle this for us. Waiting for
            # support
            self.sale_items.select(self.sale_items[0])

    def _set_sale_sensitive(self, value):
        # Enable/disable the part of the ui that is used for sales,
        # usually manipulated when printer information changes.
        widgets = [self.barcode, self.quantity, self.sale_items,
                   self.advanced_search, self.PaymentReceive]
        self.set_sensitive(widgets, value)

        if value:
            self.barcode.grab_focus()

    def _disable_printer_ui(self):
        self._set_sale_sensitive(False)

        widgets = [self.TillOpen, self.TillClose, self.TillVerify]
        self.set_sensitive(widgets, False)

        text = _(u"POS operations requires a connected fiscal printer.")
        self.till_status_label.set_text(text)

    def _till_status_changed(self, closed, blocked):
        def large(s):
            return '<span weight="bold" size="xx-large">%s</span>' % (
                api.escape(s), )

        if closed:
            text = large(_("Till closed"))
            if not blocked:
                text += '\n\n<span size="large"><a href="open-till">%s</a></span>' % (
                    api.escape(_('Open till')))
        elif blocked:
            text = large(_("Till blocked"))
        else:
            text = large(_("Till open"))
        self.till_status_label.set_use_markup(True)
        self.till_status_label.set_justify(gtk.JUSTIFY_CENTER)
        self.till_status_label.set_markup(text)

        self.set_sensitive([self.TillOpen], closed)
        self.set_sensitive([self.TillVerify, self.NewTrade,
                            self.LoanClose, self.WorkOrderClose],
                           not closed and not blocked)
        self.set_sensitive([self.TillClose],
                           not closed or blocked)

        self._set_sale_sensitive(not closed and not blocked)

    def _update_widgets(self):
        has_sale_items = len(self.sale_items) >= 1
        self.set_sensitive((self.checkout_button, self.remove_item_button,
                            self.NewDelivery,
                            self.ConfirmOrder), has_sale_items)
        # We can cancel an order whenever we have a coupon opened.
        self.set_sensitive([self.CancelOrder, self.DetailsViewer],
                           self._sale_started)
        has_products = False
        has_services = False
        for sale_item in self.sale_items:
            if sale_item and sale_item.sellable.product:
                has_products = True
            if sale_item and sale_item.service:
                has_services = True
            if has_products and has_services:
                break
        self.set_sensitive([self.delivery_button], has_products)
        self.set_sensitive([self.NewDelivery], has_sale_items)
        sale_item = self.sale_items.get_selected()

        if sale_item is not None and sale_item.service:
            # We are fetching DELIVERY_SERVICE into the sale_items' store
            # instead of the default store to avoid accidental commits.
            can_edit = not sysparam.compare_object('DELIVERY_SERVICE', sale_item.service)
        else:
            can_edit = False
        self.set_sensitive([self.edit_item_button], can_edit)
        can_remove = (sale_item is not None and sale_item.can_remove and
                      sale_item.parent_item is None)
        self.set_sensitive([self.remove_item_button], can_remove)

        self.set_sensitive((self.checkout_button,
                            self.ConfirmOrder), has_products or has_services)
        self.till_status_box.set_visible(not self._sale_started)
        self.sale_items_pane.set_visible(self._sale_started)

        self._update_totals()
        self._update_buttons()
        self._update_sellable_details()

    def _update_sellable_details(self):
        sale_item = self.sale_items.get_selected()
        sellable = sale_item and sale_item.sellable
        self._image_slave.set_sellable(sellable)

        if sale_item:
            markup = '<b>%s</b>\n%s x %s' % (
                api.escape(sale_item.description),
                api.escape(format_quantity(sale_item.quantity)),
                api.escape(get_formatted_price(sale_item.price)))

            if sellable.service:
                fix_date = (sale_item.estimated_fix_date.strftime('%x')
                            if sale_item.estimated_fix_date else '')
                extra_markup_parts = [
                    (_("Estimated fix date"), fix_date),
                    (_("Notes"), sale_item.notes)]
            elif sellable.product:
                product = sellable.product
                manufacturer = (product.manufacturer.name if
                                product.manufacturer else '')
                extra_markup_parts = [
                    (_("Manufacturer"), manufacturer),
                    (_("Brand"), product.brand),
                    (_("Family"), product.family),
                    (_("Model"), product.model),
                    (_("Width"), product.width or ''),
                    (_("Height"), product.height or ''),
                    (_("Depth"), product.depth or ''),
                    (_("Weight"), product.weight or '')]

            extra_markup = '\n'.join(
                '<b>%s</b>: %s' % (api.escape(label), api.escape(str(text)))
                for label, text in extra_markup_parts if text)
        else:
            markup = ''
            extra_markup = ''

        self.details_lbl.set_markup(markup)
        self.details_lbl.set_tooltip_markup(markup)

        self.extra_details_lbl.set_markup(extra_markup)
        self.extra_details_lbl.set_tooltip_markup(extra_markup)

    def _has_sellable(self):
        return bool(self.barcode.get_text().strip() != '' or self._sellable)

    def _update_buttons(self):
        has_quantity = self._read_quantity() > 0
        has_sellable = self._has_sellable()
        self.set_sensitive([self.add_button], has_sellable and has_quantity)
        self.set_sensitive([self.advanced_search], has_quantity)

    def _read_quantity(self):
        try:
            quantity = self.quantity.read()
        except ValidationError:
            quantity = 0

        return quantity

    def _read_scale(self, sellable):
        data = read_scale_info(self.store)
        self.quantity.set_value(data.weight)

    def _run_advanced_search(self, message=None, confirm_quantity=False):
        search_str = self.barcode.get_text()
        sellable_view_item = self.run_dialog(
            SaleSellableSearch,
            self.store,
            search_str=search_str,
            sale_items=self.sale_items,
            quantity=self.sellableitem_proxy.model.quantity,
            info_message=message)
        if not sellable_view_item:
            self.barcode.grab_focus()
            return

        sellable = sellable_view_item.sellable
        if confirm_quantity:
            self._set_selected_sellable(sellable)
            self.quantity.grab_focus()
        else:
            self._add_sellable(sellable)

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
        if (sale_item.sellable ==
                sysparam.get_object(self.store, 'DELIVERY_SERVICE').sellable):
            self._delivery = None

    #
    # Sale Order operations
    #

    def _add_sale_item(self, confirm_quantity):
        """Try to create a sale_item based on the barcode field.

        :param confirm_quantity: When True, instead of adding the sellable, we
          will move to the quantity field. Otherwise, we will just add the
          sellable.
        """
        sellable, batch = self._get_sellable_and_batch()
        if not sellable:
            message = (_("The barcode '%s' does not exist. "
                         "Searching for a product instead...")
                       % self.barcode.get_text())
            self._run_advanced_search(message, confirm_quantity)
            return

        if confirm_quantity:
            self._set_selected_sellable(sellable, batch)
            self.quantity.grab_focus()
        else:
            self._add_sellable(sellable, batch=batch)

            self._update_widgets()

    def _add_sellable(self, sellable, batch=None):
        quantity = self._read_quantity()
        if quantity == 0:
            return

        if not sellable.is_valid_quantity(quantity):
            warning(_(u"You cannot sell fractions of this product. "
                      u"The '%s' unit does not allow that") %
                    sellable.unit_description)
            return

        if sellable.product:
            # If the sellable has a weight unit specified and we have a scale
            # configured for this station, go and check what the scale says.
            if (sellable and sellable.unit and
                    sellable.unit.unit_index == UnitType.WEIGHT and
                    self._scale_settings):
                self._read_scale(sellable)

        storable = sellable.product_storable
        if storable is not None:
            if not self._check_available_stock(storable, sellable):
                info(_("You cannot sell more items of product %s. "
                       "The available quantity is not enough.") %
                     sellable.get_description())
                self.barcode.set_text('')
                self.barcode.grab_focus()
                return

        self._update_list(sellable, batch=batch)

    def _check_available_stock(self, storable, sellable):
        branch = api.get_current_branch(self.store)
        available = storable.get_balance_for_branch(branch)
        # Items that were already decreased should not be considered here
        added = sum([sale_item.quantity - sale_item.quantity_decreased
                     for sale_item in self.sale_items
                     # FIXME: We are using .id to workaround a problem when
                     # those sellables are not on the same store.
                     # See the fixme on self.checkout and fix this together
                     if sale_item.sellable.id == sellable.id])
        added += self.sellableitem_proxy.model.quantity
        return available - added >= 0

    def _clear_order(self):
        log.info("Clearing order")
        self._sale_started = False
        self.sale_items.clear()

        widgets = [self.search_box, self.list_vbox, self.CancelOrder,
                   self.PaymentReceive]
        self.set_sensitive(widgets, True)

        self._suggested_client = None
        self._delivery = None
        self._clear_trade()
        self._reset_quantity_proxy()
        self.barcode.set_text('')
        self._update_widgets()

        # store may already been closed on checkout
        if self._current_store and not self._current_store.obsolete:
            self._current_store.rollback(close=True)
        self._current_store = None

    def _clear_trade(self, remove=False):
        if self._trade and remove:
            self._trade.remove()
        self._trade = None
        self._remove_trade_infobar()

    def _edit_sale_item(self, sale_item):
        if sale_item.service:
            if sysparam.compare_object('DELIVERY_SERVICE', sale_item.service):
                self._edit_delivery()
                return
            with api.new_store() as store:
                model = self.run_dialog(ServiceItemEditor, store, sale_item)
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
        if not sysparam.get_bool('CONFIRM_SALES_ON_TILL'):
            if self._coupon:
                self._coupon.cancel()
        self._coupon = None
        self._clear_order()

        return True

    def _create_delivery(self):
        delivery_param = sysparam.get_object(self.store, 'DELIVERY_SERVICE')
        if delivery_param.sellable in self.sale_items:
            self._delivery = delivery_param.sellable

        delivery = self._edit_delivery()
        if delivery:
            self._add_delivery_item(delivery, delivery_param.sellable)
            self._delivery = delivery

    def _edit_delivery(self):
        """Edits a delivery, but do not allow the price to be changed.
        If there's no delivery, create one.
        @returns: The delivery
        """
        # FIXME: Canceling the editor still saves the changes.
        return self.run_dialog(CreateDeliveryEditor, self.store,
                               self._delivery,
                               sale_items=self._get_deliverable_items())

    def _add_delivery_item(self, delivery, delivery_sellable):
        for sale_item in self.sale_items:
            if sale_item.sellable == delivery_sellable:
                sale_item.price = delivery.price
                sale_item.notes = delivery.notes
                sale_item.estimated_fix_date = delivery.estimated_fix_date
                self._delivery_item = sale_item
                new_item = False
                break
        else:
            self._delivery_item = TemporarySaleItem(sellable=delivery_sellable,
                                                    quantity=1,
                                                    notes=delivery.notes,
                                                    price=delivery.price)
            self._delivery_item.estimated_fix_date = delivery.estimated_fix_date
            new_item = True

        self._update_added_item(self._delivery_item,
                                new_item=new_item)

    def _create_sale(self, store):
        user = api.get_current_user(store)
        branch = api.get_current_branch(store)
        salesperson = user.person.sales_person
        cfop_id = api.sysparam.get_object_id('DEFAULT_SALES_CFOP')
        nature = api.sysparam.get_string('DEFAULT_OPERATION_NATURE')
        group = PaymentGroup(store=store)
        sale = Sale(store=store,
                    branch=branch,
                    salesperson=salesperson,
                    group=group,
                    cfop_id=cfop_id,
                    coupon_id=None,
                    operation_nature=nature)

        if self._delivery:
            sale.client = store.fetch(self._delivery.client)
            sale.storeporter = store.fetch(self._delivery.transporter)
            delivery = Delivery(
                store=store,
                address=store.fetch(self._delivery.address),
                transporter=store.fetch(self._delivery.transporter),
            )
        else:
            delivery = None
            sale.client = self._suggested_client

        for fake_sale_item in self.sale_items:
            if fake_sale_item.parent_item:
                continue
            sale_item = sale.add_sellable(
                store.fetch(fake_sale_item.sellable),
                price=fake_sale_item.price, quantity=fake_sale_item.quantity,
                quantity_decreased=fake_sale_item.quantity_decreased,
                batch=store.fetch(fake_sale_item.batch))
            sale_item.notes = fake_sale_item.notes
            sale_item.estimated_fix_date = fake_sale_item.estimated_fix_date
            for child_fake in fake_sale_item.children_items:
                sale.add_sellable(store.fetch(child_fake.sellable),
                                  price=child_fake.price,
                                  quantity=child_fake.quantity,
                                  quantity_decreased=child_fake.quantity_decreased,
                                  batch=store.fetch(child_fake.batch),
                                  parent=sale_item)
            if delivery and fake_sale_item.deliver:
                delivery.add_item(sale_item)
            elif delivery and fake_sale_item == self._delivery_item:
                delivery.service_item = sale_item

        return sale

    def _set_selected_sellable(self, sellable, batch=None):
        """Saves the selected sellable for adding later.

        The user has selected a sellable, but he is still going to confirm
        the quantity. We should have what he has selected to add later.
        """
        self._sellable = sellable
        self._batch = batch
        self.sellable_description.set_text(sellable.description)
        self.barcode.set_text('')
        self._update_buttons()

    @public(since="1.5.0")
    def checkout(self, cancel_clear=False):
        """Initiates the sale wizard to confirm sale.

        :param cancel_clear: If cancel_clear is true, the sale will be cancelled
          if the checkout is cancelled.
        """
        assert len(self.sale_items) >= 1

        # FIXME: We should create self._current_store when adding the first
        # item, so we can simplify a lot of code on this module by using it
        # directly. The way it is now, most of the items will come from
        # self.store (so we need to fetch them to the store we define bellow)
        # and some from self._current_store (closed loan items, closed work
        # order items, etc)
        if self._current_store:
            store = self._current_store
            savepoint = 'before_run_fiscalprinter_confirm'
            store.savepoint(savepoint)
        else:
            store = api.new_store()
            savepoint = None

        if self._trade:
            subtotal = self._get_subtotal()
            returned_total = self._trade.returned_total
            if subtotal < returned_total:
                info(_("Traded value is greater than the new sale's value. "
                       "Please add more items or return it in Sales app, "
                       "then make a new sale"))
                return

            if (sysparam.get_bool('USE_TRADE_AS_DISCOUNT') and
                    subtotal == returned_total):
                info(_("Traded value is equal to the new sale's value. "
                       "Please add more items or return it in Sales app, "
                       "then make a new sale"))
                return

            sale = self._create_sale(store)
            self._trade.new_sale = sale
            self._trade.trade()
        else:
            sale = self._create_sale(store)

        if sysparam.get_bool('CONFIRM_SALES_ON_TILL'):
            sale.order()
            store.commit()
        else:
            assert self._coupon

            ordered = self._coupon.confirm(sale, store, savepoint,
                                           subtotal=self._get_subtotal())
            # Dont call store.confirm() here, since coupon.confirm()
            # above already did it
            if not ordered:
                # FIXME: Move to TEF plugin
                manager = get_plugin_manager()
                if (manager.is_active('tef') or cancel_clear or
                        self._coupon.cancelled):
                    self._cancel_order(show_confirmation=False)
                elif not self._current_store:
                    # Just do that if a store was created above and
                    # if _cancel_order wasn't called (it closes the connection)
                    store.rollback(close=True)
                return

            log.info("Checking out")

        self._coupon = None
        POSConfirmSaleEvent.emit(sale, self.sale_items[:])

        # We must close the connection only after the event is emmited, since it
        # may use value from the sale that will become invalid after it is
        # closed
        store.close()
        self._clear_order()

    def _remove_selected_item(self):
        sale_item = self.sale_items.get_selected()
        for child in sale_item.children_items:
            assert child.can_remove
            self._coupon_remove_item(child)
            self.sale_items.remove(child)
        assert sale_item.can_remove
        self._coupon_remove_item(sale_item)
        self.sale_items.remove(sale_item)
        self._check_delivery_removed(sale_item)
        self._select_first_item()
        self._update_widgets()
        self.barcode.grab_focus()

    def _checkout_or_add_item(self):
        # This is called when the user activates the barcode field.
        search_str = self.barcode.get_text()
        if search_str == '':
            # The user pressed enter with an empty string. Maybe start checkout
            checkout = True
            need_confirmation = sysparam.get_bool('CONFIRM_SALES_ON_TILL')
            if (need_confirmation and not
                    yesno(_('Close the order?'), gtk.RESPONSE_NO, _('Confirm'),
                          _("Don't confirm"))):
                checkout = False
            if len(self.sale_items) >= 1 and checkout:
                self.checkout()
        else:
            # The user typed something. Try to add the sellable.
            # In case there was an already selected sellable, we should reset
            # it, since the user may have changed what he is searching for.
            self._sellable = None
            self._batch = None
            self._add_sale_item(confirm_quantity=self._confirm_quantity)

    def _remove_trade_infobar(self):
        if not self._trade_infobar:
            return
        self._trade_infobar.destroy()
        self._trade_infobar = None

    def _show_trade_infobar(self, trade):
        self._remove_trade_infobar()
        if not trade:
            return

        button = gtk.Button(_("Cancel trade"))
        button.connect('clicked', self._on_remove_trade_button__clicked)
        value = converter.as_string(currency, self._trade.returned_total)
        msg = _("There is a trade with value %s in progress...\n"
                "When checking out, it will be used as part of "
                "the payment.") % (value, )
        self._trade_infobar = self.window.add_info_bar(
            gtk.MESSAGE_INFO, msg, action_widget=button)

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
                    return None

        self.set_sensitive([self.PaymentReceive], False)
        return coupon

    def _coupon_add_item(self, sale_item):
        """Adds an item to the coupon.

        Should return -1 if the coupon was not added, but will return None if
        CONFIRM_SALES_ON_TILL is true

        See :class:`stoqlib.gui.fiscalprinter.FiscalCoupon` for more information
        """
        self._sale_started = True
        if sysparam.get_bool('CONFIRM_SALES_ON_TILL'):
            return

        if self._coupon is None:
            coupon = self._open_coupon()
            if not coupon:
                return -1
            self._coupon = coupon

        return self._coupon.add_item(sale_item)

    def _coupon_remove_item(self, sale_item):
        if sysparam.get_bool('CONFIRM_SALES_ON_TILL'):
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
        self.run_dialog(ClientSearch, self.store, hide_footer=True)

    def on_Sales__activate(self, action):
        with api.new_store() as store:
            self.run_dialog(SaleWithToolbarSearch, store)

    def on_SearchSalesPersonSales__activate(self, action):
        self.run_dialog(SalesPersonSalesSearch, self.store)

    def on_SoldItemsByBranchSearch__activate(self, action):
        self.run_dialog(SoldItemsByBranchSearch, self.store)

    def on_ProductSearch__activate(self, action):
        self.run_dialog(ProductSearch, self.store, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=True)

    def on_ServiceSearch__activate(self, action):
        self.run_dialog(ServiceSearch, self.store, hide_toolbar=True,
                        hide_cost_column=True)

    def on_DeliverySearch__activate(self, action):
        self.run_dialog(DeliverySearch, self.store)

    def on_ConfirmOrder__activate(self, action):
        self.checkout()

    def on_NewDelivery__activate(self, action):
        self._create_delivery()

    def on_PaymentReceive__activate(self, action):
        self.run_dialog(PaymentReceivingSearch, self.store)

    def on_TillClose__activate(self, action):
        self._close_till()

    def on_TillOpen__activate(self, action):
        self._printer.open_till()

    def on_TillVerify__activate(self, action):
        self._printer.verify_till()

    def on_DetailsViewer__activate(self, button):
        self.details_box.set_visible(button.get_active())

    def on_LoanClose__activate(self, action):
        if self.check_open_inventory():
            return

        if self._current_store:
            store = self._current_store
            store.savepoint('before_run_wizard_closeloan')
        else:
            store = api.new_store()

        rv = self.run_dialog(CloseLoanWizard, store, create_sale=False,
                             require_sale_items=True)
        if rv:
            if self._suggested_client is None:
                # The loan close wizard lets to close more than one loan at
                # the same time (but only from the same client and branch)
                self._suggested_client = rv[0].client
            self._current_store = store
        elif self._current_store:
            store.rollback_to_savepoint('before_run_wizard_closeloan')
        else:
            store.rollback(close=True)

    def on_WorkOrderClose__activate(self, action):
        if self.check_open_inventory():
            return

        if self._current_store:
            store = self._current_store
            store.savepoint('before_run_search_workorder')
        else:
            store = api.new_store()

        rv = self.run_dialog(WorkOrderFinishedSearch, store,
                             double_click_confirm=True)
        if rv:
            work_order = rv.work_order
            for item in work_order.order_items:
                self.add_sale_item(
                    TemporarySaleItem(sellable=item.sellable,
                                      quantity=item.quantity,
                                      quantity_decreased=item.quantity_decreased,
                                      price=item.price,
                                      can_remove=False))
            work_order.close()
            if self._suggested_client is None:
                self._suggested_client = work_order.client
            self._current_store = store
        elif self._current_store:
            store.rollback_to_savepoint('before_run_search_workorder')
        else:
            store.rollback(close=True)

    def on_NewTrade__activate(self, action):
        if self._trade:
            if yesno(_("There is already a trade in progress... Do you "
                       "want to cancel it and start a new one?"),
                     gtk.RESPONSE_NO, _("Cancel trade"), _("Finish trade")):
                self._clear_trade(remove=True)
            else:
                return

        if self._current_store:
            store = self._current_store
            store.savepoint('before_run_wizard_saletrade')
        else:
            store = api.new_store()

        trade = self.run_dialog(SaleTradeWizard, store)
        if trade:
            self._trade = trade
            self._current_store = store
        elif self._current_store:
            store.rollback_to_savepoint('before_run_wizard_saletrade')
        else:
            store.rollback(close=True)

        self._show_trade_infobar(trade)

    #
    # Other callbacks
    #

    def _on_context_add__activate(self, menu_item):
        self._run_advanced_search(confirm_quantity=False)

    def _on_context_remove__activate(self, menu_item):
        self._remove_selected_item()

    def _on_context_remove__can_disable(self, menu_item):
        selected = self.sale_items.get_selected()
        if selected and selected.can_remove:
            return False

        return True

    def _on_remove_trade_button__clicked(self, button):
        if yesno(_("Do you really want to cancel the trade in progress?"),
                 gtk.RESPONSE_NO, _("Cancel trade"), _("Don't cancel")):
            self._clear_trade(remove=True)

    def on_till_status_label__activate_link(self, button, link):
        if link == 'open-till':
            self._printer.open_till()
        return True

    def on_advanced_search__clicked(self, button):
        self._run_advanced_search(confirm_quantity=self._confirm_quantity)

    def on_add_button__clicked(self, button):
        self._add_sale_item(confirm_quantity=False)

    def on_barcode__activate(self, entry):
        marker("enter pressed")
        self._checkout_or_add_item()

    def after_barcode__changed(self, editable):
        self._update_buttons()

    def on_quantity__activate(self, entry):
        # Before activate, check if 'quantity' widget is valid and if we have a
        # sellable selected
        has_sellable = self._has_sellable()
        if self.quantity.validate() is not ValueUnset and has_sellable:
            self._add_sale_item(confirm_quantity=False)

    def on_quantity__validate(self, entry, value):
        self._update_buttons()
        if value <= 0:
            return ValidationError(_("Quantity must be a positive number"))

    def on_sale_items__selection_changed(self, sale_items, sale_item):
        self._update_widgets()

    def on_remove_item_button__clicked(self, button):
        self._remove_selected_item()

    def on_delivery_button__clicked(self, button):
        self._create_delivery()

    def on_checkout_button__clicked(self, button):
        self.checkout()

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

    def _on_CloseLoanWizardFinishEvent(self, loans, sale, wizard):
        for item in wizard.get_sold_items():
            sellable, quantity, price = item
            self.add_sale_item(
                TemporarySaleItem(sellable=sellable, quantity=quantity,
                                  # Quantity was already decreased on loan
                                  quantity_decreased=quantity,
                                  price=price, can_remove=False))
