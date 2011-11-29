# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Foundation, http://www.gnu.org/
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Domain classes for handling parameters """

from stoqlib.database.orm import UnicodeCol, BoolCol, StringCol
from stoqlib.domain.base import Domain
from stoqlib.lib.translation import stoqlib_gettext as _


class ParameterData(Domain):
    """ Class to store system parameters.

    field_name = the name of the parameter we want to query on
    field_value = the current result(or value) of this parameter
    is_editable = if the item can't be edited through an editor.
    """
    field_name = StringCol(alternateID=True)
    field_value = UnicodeCol()
    is_editable = BoolCol()

    def get_group(self):
        from stoqlib.lib.parameters import get_parameter_details
        return get_parameter_details(self.field_name).group

    def get_short_description(self):
        from stoqlib.lib.parameters import get_parameter_details
        return get_parameter_details(self.field_name).short_desc

    def get_field_value(self):
        #FIXME: This is a workaround to handle some parameters which are
        #       locale specific.
        return _(self.field_value)
