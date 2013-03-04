# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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
""" Services report implementation """

from stoqlib.reporting.report import ObjectListReport, TableReport
from stoqlib.lib.translation import stoqlib_gettext as _


class ServiceReport(ObjectListReport):
    """This report show a list of services returned by a SearchBar,
    listing both its description, cost and price.
    """
    title = _("Service Listing")
    filter_format_string = _("on branch <u>%s</u>")
    main_object_name = (_("service"), _("services"))


class ServicePriceReport(TableReport):
    """This report show a list of services and it's prices."""
    title = _("Service Listing")
    main_object_name = (_("service"), _("services"))

    def get_columns(self):
        return [dict(title=_('Code'), align='right'),
                dict(title=_('Description')),
                dict(title=_('Price'), align='right')]

    def get_row(self, obj):
        return [obj.code, obj.description, obj.price]
