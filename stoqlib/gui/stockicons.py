# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2018 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

# Accounts
STOQ_MONEY = "stoq-money"
STOQ_BILLS = "stoq-bills"

# Admin options
STOQ_BRANCHES = "stoq-branches"
STOQ_BOOK = "stoq-book"
STOQ_CLIENTS = "stoq-clients"
STOQ_CONNECT = "stoq-connect"
STOQ_EMPLOYEE = "stoq-employee"
STOQ_EMPLOYEE_CARD = "stoq-employee-card"
STOQ_TRANSPORTER = "stoq-transporter"
STOQ_DEVICES = "stoq-devices"
STOQ_DOCUMENTS = "stoq-documents"
STOQ_HR = "stoq-hr"
STOQ_FORMS = "stoq-forms"
STOQ_MOVEMENT_PRODUCT = "stoq-movement-product"
STOQ_PARAMETERS = "stoq-parameters"
STOQ_PAYMENT_CATEGORY = "stoq-payment-category"
STOQ_PAYMENT_TYPE = "stoq-payment-type"
STOQ_PLUGIN = "stoq-plugin"
STOQ_PRINTER = "stoq-printer"
STOQ_PRODUCTS = "stoq-products"
STOQ_SUPPLIERS = "stoq-suppliers"
STOQ_SYSTEM = "stoq-system"
STOQ_TAX_TYPE = "stoq-tax-type"
STOQ_USER_PROFILES = "stoq-user-profiles"


# Statues
STOQ_STATUS_NA = "stoq-status-na"
STOQ_STATUS_OK = "stoq-status-ok"
STOQ_STATUS_WARNING = "stoq-status-warning"
STOQ_STATUS_ERROR = "stoq-status-error"

# Emblems
STOQ_CALC = "stoq-calc"
STOQ_CHECK = "stoq-check"
STOQ_LOCKED = "stoq-locked"
STOQ_FUNNEL = "stoq-funnel"

# Apps
STOQ_LAUNCHER = "stoq-launcher-symbolic"
STOQ_ADMIN_APP = "stoq-admin-app"
STOQ_CALENDAR_APP = "stoq-calendar-app"
STOQ_DELIVERY = "stoq-delivery"
STOQ_INVENTORY_APP = "stoq-inventory-app"
STOQ_PAYABLE_APP = "stoq-payable-app"
STOQ_POS_APP = "stoq-pos-app"
STOQ_PRODUCTION_APP = "stoq-production-app"
STOQ_PURCHASE_APP = "stoq-purchase-app"
STOQ_RECEIVABLE_APP = "stoq-receivable-app"
STOQ_SALES_APP = "stoq-sales-app"
STOQ_SERVICES = "stoq-services"
STOQ_STOCK_APP = "stoq-stock-app"
STOQ_TILL_APP = "stoq-till-app"
STOQ_LINK = "stoq-link"

# Others
STOQ_REFRESH = 'fa-sync-symbolic'
STOQ_FEEDBACK = "stoq-feedback"


def register():
    from gi.repository import Gtk
    from kiwi.environ import environ

    theme = Gtk.IconTheme.get_default()
    path = environ.get_resource_filename('stoq', 'pixmaps')
    theme.prepend_search_path(path)
