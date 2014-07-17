# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

import platform

import gtk
from kiwi.component import get_utility

from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
_user_bindings = {}

if platform.system() == 'Darwin':
    default_pref_shortcut = '<Primary>comma'
else:
    default_pref_shortcut = ''

_bindings = [
    # Common application shortcuts
    ('app.common.toggle_fullscreen', '<Primary>F11',
     _('Toggle fullscreen')),
    ('app.common.toggle_statusbar', '',
     _('Toggle statusbar')),
    ('app.common.toggle_toolbar', '',
     _('Toggle toolbar')),
    ('app.common.new_window', '<Primary>n',
     _('Create a new Window')),
    ('app.common.change_password', '',
     _('Change password')),
    ('app.common.sign_out', '',
     _('Sign out')),
    ('app.common.close_window', '<Primary>w',
     _('Close window')),
    ('app.common.print', '<Primary>p',
     _("Print"),),
    ('app.common.preferences', default_pref_shortcut,
     _("Show preferences")),
    ('app.common.quit', '<Primary>q',
     _("Quit the application")),
    ('app.common.help', 'F1',
     _('Show help')),
    ('app.common.help_contents', '<Primary>F1',
     _('Show help contents')),

    # Admin application
    ('app.admin.search_cost_centers', '',
     _("Search for cost centers")),
    ('app.admin.search_roles', '<Primary><Alt>o',
     _("Search for employee roles")),
    ('app.admin.search_employees', '<Primary><Alt>e',
     _("Search for employees")),
    ('app.admin.search_events', '',
     _("Search for events")),
    ('app.admin.search_cfop', '<Primary>o',
     _("Search for C.F.O.Ps")),
    ('app.admin.search_fiscalbook', '<Primary><alt>f',
     _("Search for fiscal books")),
    ('app.admin.search_profile', '<Primary><Alt>u',
     _("Search for user profiles")),
    ('app.admin.search_users', '<Primary>u',
     _("Search for users")),
    ('app.admin.search_branches', '<Primary>b',
     _("Search for company branches")),
    ('app.admin.search_computers', '<Primary><alt>h',
     _("Search for computers")),
    ('app.admin.config_devices', '<Primary>d',
     _("Configure devices")),
    ('app.admin.config_payment_methods', '<Primary>m',
     _("Configure payment methods")),
    ('app.admin.config_payment_categories', '<Primary>a',
     _("Configure payment categories")),
    ('app.admin.config_client_categories', '<Primary>x',
     _("Configure client categories")),
    ('app.admin.config_invoices', '<Primary>n',
     _("Configure invoices")),
    ('app.admin.config_invoice_printers', '<Primary>f',
     _("Configure invoice printers")),
    ('app.admin.config_sintegra', '',
     _("Configure sintegra")),
    ('app.admin.config_taxes', '<Primary>l',
     _("Configure tax classes")),
    ('app.admin.config_parameters', '<Primary>y',
     _("Configure parameters")),

    # Calendar application
    ('app.calendar.new_client_call', '',
     _("Register a new client call")),
    ('app.calendar.new_payable', '',
     _("Add a new account payable")),
    ('app.calendar.new_receivable', '',
     _("Add a new account receivable")),
    ('app.calendar.new_work_order', '',
     _("Add a new work order")),
    ('app.calendar.go_back', '',
     _("Go back")),
    ('app.calendar.go_forward', '',
     _("Go forward")),
    ('app.calendar.show_today', '',
     _("Show today")),

    # Financial application
    ('app.financial.configure_payment_methods', '',
     _("Configure payment methods")),
    ('app.financial.import', '<Primary>i',
     _("Import transactions")),
    ('app.financial.delete_account', '',
     _("Delete account")),
    ('app.financial.delete_transaction', '',
     _("Delete account transaction")),
    ('app.financial.new_account', '<Primary>a',
     _("Create a new account")),
    ('app.financial.new_store', '<Primary>t',
     _("Create a new account transaction")),
    ('app.financial.edit', '',
     _("Edit an account or account transaction")),

    # Inventory application
    ('app.inventory.new_inventory', '',
     _("Open a new inventory")),
    ('app.inventory.inventory_count', '<Primary>c',
     _("Count the selected inventory")),
    ('app.inventory.inventory_adjust', '<Primary>a',
     _("Adjust the selected inventory")),
    ('app.inventory.inventory_cancel', '',
     _("Cancel the selected inventory")),
    ('app.inventory.inventory_details', '',
     _("View details of the selected inventory")),
    ('app.inventory.inventory_print', '',
     _('Print the product listing for the selected inventory')),

    # Services application
    ('app.services.new_order', '<control>o',
     _("Create a new work order")),
    ('app.services.search_categories', '<control>c',
     _("Search for categories")),
    ('app.services.search_clients', '<Primary><Alt>c',
     _("Search for clients")),
    ('app.services.search_products', '<Primary>d',
     _("Search for products")),
    ('app.services.search_services', '<Primary>s',
     _("Search for services")),
    ('app.services.order_edit', '',
     _("Edit the selected work order")),
    ('app.services.order_cancel', '',
     _("Cancel the selected work order")),
    ('app.services.order_finish', '',
     _("Finish the selected work order")),
    ('app.services.order_details', '',
     _("Show details for the selected work order")),
    ('app.services.order_print_quote', '',
     _("Print a quote report of the selected order")),
    ('app.services.order_print_receipt', '',
     _("Print a receipt of the selected order")),

    # Payable application
    ('app.payable.add_payable', '',
     _("Create a new account payable")),
    ('app.payable.payment_flow_history', '<Primary>f',
     _('Show a report of payment expected to receive grouped by day')),
    ('app.payable.payment_details', '',
     _("Show details for the selected payment")),
    ('app.payable.payment_pay', '',
     _("Pay the selected payment")),
    ('app.payable.payment_edit', '',
     _("Edit the selected payment installments")),
    ('app.payable.payment_cancel', '',
     _("Cancel the selected payment")),
    ('app.payable.payment_set_not_paid', '',
     _("Mark the selected payment as not paid")),
    ('app.payable.payment_change_due_date', '',
     _("Change the selected payment due date")),
    ('app.payable.payment_comments', '',
     _("Add comments to the selected payment")),
    ('app.payable.payment_print_receipt', '<Primary>r',
     _("Print a receipt for the selected payment")),
    ('app.payable.search_payment_categories', '',
     _("Search for payment categories")),
    ('app.payable.search_bills', '',
     _("Search for paid bills")),

    # Pos application
    ('app.pos.new_trade', '<Primary>t',
     _("Start a new trade")),
    ('app.pos.till_open', '<Primary>F6',
     _("Open the till")),
    ('app.pos.till_close', '<Primary>F7',
     _("Close the till")),
    ('app.pos.till_verify', '<Primary>F8',
     _("Verify the till")),
    ('app.pos.order_confirm', '<Primary>F10',
     _("Confirm the current order")),
    ('app.pos.order_cancel', '<Primary><Alt>o',
     _("Cancel the current order")),
    ('app.pos.order_create_delivery', '<Primary>F5',
     _("Create a delivery for the current order")),
    ('app.pos.search_sales', '<Primary><Alt>a',
     _("Search for sales ")),
    ('app.pos.search_sold_items', '<Primary><Alt>a',
     _("Search for sold items")),
    ('app.pos.search_clients', '<Primary><Alt>c',
     _("Search for clients")),
    ('app.pos.search_products', '<Primary><Alt>p',
     _("Search for products")),
    ('app.pos.search_services', '<Primary><Alt>s',
     _("Search for services")),
    ('app.pos.search_deliveries', '<Primary><Alt>e',
     _("Search for deliveries")),
    ('app.pos.payment_receive', '',
     _("Receive payment")),
    ('app.pos.toggle_details_viewer', '',
     _("Toggle the details viewer")),
    # ecf till read memory: <Primary>F9
    # ecf till summarize: <Primary>F11
    # books search books: <Primary><Alt>B
    # books search publishers: <Primary><Alt>P

    # Production application
    ('app.production.new_production_order', '<Primary>o',
     _("Create a new production order")),
    ('app.production.new_production_quote', '<Primary>p',
     _("Create a new production quote")),
    ('app.production.production_details', '',
     _("Show details for the selected production")),
    ('app.production.production_start', '<Primary>t',
     _("Start the selected production")),
    ('app.production.production_edit', '',
     _("Edit the selected production")),
    ('app.production.search_production_products', '<Primary>d',
     _("Search for production products")),
    ('app.production.search_services', '<Primary>s',
     _("Search for services")),
    ('app.production.search_production_items', '<Primary>r',
     _("Search for production items")),
    ('app.production.search_production_history', '<Primary>h',
     _("Search for production history")),

    # Purchase application
    ('app.purchase.new_order', '<control>o',
     _("Create a new purchase order")),
    ('app.purchase.new_quote', '<control>e',
     _("Create a new purchase quote")),
    ('app.purchase.new_consignment', '',
     _("Create a new consignment")),
    ('app.purchase.new_product', '',
     _("Create a new product")),
    ('app.purchase.search_categories', '<Primary>c',
     _("Search for categories")),
    ('app.purchase.search_products', '<Primary>d',
     _("Search for products")),
    ('app.purchase.search_product_units', '<Primary>u',
     _("Search for product units")),
    ('app.purchase.search_product_manufacturers', '',
     _("Search for product manufacturers")),
    ('app.purchase.search_services', '<Primary>s',
     _("Search for services")),
    ('app.purchase.search_stock_items', '<Primary>i',
     _("Search for stock items")),
    ('app.purchase.search_closed_stock_items', '<Primary><Alt>c',
     _("Search for closed stock items")),
    ('app.purchase.search_suppliers', '<Primary>u',
     _("Search for suppliers")),
    ('app.purchase.search_transporters', '<Primary>t',
     _("Search for transporters")),
    ('app.purchase.search_quotes', '<Primary>e',
     _("Search for quotes")),
    ('app.purchase.search_purchased_items', '<Primary>p',
     _("Search for purchased items")),
    ('app.purchase.search_products_sold', '',
     _("Search for sold products")),
    ('app.purchase.search_prices', '',
     _("Search for prices")),
    ('app.purchase.search_consignment_items', '',
     _("Search for consignment items")),
    ('app.purchase.order_confirm', '',
     _("Confirm the selected purchase order")),
    ('app.purchase.order_cancel', '',
     _("Cancel the selected purchase order")),
    ('app.purchase.order_edit', '',
     _("Edit the selected purchase order")),
    ('app.purchase.order_details', '',
     _("Show details for the selected purchase order")),
    ('app.purchase.order_finish', '',
     _("Finish the selected purchase order")),
    # books search books: <Primary><Alt>B
    # books search publishers: <Primary><Alt>P

    # Receivable application
    ('app.receivable.add_receiving', '',
     _("Create a new account receivable")),
    ('app.receivable.payment_flow_history', '<Primary>f',
     _('Show a report of payment expected to receive grouped by day')),
    ('app.receivable.payment_details', '',
     _("Show details for the selected payment")),
    ('app.receivable.payment_receive', '',
     _("Receive the selected payment")),
    ('app.receivable.payment_cancel', '',
     _("Cancel the selected payment")),
    ('app.receivable.payment_set_not_paid', '',
     _("Mark the selected payment as not paid")),
    ('app.receivable.payment_change_due_date', '',
     _("Change the selected payment due date")),
    ('app.receivable.payment_renegotiate', '',
     _("Renegotiate the selected payment")),
    ('app.receivable.payment_edit_installments', '',
     _("Edit the selected payment installments")),
    ('app.receivable.payment_comments', '',
     _("Add comments to the selected payment")),
    ('app.receivable.payment_print_bill', '',
     _("Print a bill for the selected payment")),
    ('app.receivable.payment_print_receipt', '<Primary>r',
     _("Print a receipt for the selected payment")),
    ('app.receivable.search_payment_categories', '',
     _("Search for payment categories")),
    ('app.receivable.search_bills', '',
     _("Search for bills")),
    ('app.receivable.search_card_payments', '',
     _("Search for card payments")),

    # Sales application
    ('app.sales.search_sold_items_by_branch', '<Primary><Alt>a',
     _("Search for sold items by branch")),
    ('app.sales.search_sales_by_payment', '',
     _("Search for sales by payment method")),
    ('app.sales.search_salesperson_sales', '',
     _("Search for the total sales made by a salesperson")),
    ('app.sales.search_products', '<Primary><Alt>p',
     _("Search for products")),
    ('app.sales.search_services', '<Primary><Alt>s',
     _("Search for services")),
    ('app.sales.search_deliveries', '<Primary><Alt>e',
     _("Search for deliveries")),
    ('app.sales.search_clients', '<Primary><Alt>c',
     _("Search for clients")),
    ('app.sales.search_commissions', '<Primary><Alt>o',
     _("Search for commissions")),
    ('app.sales.search_loans', '',
     _("Search for loans")),
    ('app.sales.search_loan_items', '',
     _("Search for loan items")),
    ('app.sales.returned_sales', '',
     _("Search for returned sales")),
    ('app.sales.sale_cancel', '',
     _("Cancel the selected sale")),
    ('app.sales.sale_print_invoice', '',
     _("Print an invoice for the selected sale")),
    ('app.sales.sale_return', '',
     _("Return the selected sale")),
    ('app.sales.sale_edit', '',
     _("Edit the selected sale")),
    ('app.sales.sale_details', '',
     _("Show details for the selected sale")),
    ('app.sales.search_client_calls', '',
     _("Search for client calls")),
    ('app.sales.search_credit_check_history', '',
     _("Search for client credit check history")),
    ('app.sales.search_reserved_product', '',
     _("Search for Reserved Products")),
    ('app.sales.search_clients', '',
     _("Search for Reserved Products")),
    # books search books: <Primary><Alt>B
    # books search publishers: <Primary><Alt>P

    # Stock application
    ('app.stock.stock_decrease', '<Primary>m',
     _("Create a stock decrease")),
    ('app.stock.new_receiving', '<Primary>r',
     _("Create a new receiving")),
    ('app.stock.transfer_product', '<Primary>t',
     _("Create a new product transfer")),
    ('app.stock.search_receiving', '<Primary><Alt>u',
     _("Search for receivings")),
    ('app.stock.search_product_history', "<Primary><Alt>p",
     _("Search for product history")),
    ('app.stock.search_purchased_stock_items', '',
     _("Search for purchased stock items")),
    ('app.stock.search_stock_items', "<Primary><Alt>s",
     _("Search for stock items")),
    ('app.stock.search_brand_items', "",
     _("Search for brand items")),
    ('app.stock.search_brand_by_branch', "",
     _("Search for brand items by branch")),
    ('app.stock.search_batch_items', "",
     _("Search for Batch items")),
    ('app.stock.search_transfers', "<Primary><Alt>t",
     _("Search for transfers")),
    ('app.stock.search_closed_stock_items', "<Primary><Alt>c",
     _("Search for closed stock items")),
    ('app.stock.edit_product', '',
     _("Edit the selected product")),
    ('app.stock.history', '',
     _("Show the selected product history")),
    ('app.stock.toggle_picture_viewer', '<Primary><Alt>v',
     _("Toggle the picture viewer")),

    # Till application
    ('app.till.open_till', '<Primary>F6',
     _("Open the till")),
    ('app.till.close_till', '<Primary>F7',
     _("Close the till")),
    ('app.till.verify_till', '<Primary>F8',
     _("Verify the till")),
    ('app.till.search_clients', '<Primary><Alt>c',
     _("Search for clients")),
    ('app.till.search_sale', '<Primary><Alt>a',
     _("Search for sales")),
    ('app.till.search_sold_items_by_branch', '<Primary><Alt>d',
     _("Search for sold items by branch")),
    ('app.till.search_till_history', '<Primary><Alt>t',
     _("Search for till entry history")),
    ('app.till.search_fiscal_till_operations', '<Primary><Alt>f',
     _("Search for fiscal till operations")),
    ('app.till.search_closed_till', '',
     _("Search for all closed tills")),
    ('app.till.confirm_sale', '',
     _("Confirm the sale")),
    ('app.till.return_sale', '',
     _("Return the sale")),
    ('app.till.sale_details', '',
     _("Show details of the sale")),
    ('app.till.payment_receive', '',
     _("Receive payment")),
    ('app.till.daily_movement', '',
     _("Print daily movement report")),
    # ecf till read memory: <Primary>F9
    # ecf till summarize: <Primary>F11
]


