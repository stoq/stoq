# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Helper functions related to administration of the database, creating
tables, removing tables and configuring administration user.
"""


from kiwi.argcheck import argcheck
from kiwi.environ import environ

from stoqdrivers.constants import UNIT_WEIGHT, UNIT_LITERS, UNIT_METERS

from stoqlib.database import (setup_tables, get_registered_db_settings,
                              finish_transaction, run_sql_file)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.runtime import (new_transaction, print_msg,
                                 set_current_user, get_connection)
from stoqlib.lib.parameters import sysparam, ensure_system_parameters
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.interfaces import (IIndividual, IEmployee, IUser,
                                       ISalesPerson)

_ = stoqlib_gettext

USER_ADMIN_DEFAULT_NAME = _('administrator')

def ensure_admin_user(administrator_password):
    from stoqlib.domain.person import EmployeeRole, PersonAdaptToUser
    from stoqlib.domain.profile import UserProfile
    print_msg("Creating administrator user...", break_line=False)
    conn = new_transaction()

    # XXX Person for administrator user is the same of Current Branch. I'm not
    # sure if it's the best approach but for sure it's better than
    # create another one just for this user.
    company = sysparam(conn).CURRENT_BRANCH
    person_obj = company.get_adapted()

    # Dependencies to create an user.
    role = EmployeeRole(name=_('System Administrator'), connection=conn)
    user = person_obj.addFacet(IIndividual, connection=conn)
    user = person_obj.addFacet(IEmployee, role=role,
                               connection=conn)
    # This is usefull when testing a initial database. Admin user actually
    # must have all the facets.
    person_obj.addFacet(ISalesPerson, connection=conn)

    profile = UserProfile.create_profile_template(conn, _('Administrator'),
                                                  has_full_permission=True)

    username = USER_ADMIN_DEFAULT_NAME
    user = person_obj.addFacet(IUser, username=username,
                               password=administrator_password,
                               profile=profile, connection=conn)
    table = PersonAdaptToUser
    ret = table.select(table.q.username == username, connection=conn)
    assert ret, ret.count() == 1
    assert ret[0].password == administrator_password
    finish_transaction(conn, 1)
    print_msg('done')
    return user

def set_current_user_admin():
    conn = get_connection()
    branch = sysparam(conn).CURRENT_BRANCH
    user = IUser(branch.get_adapted(), connection=conn)
    if not user:
        raise DatabaseInconsistency("You should have a user admin set "
                                    "at this point")
    set_current_user(user)

def ensure_sellable_units():
    from stoqlib.domain.sellable import SellableUnit
    """ Create native sellable units. """
    print_msg("Creating sellable units... ", break_line=False)
    conn = new_transaction()
    unit_list = [("Kg", UNIT_WEIGHT),
                 ("Lt", UNIT_LITERS),
                 ("m ", UNIT_METERS)]
    for desc, index in unit_list:
        SellableUnit(description=desc, index=index, connection=conn)
    finish_transaction(conn, 1)
    print_msg("done")

def create_base_schema():
    rdbms_name = get_registered_db_settings().rdbms
    filename = '%s-schema.sql' % rdbms_name
    sql_file = environ.find_resource('sql', filename)
    conn = new_transaction()
    run_sql_file(sql_file, conn)
    finish_transaction(conn, 1)

@argcheck(str, bool, bool, bool)
def initialize_system(password='', delete_only=False, 
                      list_tables=False, verbose=False):
    """Call all the necessary methods to startup Stoq applications for
    every purpose: production usage, testing or demonstration
    """
    setup_tables(delete_only=delete_only, list_tables=list_tables,
                 verbose=verbose)
    create_base_schema()
    ensure_system_parameters()
    ensure_admin_user(password)
    ensure_sellable_units()
