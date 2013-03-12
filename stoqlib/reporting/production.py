# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Production report implementation """

from stoqlib.reporting.report import ObjectListReport, HTMLReport
from stoqlib.lib.translation import stoqlib_gettext as _


class ProductionItemReport(ObjectListReport):
    """ This report show a list of all production items returned by a SearchBar,
    listing both its description, category and its quantities.
    """
    title = _("Production Item Listing")
    filter_format_string = _("on branch <u>%s</u>")
    summary = ['quantity', 'produced', 'lost']


class ProductionReport(ObjectListReport):
    title = _(u'Production Order Report')
    main_object_name = (_("order"), _("orders"))
    filter_format_string = _(u'with status <u>%s</u>')


class ProductionOrderReport(HTMLReport):
    template_filename = 'production/production.html'
    title = _(u'Production Order')
    complete_header = False

    def __init__(self, filename, order):
        self.order = order
        HTMLReport.__init__(self, filename)

    def get_subtitle(self):
        return _(u'Number: %s - %s') % (self.order.identifier,
                                        self.order.get_description())
