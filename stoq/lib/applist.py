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

import platform

from stoqlib.lib.translation import stoqlib_gettext as _

N_ = lambda s: s

_APPLICATIONS = {
    u'admin': (N_(u"Administrative"),
               N_(u"Administer the branches, users, employees and configure "
                  u"system parameters.")),
    u'calendar': (N_(u"Calendar"),
                  N_(u"Shows payments, orders and other things that will happen "
                     u"in the future.")),
    u'financial': (N_(u"Financial"),
                   N_(u"Control accounts and financial transactions.")),
    u'inventory': (N_(u"Inventory"),
                   N_(u"Audit and adjust the product stock.")),
    u'link': (N_(u"Stoq.Link"),
              N_(u"Manage your company from the cloud with Stoq.link.")),
    u'services': (N_(u"Services"),
                  N_(u"Perform services like maintenance, installation or repair.")),
    u'payable': (N_(u"Accounts Payable"),
                 N_(u"Manage payment that needs to be paid.")),
    u'pos': (N_(u"Point of Sales"),
             N_(u"Terminal and cash register for selling products and "
                u"services.")),
    u'production': (N_(u"Production"),
                    N_(u"Manage the production process.")),
    u'purchase': (N_(u"Purchase"),
                  N_(u"Create purchase orders and quotes")),
    u'receivable': (N_(u"Accounts Receivable"),
                    N_(u"Manage payments that needs to be received.")),
    u'sales': (N_(u"Sales"),
               N_(u"Quotes management and commission calculation.")),
    u'stock': (N_(u"Stock"),
               N_(u"Stock management, receive products and transfer them "
                  u"between branches.")),
    u'till': (N_(u"Till"),
              N_(u"Control tills and their workflow.")),
}

if platform.system() == u'Windows':
    del _APPLICATIONS[u'calendar']


def get_application_names():
    """Get a list of application names, useful for launcher programs

    @returns: application names
    """
    return list(_APPLICATIONS.keys())


def get_application_icon(appname):
    from stoqlib.gui.stockicons import (
        STOQ_ADMIN_APP, STOQ_CALENDAR_APP, STOQ_CALC, STOQ_INVENTORY_APP,
        STOQ_PAYABLE_APP, STOQ_POS_APP, STOQ_PRODUCTION_APP,
        STOQ_PURCHASE_APP, STOQ_BILLS, STOQ_SALES_APP, STOQ_SERVICES,
        STOQ_STOCK_APP, STOQ_TILL_APP, STOQ_LINK)

    return {u'admin': STOQ_ADMIN_APP,
            u'calendar': STOQ_CALENDAR_APP,
            u'financial': STOQ_CALC,
            u'inventory': STOQ_INVENTORY_APP,
            u'launcher': STOQ_STOCK_APP,
            u'link': STOQ_LINK,
            u'services': STOQ_SERVICES,
            u'payable': STOQ_PAYABLE_APP,
            u'pos': STOQ_POS_APP,
            u'production': STOQ_PRODUCTION_APP,
            u'purchase': STOQ_PURCHASE_APP,
            u'receivable': STOQ_BILLS,
            u'sales': STOQ_SALES_APP,
            u'stock': STOQ_STOCK_APP,
            u'till': STOQ_TILL_APP}[appname]


#@implementer(IApplicationDescriptions)
class ApplicationDescriptions:

    def get_application_names(self):
        return get_application_names()

    def get_descriptions(self):
        app_desc = []
        for name, (label, description) in _APPLICATIONS.items():
            icon = get_application_icon(name)
            app_desc.append((name, _(label),
                             icon, _(description)))
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
