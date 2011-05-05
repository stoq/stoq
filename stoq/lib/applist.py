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

from kiwi.component import implements
from stoqlib.lib.interfaces import IApplicationDescriptions


def get_application_names():
    """Get a list of application names, useful for launcher programs

    @returns: application names
    """
    return ['admin',
            'financial',
            'inventory',
            'payable',
            'pos',
            'production',
            'purchase',
            'receivable',
            'sales',
            'stock',
            'till']


class ApplicationDescriptions:

    implements(IApplicationDescriptions)

    def get_application_names(self):
        return get_application_names()

    def get_descriptions(self):
        applications = self.get_application_names()
        app_desc = []
        for name in applications:
            module = __import__("stoq.gui.%s" % (name,),
                                globals(), locals(), ' ')
            if not hasattr(module, "application"):
                raise ValueError('Module %r must have an application attribute'
                                 % module)
            icon = getattr(module, 'icon_name', None)
            description = getattr(module, 'description', None)
            app_desc.append((name,
                             module.application, icon, description))
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
