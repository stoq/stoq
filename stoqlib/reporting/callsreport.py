# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

""" A calls receipt implementation """

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import ObjectListReport

_ = stoqlib_gettext


class CallsReport(ObjectListReport):
    """Realized calls to client report"""
    title = _("Calls Report")
    main_object_name = (_("call"), _("calls"))

    def __init__(self, filename, objectlist, data, *args, **kwargs):
        person = kwargs.pop('person', None)
        if person:
            self.main_object_name = (_("performed call to %s") % person.name,
                                     _("performed calls to %s") % person.name)
        ObjectListReport.__init__(self, filename, objectlist, data,
                                  *args, **kwargs)
