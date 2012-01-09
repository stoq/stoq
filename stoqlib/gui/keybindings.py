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

_bindings = [
    # Common application shortcuts
    ('app.common.toggle_fullscreen', '<Control>F11'),
    ('app.common.toggle_statusbar', ''),
    ('app.common.toggle_toolbar', ''),
    ('app.common.help_contents', ''),
    ('app.common.new_window', '<Control>n'),
    ('app.common.change_password', ''),
    ('app.common.sign_out', ''),
    ('app.common.close_window', '<Control>w'),
    ('app.common.print', '<Control>p'),
    ('app.common.quit', '<Control>q'),
    ('app.common.help', 'F1'),
    ('app.common.help_contents', '<Control>F1'),

    # Admin application
    ('app.admin.search_roles', '<Control><Alt>o'),
    ('app.admin.search_employees', '<Control><Alt>e'),
    ('app.admin.search_events', ''),
    ('app.admin.search_cfop', '<Control>o'),
    ('app.admin.search_fiscalbook', '<Control><alt>f'),
    ('app.admin.search_profile', '<Control><Alt>u'),
    ('app.admin.search_users', '<Control>u'),
    ('app.admin.search_branches', '<Control>b'),
    ('app.admin.search_computers', '<Control><alt>h'),
    ('app.admin.config_devices', '<Control>d'),
    ('app.admin.config_payment_methods', '<Control>m'),
    ('app.admin.config_payment_categories', '<Control>a'),
    ('app.admin.config_client_categories', '<Control>x'),
    ('app.admin.config_invoices', '<Control>n'),
    ('app.admin.config_invoice_printers', '<Control>f'),
    ('app.admin.config_sintegra', '<Control>w'),
    ('app.admin.config_taxes', '<Control>l'),
    ('app.admin.config_parameters', '<Control>y'),

    # Calendar application
    ('app.calendar.go_back', ''),
    ('app.calendar.go_forward', ''),
    ('app.calendar.show_today', ''),

    # Financial application
    ('app.financial.import', '<Control>i'),
    ('app.financial.delete_account', ''),
    ('app.financial.delete_transaction', ''),
    ('app.financial.new_account', '<Control>a'),
    ('app.financial.new_transaction', '<Control>t'),
    ('app.financial.edit', ''),

    # Inventory application
    ('app.inventory.new_inventory', ''),
    ('app.inventory.inventory_count', '<Control>c'),
    ('app.inventory.inventory_adjust', '<Control>a'),
    ('app.inventory.inventory_cancel', ''),
    ('app.inventory.inventory_print', ''),

    # Payable application
    ('app.payable.add_payable', '<Control>p'),
    ('app.payable.payment_flow_history', '<Control>f'),
    ('app.payable.payment_details', ''),
    ('app.payable.payment_pay', ''),
    ('app.payable.payment_edit', ''),
    ('app.payable.payment_cancel', ''),
    ('app.payable.payment_set_not_paid', ''),
    ('app.payable.payment_change_due_date', ''),
    ('app.payable.payment_comments', ''),
    ('app.payable.payment_print_receipt', '<Control>r'),
    ('app.payable.search_bills', ''),

    # Pos application
    ('app.pos.till_open', '<Control>F6'),
    ('app.pos.till_close', '<Control>F7'),
    ('app.pos.order_confirm', '<Control>F10'),
    ('app.pos.order_cancel', '<Control><Alt>o'),
    ('app.pos.order_create_delivery', '<Control>F5'),
    ('app.pos.search_sales', '<Control><Alt>a'),
    ('app.pos.search_sold_items', '<Contrl><Alt>a'),
    ('app.pos.search_clients', '<Control><Alt>c'),
    ('app.pos.search_products', '<Control><Alt>p'),
    ('app.pos.search_services', '<Contro><Alt>s'),
    ('app.pos.search_deliveries', '<Control><Alt>e'),
    # ecf till read memory: <Control>F9
    # ecf till summarize: <Control>F11
    # books search books: <Control><Alt>B
    # books search publishers: <Control><Alt>P

    # Production application
    ('app.production.new_production_order', '<Control>o'),
    ('app.production.new_production_quote', '<Control>p'),
    ('app.production.production_details', ''),
    ('app.production.production_start', '<Control>t'),
    ('app.production.production_edit', ''),
    ('app.production.search_production_products', '<Control>d'),
    ('app.production.search_services', '<Control>s'),
    ('app.production.search_production_items', '<Control>r'),
    ('app.production.search_production_history', '<Control>h'),

    # Purchase application
    ('app.purchase.new_order', '<control>o'),
    ('app.purchase.new_quote', '<control>e'),
    ('app.purchase.new_consignment', ''),
    ('app.purchase.new_product', ''),
    ('app.purchase.search_base_categories', '<Control>b'),
    ('app.purchase.search_categories', '<Control>c'),
    ('app.purchase.search_products', '<Control>d'),
    ('app.purchase.search_product_units', '<Control>u'),
    ('app.purchase.search_services', '<Control>s'),
    ('app.purchase.search_stock_items', '<Control>i'),
    ('app.purchase.search_closed_stock_items', '<Control><Alt>c'),
    ('app.purchase.search_suppliers', '<Control>u'),
    ('app.purchase.search_transporters', '<Control>t'),
    ('app.purchase.search_quotes', '<Control>e'),
    ('app.purchase.search_purchased_items', '<Control>p'),
    ('app.purchase.search_products_sold', ''),
    ('app.purchase.search_prices', ''),
    ('app.purchase.search_consignment_items', ''),
    ('app.purchase.order_confirm', ''),
    ('app.purchase.order_cancel', ''),
    ('app.purchase.order_edit', ''),
    ('app.purchase.order_details', ''),
    ('app.purchase.order_finish', ''),
    # books search books: <Control><Alt>B
    # books search publishers: <Control><Alt>P

    # Receivable application
    ('app.receivable.add_receiving', '<Control>p'),
    ('app.receivable.payment_flow_history', '<Control>f'),
    ('app.receivable.payment_details', ''),
    ('app.receivable.payment_receive', ''),
    ('app.receivable.payment_cancel', ''),
    ('app.receivable.payment_set_not_paid', ''),
    ('app.receivable.payment_change_due_date', ''),
    ('app.receivable.payment_renegotiate', ''),
    ('app.receivable.payment_comments', ''),
    ('app.receivable.payment_print_bill', ''),
    ('app.receivable.payment_print_receipt', '<Control>r'),
    ('app.receivable.search_bills', ''),
    ('app.receivable.search_card_payments', ''),

    # Sales application
    ('app.sales.search_sold_items_by_branch', '<Control><Alt>a'),
    ('app.sales.search_products', '<Control><Alt>p'),
    ('app.sales.search_services', '<Control><Alt>s'),
    ('app.sales.search_deliveries', '<Control><Alt>e'),
    ('app.sales.search_clients', '<Control><Alt>c'),
    ('app.sales.search_commissions', '<Control><Alt>o'),
    ('app.sales.search_loans', ''),
    ('app.sales.search_loan_items', ''),
    ('app.sales.sale_cancel', ''),
    ('app.sales.sale_print_invoice', ''),
    ('app.sales.sale_return', ''),
    ('app.sales.sale_edit', ''),
    ('app.sales.sale_details', ''),
    # books search books: <Control><Alt>B
    # books search publishers: <Control><Alt>P

    # Stock application
    ('app.stock.new_receiving', '<Control>r'),
    ('app.stock.transfer_product', '<Control>t'),
    ('app.stock.search_receiving', '<Control><Alt>u'),
    ('app.stock.search_product_history', "<Control><Alt>p"),
    ('app.stock.search_purchased_stock_items', ''),
    ('app.stock.search_stock_items', "<Control><Alt>s"),
    ('app.stock.search_transfers', "<Control><Alt>t"),
    ('app.stock.search_closed_stock_items', "<Control><Alt>c"),
    ('app.stock.edit_product', ''),
    ('app.stock.history', ''),
    ('app.stock.toggle_picture_viewer', '<Control><Alt>v'),

    # Till application
    ('app.till.open_till', '<Control>F6'),
    ('app.till.close_till', '<Control>F7'),
    ('app.till.search_clients', '<Control><Alt>c'),
    ('app.till.search_sale', '<Control><Alt>a'),
    ('app.till.search_sold_items_by_branch', '<Contrl><Alt>d'),
    ('app.till.search_till_history', '<Control><Alt>t'),
    ('app.till.search_fiscal_till_operations', '<Contro><Alt>f'),
    ('app.till.confirm_sale', ''),
    ('app.till.return_sale', ''),
    ('app.till.sale_details', ''),
    # ecf till read memory: <Control>F9
    # ecf till summarize: <Control>F11
]


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


def get_accels(prefix=''):
    d = {}
    if prefix and not prefix.endswith('.'):
        prefix += '.'

    for name, accel in _bindings:
        if name.startswith(prefix):
            sub = name[len(prefix):]
            d[sub] = accel
    return KeyBindingGroup(d)


def get_accel(accel_name):
    for name, accel in _bindings:
        if name == accel_name:
            return accel

    raise AttributeError(accel_name)
