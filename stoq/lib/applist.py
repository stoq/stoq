# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Listing and importing applications """

import gettext
import platform

N_ = lambda s: s

_APPLICATIONS = {
    'admin': (N_("Administrative"),
              N_("Administer the branches, users, employees and configure "
                 "system parameters.")),
    'calendar': (N_("Calendar"),
                 N_("Shows payments, orders and other things that will happen "
                    "in the future.")),
    'financial': (N_("Financial"),
                  N_("Control accounts and financial transactions.")),
    'inventory': (N_("Inventory"),
                  N_("Audit and adjust the product stock.")),
    'payable': (N_("Accounts Payable"),
                N_("Manage payment that needs to be paid.")),
    'pos': (N_("Point of Sales"),
            N_("Terminal and cash register for selling products and "
               "services.")),
    'production': (N_("Production"),
                   N_("Manage the production process.")),
    'purchase': (N_("Purchase"),
                 N_("Create purchase orders and quotes")),
    'receivable': (N_("Accounts Receivable"),
                   N_("Manage payments that needs to be received.")),
    'sales': (N_("Sales"),
              N_("Quotes management and commission calculation.")),
    'stock': (N_("Stock"),
              N_("Stock management, receive products and transfer them "
                 "between branches.")),
    'till': (N_("Till"),
             N_("Control tills and their workflow.")),
}

if platform.system() == 'Windows':
    del _APPLICATIONS['calendar']


def get_application_names():
    """Get a list of application names, useful for launcher programs

    @returns: application names
    """
    return _APPLICATIONS.keys()


def get_application_icon(appname):
    from stoqlib.gui.stockicons import (
        STOQ_ADMIN_APP, STOQ_CALENDAR_APP, STOQ_CALC, STOQ_INVENTORY_APP,
        STOQ_PAYABLE_APP, STOQ_POS_APP, STOQ_PRODUCTION_APP,
        STOQ_PURCHASE_APP, STOQ_BILLS, STOQ_SALES_APP, STOQ_STOCK_APP,
        STOQ_TILL_APP)

    return {'admin': STOQ_ADMIN_APP,
            'calendar': STOQ_CALENDAR_APP,
            'financial': STOQ_CALC,
            'inventory': STOQ_INVENTORY_APP,
            'payable': STOQ_PAYABLE_APP,
            'pos': STOQ_POS_APP,
            'production': STOQ_PRODUCTION_APP,
            'purchase': STOQ_PURCHASE_APP,
            'receivable': STOQ_BILLS,
            'sales': STOQ_SALES_APP,
            'stock': STOQ_STOCK_APP,
            'till': STOQ_TILL_APP}[appname]


class ApplicationDescriptions:

    # implements(IApplicationDescriptions)

    def get_application_names(self):
        return get_application_names()

    def get_descriptions(self):
        app_desc = []
        for name, (label, description) in _APPLICATIONS.items():
            icon = get_application_icon(name)
            app_desc.append((name, gettext.gettext(label),
                             icon, gettext.gettext(description)))
        return app_desc


class Application(object):
    """
    Describes an application

    @ivar name: short name of application
    @ivar fullname: complete name of application
    @ivar icon: application icon
    @ivar description: long description of application
    """

    def __init__(self, name, fullname, icon, description):
        self.name = name
        self.fullname = fullname
        self.icon = icon
        self.description = description
