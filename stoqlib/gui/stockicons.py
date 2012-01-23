# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source
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

STOQ_ADMIN_APP = "stoq-admin-app"
STOQ_BILLS = "stoq-bills"
STOQ_CALENDAR_APP = "stoq-calendar-app"
STOQ_CALENDAR_LIST = "stoq-calendar-list"
STOQ_CALENDAR_MONTH = "stoq-calendar-month"
STOQ_CALENDAR_TODAY = "stoq-calendar-today"
STOQ_CALENDAR_WEEK = "stoq-calendar-week"
STOQ_CLIENTS = "stoq-clients"
STOQ_EDIT = "stoq-edit"
STOQ_DELIVERY = "stoq-delivery"
STOQ_HR = "stoq-hr"
STOQ_INVENTORY_APP = "stoq-inventory-app"
STOQ_FORMS = "stoq-forms"
STOQ_KEYBOARD = "stoq-keyboard"
STOQ_MONEY = "stoq-money"
STOQ_MONEY_ADD = "stoq-money-add"
STOQ_MONEY_REMOVE = "stoq-money-remove"
STOQ_PAYABLE_APP = "stoq-payable-app"
STOQ_POS_APP = "stoq-pos-app"
STOQ_PRODUCTION_APP = "stoq-production-app"
STOQ_PRODUCTS = "stoq-products"
STOQ_PURCHASE_APP = "stoq-purchase-app"
STOQ_RECEIVING = "stoq-receiving"
STOQ_SALES_APP = "stoq-sales-app"
STOQ_SERVICES = "stoq-services"
STOQ_STOCK_APP = "stoq-stock-app"
STOQ_SUPPLIERS = "stoq-suppliers"
STOQ_TILL_APP = "stoq-till-app"
STOQ_USERS = "stoq-users"
STOQ_SYSTEM = "stoq-system"
STOQ_CALC = "stoq-calc"
STOQ_TAXES = "stoq-taxes"
STOQ_DOCUMENTS = "stoq-documents"
STOQ_DEVICES = "stoq-devices"
STOQ_USER_PROFILES = "stoq-user-profiles"


# Add aliases so we don't need to import gtk
# 16: GTK_ICON_SIZE_MENU
# 18: GTK_ICON_SIZE_SMALL_TOOLBAR
# 20: GTK_ICON_SIZE_BUTTON
# 24: GTK_ICON_SIZE_LARGE_TOOLBAR
# 32: GTK_ICON_SIZE_DND
# 48: GTK_ICON_SIZE_DIALOG
GTK_ICON_SIZE_MENU = 16
GTK_ICON_SIZE_SMALL_TOOLBAR = 18
GTK_ICON_SIZE_BUTTON = 20
GTK_ICON_SIZE_LARGE_TOOLBAR = 24
GTK_ICON_SIZE_DND = 32
GTK_ICON_SIZE_DIALOG = 48

