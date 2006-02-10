# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Database access methods """

from stoqlib.lib.runtime import new_transaction, print_msg
from stoqlib.domain.tables import get_table_types


# This class will be moved to it's proper place after bug 2253
class Adapter:
    pass


def rollback_and_begin(conn):
    conn.rollback()
    conn.begin()

def finish_transaction(conn, model=None, keep_transaction=False):
    if model:
        conn.commit()
    else:
        rollback_and_begin(conn)
    if not keep_transaction:
        # XXX Waiting for SQLObject improvements. We need there a
        # simple method do this in a simple way.
        conn._connection.close()
    return model


def setup_tables(delete_only=False, list_tables=False, verbose=False):
    from stoqlib.domain.system import add_system_table_reference
    if not list_tables and verbose:
        print_msg('Setting up tables... ', break_line=False)
    else:
        print_msg('Setting up tables... ')

    table_types = get_table_types()
    conn = new_transaction()
    for table in table_types:
        if conn.tableExists(table.get_db_table_name()):
            table.dropTable(ifExists=True, cascade=True, connection=conn)
            if list_tables:
                print_msg('<removed>:  %s' % table)
        if delete_only:
            continue
        table.createTable(connection=conn)
        if list_tables:
            print_msg('<created>:  %s' % table)
    conn.commit()
    if delete_only:
        return

    add_system_table_reference(conn, check_new_db=True)
    finish_transaction(conn, 1)
    print_msg('done')
