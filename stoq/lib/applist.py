# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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

from kiwi.component import implements
from stoqlib.lib.interfaces import IApplicationDescriptions

_ = gettext.gettext
_APPLICATIONS = {
    'admin': ( _('Administrative'),
               _("""Administrative application."""),
               'stoq-admin-app'),
    'financial' : (_('Financial'),
                   _("""Financial application."""),
                   'stoq-payable-app'),
    'inventory' : (_('Inventory'),
                   _("""Inventory application."""),
                   'stoq-inventory-app'),
    'payable' : (_('Accounts Payable'),
                 _("""Accounts Payable application."""),
                 'stoq-payable-app'),
    'pos' : (_('Point of Sales'),
             _("""Point Of Sale application."""),
             'stoq-pos-app'),
    'production' : (_('Production'),
                    _('Production application.'),
                    'stoq-production-app'),
    'purchase' : (_('Purchase'),
                  _("""Purchase application."""),
                  'stoq-purchase-app'),
    'receivable' : (_('Accounts Receivable'),
                    _("""Accounts Receivable application."""),
                    'stoq-bills'),
    'sales' : (_('Sales'),
               _("""Sales application."""),
               'stoq-sales-app'),
    'stock' : (_('Stock'),
               _("""Stock application."""),
               'stoq-stock-app'),
    'till' : (_('Till'),
              _("""Till application."""),
              'stoq-till-app'),
}

def get_application_names():
    """Get a list of application names, useful for launcher programs

    @returns: application names
    """
    return _APPLICATIONS.keys()


class ApplicationDescriptions:

    implements(IApplicationDescriptions)

    def get_application_names(self):
        return get_application_names()

    def get_descriptions(self):
        app_desc = []
        for name, (label, description, icon) in _APPLICATIONS.items():
            app_desc.append((name, label, icon, description))
        return app_desc


class Application(object):
    """
    Describes an application

    @ivar name: short name of application
    @ivar fullname: complete name of application
    @ivar icon: application icon
    @ivar description: long description of application
    """

    def __init__ (self, name, fullname, icon, description):
        self.name = name
        self.fullname = fullname
        self.icon = icon
        self.description = description