icon_info = [
    (STOQ_ADMIN_APP,
     {GTK_ICON_SIZE_MENU: "stoq-admin-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-admin-24x24.png",
      GTK_ICON_SIZE_DND: "stoq-admin-32x32.png",
      GTK_ICON_SIZE_DIALOG: "stoq-admin-48x48.png"}),
    (STOQ_BILLS,
     {GTK_ICON_SIZE_DIALOG: "stoq-bills-48x48.png"}),
    (STOQ_CALENDAR_APP,
     {GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-calendar-24x24.svg",
      GTK_ICON_SIZE_DIALOG: "stoq-calendar-48x48.svg"}),
    (STOQ_CALENDAR_LIST,
     {GTK_ICON_SIZE_MENU: "stoq-calendar-list-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-calendar-list-24x24.png"}),
    (STOQ_CALENDAR_MONTH,
     {GTK_ICON_SIZE_MENU: "stoq-calendar-month-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-calendar-month-24x24.png"}),
    (STOQ_CALENDAR_TODAY,
     {GTK_ICON_SIZE_MENU: "stoq-calendar-today-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-calendar-today-24x24.png"}),
    (STOQ_CALENDAR_WEEK,
     {GTK_ICON_SIZE_MENU: "stoq-calendar-week-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-calendar-week-24x24.png"}),
    (STOQ_CLIENTS,
     {GTK_ICON_SIZE_DIALOG: "stoq-clients-48x48.png"}),
    (STOQ_DELIVERY,
     {GTK_ICON_SIZE_MENU: "stoq-delivery-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-delivery-24x24.png",
      GTK_ICON_SIZE_DIALOG: "stoq-delivery-48x48.png"}),
    (STOQ_EDIT,
     {GTK_ICON_SIZE_DIALOG: "stoq-edit-48x48.png"}),
    (STOQ_FORMS,
     {GTK_ICON_SIZE_DIALOG: "stoq-forms-48x48.png"}),
    (STOQ_HR,
     {GTK_ICON_SIZE_MENU: "stoq-hr-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-hr-24x24.png",
      GTK_ICON_SIZE_DND: "stoq-hr-32x32.png",
      GTK_ICON_SIZE_DIALOG: "stoq-hr-48x48.png"}),
    (STOQ_INVENTORY_APP,
     {GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-inventory-app-24x24.png",
      GTK_ICON_SIZE_DIALOG: "stoq-inventory-app-48x48.png"}),
    (STOQ_KEYBOARD,
     {GTK_ICON_SIZE_DIALOG: "stoq-keyboard-48x48.svg"}),
    (STOQ_MONEY,
     {GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-money-24x24.png",
      GTK_ICON_SIZE_DIALOG: "stoq-money-48x48.png"}),
    (STOQ_MONEY_ADD,
     {GTK_ICON_SIZE_MENU: "stoq-money-add-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-money-add-24x24.png"}),
    (STOQ_MONEY_REMOVE,
     {GTK_ICON_SIZE_MENU: "stoq-money-remove-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-money-remove-24x24.png"}),
    (STOQ_PAYABLE_APP,
     {GTK_ICON_SIZE_DIALOG: "stoq-payable-app-48x48.png"}),
    (STOQ_POS_APP,
     {GTK_ICON_SIZE_MENU: "stoq-pos-app-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-pos-app-24x24.png",
      GTK_ICON_SIZE_DND: "stoq-pos-app-32x32.png",
      GTK_ICON_SIZE_DIALOG: "stoq-pos-app-48x48.png"}),
    (STOQ_PRODUCTION_APP,
     {GTK_ICON_SIZE_DIALOG: "stoq-production-app.png"}),
    (STOQ_PRODUCTS,
     {GTK_ICON_SIZE_MENU: "stoq-products-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-products-24x24.png",
      GTK_ICON_SIZE_DND: "stoq-products-32x32.png",
      GTK_ICON_SIZE_DIALOG: "stoq-products-48x48.png"}),
    (STOQ_PURCHASE_APP,
    {GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-purchase-app-24x24.png",
      GTK_ICON_SIZE_DIALOG: "stoq-purchase-app-48x48.png"}),
    (STOQ_RECEIVING,
     {GTK_ICON_SIZE_DIALOG: "stoq-receiving-48x48.png"}),
    (STOQ_SALES_APP,
     {GTK_ICON_SIZE_DIALOG: "stoq-sales-app-48x48.png"}),
    (STOQ_SERVICES,
     {GTK_ICON_SIZE_DIALOG: "stoq-services-48x48.png"}),
    (STOQ_STOCK_APP,
     {GTK_ICON_SIZE_MENU: "stoq-stock-app-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-stock-app-24x24.png",
      GTK_ICON_SIZE_DND: "stoq-stock-app-32x32.png",
      GTK_ICON_SIZE_DIALOG: "stoq-stock-app-48x48.png"}),
    (STOQ_SUPPLIERS,
     {GTK_ICON_SIZE_DIALOG: "stoq-suppliers-48x48.png"}),
    (STOQ_TILL_APP,
     {GTK_ICON_SIZE_MENU: "stoq-till-app-16x16.png",
      GTK_ICON_SIZE_LARGE_TOOLBAR: "stoq-till-app-24x24.png",
      GTK_ICON_SIZE_DND: "stoq-till-app-32x32.png",
      GTK_ICON_SIZE_DIALOG: "stoq-till-app-48x48.png"}),
    (STOQ_USERS,
     {GTK_ICON_SIZE_MENU: "stoq-users-16x16.png",
      GTK_ICON_SIZE_DIALOG: "stoq-users-48x48.png"}),
    (STOQ_SYSTEM,
     {GTK_ICON_SIZE_DIALOG: "stoq-system-48x48.png"}),
    (STOQ_CALC,
     {GTK_ICON_SIZE_DIALOG: "stoq-calc-48x48.png"}),
    (STOQ_TAXES,
     {GTK_ICON_SIZE_DIALOG: "stoq-taxes-48x48.png"}),
    (STOQ_DOCUMENTS,
     {GTK_ICON_SIZE_DIALOG: "stoq-documents-48x48.png"}),
    (STOQ_DEVICES,
     {GTK_ICON_SIZE_DIALOG: "stoq-devices-48x48.png"}),
    (STOQ_USER_PROFILES,
     {GTK_ICON_SIZE_DIALOG: "stoq-user-profiles-48x48.png"}),
]


# register stoq stock icons
def register():
    import gtk
    from kiwi.environ import environ

    iconfactory = gtk.IconFactory()
    stock_ids = gtk.stock_list_ids()
    for stock_id, arg in icon_info:
        # only load image files when our stock_id is not present
        if stock_id in stock_ids:
            continue
        iconset = gtk.IconSet()
        for size, filename in arg.items():
            iconsource = gtk.IconSource()
            filename = environ.find_resource('pixmaps', filename)
            iconsource.set_filename(filename)
            iconsource.set_size(size)
            iconset.add_source(iconsource)
        iconfactory.add(stock_id, iconset)
    iconfactory.add_default()
