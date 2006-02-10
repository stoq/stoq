# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Routines for system data management"""


from sqlobject import SQLObject
from sqlobject import DateTimeCol, IntCol

from stoqlib.domain.base import AbstractModel


class SystemTable(SQLObject, AbstractModel):
    """Stores information about database schema migration

    I{update_date}: the date when the database schema was updated
    I{version}: the version of the schema installed
    """
    update_date = DateTimeCol()
    version = IntCol()