class KeyBinding(object):
    def __init__(self, item):
        self.name = item[0]
        self.shortcut = _user_bindings.get(self.name, item[1])
        self.category = get_category_label(item[0])
        self.description = self._parse_description(item)

    def _parse_description(self, item):
        if len(item) > 2:
            return item[2]
        else:
            n = self.name.rsplit('.')[-1]
            n = n.replace('_', ' ')
            return n.capitalize()


class KeyBindingCategory(object):
    def __init__(self, name, label):
        self.name = name
        self.label = label


_pre_gtk_2_24_9 = gtk.gtk_version < (2, 24, 9)


class KeyBindingGroup(object):
    def __init__(self, bindings):
        self._bindings = bindings

    def get(self, name):
        if not name in self._bindings:
            raise AttributeError(name)
        binding = self._bindings[name]
        if _pre_gtk_2_24_9:
            binding = binding.replace('<Primary>', '<Control>')
        if platform.system() == 'Darwin':
            binding = binding.replace('<Alt>', '<Control>')
        return binding


def add_bindings(bindings):
    _bindings.extend(bindings)


def load_user_keybindings():
    from stoqlib.lib.settings import get_settings
    settings = get_settings()
    d = settings.get('shortcuts', {})
    for key, value in d.items():
        set_user_binding(key, value)


