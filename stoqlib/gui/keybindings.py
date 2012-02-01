# -*- Mode: Python; coding: iso-8859-1 -*-
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

from kiwi.component import get_utility

from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

_user_bindings = {}

_bindings = [
    # Common application shortcuts
    ('app.common.toggle_fullscreen', '<Control>F11',
     _('Toggle fullscreen')),
    ('app.common.toggle_statusbar', '',
     _('Toggle statusbar')),
    ('app.common.toggle_toolbar', '',
     _('Toggle toolbar')),
    ('app.common.new_window', '<Control>n',
     _('Create a new Window')),
    ('app.common.change_password', '',
     _('Change password')),
    ('app.common.sign_out', '',
     _('Sign out')),
    ('app.common.close_window', '<Control>w',
     _('Close window')),
    ('app.common.print', '<Control>p',
     _("Print"),),
    ('app.common.quit', '<Control>q',
     _("Quit the application")),
    ('app.common.help', 'F1',
     _('Show help')),
    ('app.common.help_contents', '<Control>F1',
     _('Show help contents')),

    # Admin application
    ('app.admin.search_roles', '<Control><Alt>o',
     _("Search for employee roles")),
    ('app.admin.search_employees', '<Control><Alt>e',
     _("Search for employees")),
    ('app.admin.search_events', '',
     _("Search for events")),
    ('app.admin.search_cfop', '<Control>o',
     _("Search for C.F.O.Ps")),
    ('app.admin.search_fiscalbook', '<Control><alt>f',
     _("Search for fiscal books")),
    ('app.admin.search_profile', '<Control><Alt>u',
     _("Search for user profiles")),
    ('app.admin.search_users', '<Control>u',
     _("Search for users")),
    ('app.admin.search_branches', '<Control>b',
     _("Search for company branches")),
    ('app.admin.search_computers', '<Control><alt>h',
     _("Search for computers")),
    ('app.admin.config_devices', '<Control>d',
     _("Configure devices")),
    ('app.admin.config_payment_methods', '<Control>m',
     _("Configure payment methods")),
    ('app.admin.config_payment_categories', '<Control>a',
     _("Configure payment categories")),
    ('app.admin.config_client_categories', '<Control>x',
     _("Configure client categories")),
    ('app.admin.config_invoices', '<Control>n',
     _("Configure invoices")),
    ('app.admin.config_invoice_printers', '<Control>f',
     _("Configure invoice printers")),
    ('app.admin.config_sintegra', '<Control>w',
     _("Configure sintegra")),
    ('app.admin.config_taxes', '<Control>l',
     _("Configure tax classes")),
    ('app.admin.config_parameters', '<Control>y',
     _("Configure parameters")),

    # Calendar application
    ('app.calendar.new_client_call', '',
     _("Register a new client call")),
    ('app.calendar.new_payable', '',
     _("Add a new account payable")),
    ('app.calendar.new_receivable', '',
     _("Add a new account receivable")),
    ('app.calendar.go_back', '',
     _("Go back")),
    ('app.calendar.go_forward', '',
     _("Go forward")),
    ('app.calendar.show_today', '',
     _("Show today")),

    # Financial application
    ('app.financial.import', '<Control>i',
     _("Import transactions")),
    ('app.financial.delete_account', '',
     _("Delete account")),
    ('app.financial.delete_transaction', '',
     _("Delete account transaction")),
    ('app.financial.new_account', '<Control>a',
     _("Create a new account")),
    ('app.financial.new_transaction', '<Control>t',
     _("Create a new account transaction")),
    ('app.financial.edit', '',
     _("Edit an account or account transaction")),

    # Inventory application
    ('app.inventory.new_inventory', '',
     _("Open a new inventory")),
    ('app.inventory.inventory_count', '<Control>c',
     _("Count the selected inventory")),
    ('app.inventory.inventory_adjust', '<Control>a',
     _("Adjust the selected inventory")),
    ('app.inventory.inventory_cancel', '',
     _("Cancel the selected inventory")),
    ('app.inventory.inventory_print', '',
     _('Print the product listing for the selected inventory')),

    # Payable application
    ('app.payable.add_payable', '<Control>p',
     _("Create a new account payable")),
    ('app.payable.payment_flow_history', '<Control>f',
     _('Show a report of payment expected to receive grouped by day')),
    ('app.payable.payment_details', '',
     _("Show details for the selected payment")),
    ('app.payable.payment_pay', '',
     _("Pay the selected payment")),
    ('app.payable.payment_edit', '',
     _("Edit the selected payment")),
    ('app.payable.payment_cancel', '',
     _("Cancel the selected payment")),
    ('app.payable.payment_set_not_paid', '',
     _("Mark the selected payment as not paid")),
    ('app.payable.payment_change_due_date', '',
     _("Change the selected payment due date")),
    ('app.payable.payment_comments', '',
     _("Add comments to the selected payment")),
    ('app.payable.payment_print_receipt', '<Control>r',
     _("Print a receipt for the selected payment")),
    ('app.payable.search_bills', '',
     _("Search for paid bills")),

    # Pos application
    ('app.pos.till_open', '<Control>F6',
     _("Open the till")),
    ('app.pos.till_close', '<Control>F7',
     _("Close the till")),
    ('app.pos.order_confirm', '<Control>F10',
     _("Confirm the current order")),
    ('app.pos.order_cancel', '<Control><Alt>o',
     _("Cancel the current order")),
    ('app.pos.order_create_delivery', '<Control>F5',
     _("Create a delivery for the current order")),
    ('app.pos.search_sales', '<Control><Alt>a',
     _("Search for sales ")),
    ('app.pos.search_sold_items', '<Contrl><Alt>a',
     _("Search for sold items")),
    ('app.pos.search_clients', '<Control><Alt>c',
     _("Search for clients")),
    ('app.pos.search_products', '<Control><Alt>p',
     _("Search for products")),
    ('app.pos.search_services', '<Contro><Alt>s',
     _("Search for services")),
    ('app.pos.search_deliveries', '<Control><Alt>e',
     _("Search for deliveries")),
    # ecf till read memory: <Control>F9
    # ecf till summarize: <Control>F11
    # books search books: <Control><Alt>B
    # books search publishers: <Control><Alt>P

    # Production application
    ('app.production.new_production_order', '<Control>o',
     _("Create a new production order")),
    ('app.production.new_production_quote', '<Control>p',
     _("Create a new production quote")),
    ('app.production.production_details', '',
     _("Show details for the selected production")),
    ('app.production.production_start', '<Control>t',
     _("Start the selected production")),
    ('app.production.production_edit', '',
     _("Edit the selected production")),
    ('app.production.search_production_products', '<Control>d',
     _("Search for production products")),
    ('app.production.search_services', '<Control>s',
     _("Search for services")),
    ('app.production.search_production_items', '<Control>r',
     _("Search for production items")),
    ('app.production.search_production_history', '<Control>h',
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
    ('app.purchase.search_base_categories', '<Control>b',
     _("Search for base categories")),
    ('app.purchase.search_categories', '<Control>c',
     _("Search for categories")),
    ('app.purchase.search_products', '<Control>d',
     _("Search for products")),
    ('app.purchase.search_product_units', '<Control>u',
     _("Search for product units")),
    ('app.purchase.search_services', '<Control>s',
     _("Search for services")),
    ('app.purchase.search_stock_items', '<Control>i',
     _("Search for stock items")),
    ('app.purchase.search_closed_stock_items', '<Control><Alt>c',
     _("Search for closed stock items")),
    ('app.purchase.search_suppliers', '<Control>u',
     _("Search for suppliers")),
    ('app.purchase.search_transporters', '<Control>t',
     _("Search for transporters")),
    ('app.purchase.search_quotes', '<Control>e',
     _("Search for quotes")),
    ('app.purchase.search_purchased_items', '<Control>p',
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
    # books search books: <Control><Alt>B
    # books search publishers: <Control><Alt>P

    # Receivable application
    ('app.receivable.add_receiving', '<Control>p',
     _("Create a new account receivable")),
    ('app.receivable.payment_flow_history', '<Control>f',
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
    ('app.receivable.payment_comments', '',
     _("Add comments to the selected payment")),
    ('app.receivable.payment_print_bill', '',
     _("Print a bill for the selected payment")),
    ('app.receivable.payment_print_receipt', '<Control>r',
     _("Print a receipt for the selected payment")),
    ('app.receivable.search_bills', '',
     _("Search for bills")),
    ('app.receivable.search_card_payments', '',
     _("Search for card payments")),

    # Sales application
    ('app.sales.search_sold_items_by_branch', '<Control><Alt>a',
     _("Search for sold items by branch")),
    ('app.sales.search_products', '<Control><Alt>p',
     _("Search for products")),
    ('app.sales.search_services', '<Control><Alt>s',
     _("Search for services")),
    ('app.sales.search_deliveries', '<Control><Alt>e',
     _("Search for deliveries")),
    ('app.sales.search_clients', '<Control><Alt>c',
     _("Search for clients")),
    ('app.sales.search_commissions', '<Control><Alt>o',
     _("Search for commissions")),
    ('app.sales.search_loans', '',
     _("Search for loans")),
    ('app.sales.search_loan_items', '',
     _("Search for loan items")),
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
    # books search books: <Control><Alt>B
    # books search publishers: <Control><Alt>P

    # Stock application
    ('app.stock.new_receiving', '<Control>r',
     _("Create a new receiving")),
    ('app.stock.transfer_product', '<Control>t',
     _("Create a new product transfer")),
    ('app.stock.search_receiving', '<Control><Alt>u',
     _("Search for receivings")),
    ('app.stock.search_product_history', "<Control><Alt>p",
     _("Search for product history")),
    ('app.stock.search_purchased_stock_items', '',
     _("Search for purchased stock items")),
    ('app.stock.search_stock_items', "<Control><Alt>s",
     _("Search for stock items")),
    ('app.stock.search_transfers', "<Control><Alt>t",
     _("Search for transfers")),
    ('app.stock.search_closed_stock_items', "<Control><Alt>c",
     _("Search for closed stock items")),
    ('app.stock.edit_product', '',
     _("Edit the selected product")),
    ('app.stock.history', '',
     _("Show the selected product history")),
    ('app.stock.toggle_picture_viewer', '<Control><Alt>v',
     _("Toggle the picture viewer")),

    # Till application
    ('app.till.open_till', '<Control>F6',
     _("Open the till")),
    ('app.till.close_till', '<Control>F7',
     _("Close the till")),
    ('app.till.search_clients', '<Control><Alt>c',
     _("Search for clients")),
    ('app.till.search_sale', '<Control><Alt>a',
     _("Search for sales")),
    ('app.till.search_sold_items_by_branch', '<Contrl><Alt>d',
     _("Search for sold items by branch")),
    ('app.till.search_till_history', '<Control><Alt>t',
     _("Search for till history")),
    ('app.till.search_fiscal_till_operations', '<Contro><Alt>f',
     _("Search for fiscal till operations")),
    ('app.till.confirm_sale', '',
     _("Confirm the sale")),
    ('app.till.return_sale', '',
     _("Return the sale")),
    ('app.till.sale_details', '',
     _("Show details of the sale")),
    # ecf till read memory: <Control>F9
    # ecf till summarize: <Control>F11
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


class KeyBindingGroup(object):
    def __init__(self, bindings):
        self._bindings = bindings

    def get(self, name):
        if not name in self._bindings:
            raise AttributeError(name)
        return self._bindings[name]


def add_bindings(bindings):
    global _bindings
    _bindings.extend(bindings)


def load_user_keybindings():
    from stoqlib.api import api
    d = api.user_settings.get('shortcuts', {})
    for key, value in d.items():
        set_user_binding(key, value)


def set_user_binding(binding, value):
    global _user_bindings
    _user_bindings[binding] = value


def remove_user_binding(binding):
    global _user_bindings
    try:
        del _user_bindings[binding]
    except KeyError:
        pass


def remove_user_bindings():
    global _user_bindings
    _user_bindings = {}


def get_bindings(category=None):
    global _bindings
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
