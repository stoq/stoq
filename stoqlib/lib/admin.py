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
from kiwi.component import get_utility, provide_utility
from kiwi.datatypes import currency
from kiwi.environ import environ
from kiwi.log import Logger

from stoqdrivers.constants import UNIT_WEIGHT, UNIT_LITERS, UNIT_METERS

from stoqlib.database import setup_tables, finish_transaction, run_sql_file
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.interfaces import ICurrentUser, IDatabaseSettings
from stoqlib.lib.runtime import new_transaction
from stoqlib.lib.parameters import sysparam, ensure_system_parameters
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.interfaces import (IIndividual, IEmployee, IUser,
                                       ISalesPerson)

_ = stoqlib_gettext

log = Logger('stoqlib.admin')
USER_ADMIN_DEFAULT_NAME = 'admin'

def ensure_admin_user(administrator_password):
    from stoqlib.domain.person import EmployeeRole, PersonAdaptToUser
    from stoqlib.domain.profile import UserProfile
    from stoqlib.domain.person import EmployeeRoleHistory
    log.info("Creating administrator user")
    trans = new_transaction()

    # XXX Person for administrator user is the same of Current Branch. I'm not
    # sure if it's the best approach but for sure it's better than
    # create another one just for this user.
    company = sysparam(trans).MAIN_COMPANY
    person_obj = company.get_adapted()

    # Dependencies to create an user.
    role = EmployeeRole(name=_('System Administrator'), connection=trans)
    user = person_obj.addFacet(IIndividual, connection=trans)
    user = person_obj.addFacet(IEmployee, role=role,
                               connection=trans)
    role_history = EmployeeRoleHistory(connection=trans,
                                       role=role,
                                       employee=user,
                                       is_active=True,
                                       salary=currency(800))

    # This is usefull when testing a initial database. Admin user actually
    # must have all the facets.
    person_obj.addFacet(ISalesPerson, connection=trans)

    log.info("Creating user profile for administrator")
    profile = UserProfile.create_profile_template(trans, _('Administrator'),
                                                  has_full_permission=True)


    username = USER_ADMIN_DEFAULT_NAME
    log.info("Attaching IUser facet (%s)" % (username,))
    user = person_obj.addFacet(IUser, username=username,
                               password=administrator_password,
                               profile=profile, connection=trans)

    table = PersonAdaptToUser
    ret = table.select(table.q.username == username, connection=trans)
    assert ret, ret.count() == 1
    assert ret[0].password == administrator_password

    finish_transaction(trans, 1)

    # We can't provide the utility until it's actually in the database
    log.info('providing utility ICurrentUser')
    provide_utility(ICurrentUser, user)

def ensure_sellable_units():
    from stoqlib.domain.sellable import SellableUnit
    """ Create native sellable units. """
    log.info("Creating sellable units")
    trans = new_transaction()
    unit_list = [("Kg", UNIT_WEIGHT),
                 ("Lt", UNIT_LITERS),
                 ("m ", UNIT_METERS)]
    for desc, index in unit_list:
        SellableUnit(description=desc, index=index, connection=trans)
    finish_transaction(trans, 1)

def user_has_usesuper(trans):
    """
    This method checks if the currently logged in postgres user has
    `usesuper' access which is necessary for certain operations

    @param trans: a database connection
    @returns: if the user has `usesuper' access
    """

    results = trans.queryOne(
        'SELECT usesuper FROM pg_user WHERE usename=CURRENT_USER')
    return results[0] == 1

def _create_procedural_languages(trans):
    "Creates procedural SQL languages we're going to use in scripts"

    results = trans.queryAll('SELECT lanname FROM pg_language')
    languages = [item[0] for item in results]
    if 'plpgsql' in languages:
        return

    if not user_has_usesuper(trans):
        raise StoqlibError(
            "The current database user does not have super user rights")

    # Create the plpgsql language
    trans.query('CREATE LANGUAGE plpgsql')

def create_base_schema():
    filename = '%s-schema.sql' % get_utility(IDatabaseSettings).rdbms
    sql_file = environ.find_resource('sql', filename)

    trans = new_transaction()

    # Create the procedural languages here instead of depending
    # on the user running the `createlang' utility manually.
    _create_procedural_languages(trans)

    run_sql_file(sql_file, trans)
    finish_transaction(trans, 1)

@argcheck(bool, bool)
def initialize_system(delete_only=False, verbose=False):
    """Call all the necessary methods to startup Stoq applications for
    every purpose: production usage, testing or demonstration
    """
    setup_tables(delete_only=delete_only)
    create_base_schema()
    ensure_system_parameters()
    ensure_sellable_units()

    trans = new_transaction()
    # Import here since we must create properly the domain schema before
    # importing them in the migration module
    from stoqlib.lib.migration import add_system_table_reference
    add_system_table_reference(trans, check_new_db=True)
    finish_transaction(trans, 1)