def set_user_binding(binding, value):
    _user_bindings[binding] = value


def remove_user_binding(binding):
    try:
        del _user_bindings[binding]
    except KeyError:
        pass


def remove_user_bindings():
    global _user_bindings
    _user_bindings = {}


def get_bindings(category=None):
    for binding in _bindings:
        if category is not None and not binding[0].startswith(category):
            continue
        yield KeyBinding(binding)


def get_category_label(name):
    if name.startswith('app.common'):
        return _("General")
    elif name.startswith('app'):
        app_name = name.split('.', 2)[1]
        app_list = get_utility(IApplicationDescriptions)
        for item in app_list.get_descriptions():
            if item[0] == app_name:
                return item[1]  # the label

    elif name.startswith('plugin'):
        return _('%s plugin') % (name.split('.', 2)[1], )
    else:
        raise AssertionError(name)


def get_binding_categories():
    categories = set()
    for binding in _bindings:
        name = binding[0]
        category = '.'.join(name.split('.', 2)[:2])
        categories.add((category, get_category_label(name)))

    for name, label in categories:
        yield KeyBindingCategory(name, label)


def get_accels(prefix=''):
    d = {}
    if prefix and not prefix.endswith('.'):
        prefix += '.'

    for item in _bindings:
        name = item[0]
        if not name.startswith(prefix):
            continue
        key = name[len(prefix):]
        d[key] = _user_bindings.get(name, item[1])
    return KeyBindingGroup(d)


def get_accel(accel_name):
    for item in _bindings:
        if item[0] == accel_name:
            return item[1]

    raise AttributeError(accel_name)
