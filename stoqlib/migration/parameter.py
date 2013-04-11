# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""
Use this functions to interact with parameters when creating database patches.

We cannot use stoqlib.lib.parameters directly, since those will use
stoqlib.domain, and se cannot use stoqlib.domain while migrating the database.

See stoqlib.migration.domain for mor information
"""


def get_parameter(store, name, klass=None):
    """Returns the parameter value given its name

    :param klass: if this parameter is a reference to another table, an instance
      of this klass will be returned.
    """
    res = store.execute("""SELECT field_value FROM parameter_data WHERE
                                    field_name = ?""", (name,)).get_one()
    if not res:
        return None
    field_value = res[0]

    if klass:
        return store.find(klass, id=int(field_value)).one()
    return field_value


def update_parameter(store, name, value):
    """Updates the parameter in the database.

    The callsite should convert the value properly
    """
    store.execute("""UPDATE parameter_data
                    SET field_value = ?
                    WHERE field_name = ?""", (value, name))
