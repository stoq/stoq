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

# pylint: enable=E1101

from stoqlib.database.properties import BoolCol, UnicodeCol
from stoqlib.domain.base import Domain


class ParameterData(Domain):
    """ Class to store system parameters.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/parameter_data.html>`__
    """
    __storm_table__ = 'parameter_data'

    #: name of the parameter we want to query on
    field_name = UnicodeCol()

    #: current result(or value) of this parameter
    field_value = UnicodeCol()

    #: the item can't be edited through an editor.
    is_editable = BoolCol()
