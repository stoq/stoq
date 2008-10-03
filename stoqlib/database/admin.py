# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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

"""Administration

Helper functions related to administration of the database, creating
tables, removing tables and configuring administration user.
"""

from kiwi.argcheck import argcheck
from kiwi.component import get_utility, provide_utility
from kiwi.datatypes import currency
from kiwi.environ import environ
from kiwi.log import Logger

from stoqdrivers.enum import TaxType, UnitType
from stoqdrivers.constants import describe_constant

from stoqlib.database.database import execute_sql, clean_database
from stoqlib.database.interfaces import (ICurrentBranch, ICurrentUser,
                                         IDatabaseSettings)
from stoqlib.database.migration import StoqlibSchemaMigration
from stoqlib.database.runtime import get_connection, new_transaction
from stoqlib.domain.interfaces import (IIndividual, IEmployee, IUser,
                                       ISalesPerson, ICompany, IBranch)
from stoqlib.domain.person import EmployeeRole, Person
from stoqlib.domain.person import EmployeeRoleHistory
from stoqlib.domain.profile import UserProfile
from stoqlib.domain.sellable import SellableTaxConstant, SellableUnit
from stoqlib.exceptions import StoqlibError
from stoqlib.importers.invoiceimporter import InvoiceImporter
from stoqlib.lib.interfaces import IPaymentOperationManager
from stoqlib.lib.message import error
from stoqlib.lib.paymentoperation import PaymentOperationManager
from stoqlib.lib.parameters import sysparam, ensure_system_parameters
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = Logger('stoqlib.admin')
USER_ADMIN_DEFAULT_NAME = 'admin'

def ensure_admin_user(administrator_password):
    log.info("Creating administrator user")

    conn = get_connection()
    user = get_admin_user(conn)
    if user is None:
        trans = new_transaction()
        person = Person(name='Administrator', connection=trans)

        # Dependencies to create an user.
        role = EmployeeRole(name=_('System Administrator'), connection=trans)
        person.addFacet(IIndividual, connection=trans)
        employee = person.addFacet(IEmployee, role=role, connection=trans)
        EmployeeRoleHistory(connection=trans,
                            role=role,
                            employee=employee,
                            is_active=True,
                            salary=currency(800))

        # This is usefull when testing a initial database. Admin user actually
        # must have all the facets.
        person.addFacet(ISalesPerson, connection=trans)

        profile = UserProfile.selectOneBy(name='Administrator', connection=trans)

        log.info("Attaching IUser facet (%s)" % (USER_ADMIN_DEFAULT_NAME,))
        person.addFacet(IUser, username=USER_ADMIN_DEFAULT_NAME,
                        password=administrator_password,
                        profile=profile, connection=trans)

        trans.commit(close=True)

    # Fetch the user again, this time from the right connection
    user = get_admin_user(conn)
    assert user

    user.password = administrator_password

    # We can't provide the utility until it's actually in the database
    log.info('providing utility ICurrentUser')
    provide_utility(ICurrentUser, user)


def create_main_branch(trans, name):
    """Creates a new branch and sets it as the main branch for the system
    @param trans: a database transaction
    @param name: name of the new branch
    """
    person = Person(name=name, connection=trans)
    person.addFacet(ICompany, connection=trans)
    branch = person.addFacet(IBranch, connection=trans)
    trans.commit()

    sysparam(trans).MAIN_COMPANY = branch.id

    provide_utility(ICurrentBranch, branch)

    return branch


def _register_payment_methods():
    """Registers the payment methods and creates persistent
    domain classes associated with them.
    """
    from stoqlib.domain.payment.method import PaymentMethod
    from stoqlib.domain.payment.operation import register_payment_operations

    pom = PaymentOperationManager()
    provide_utility(IPaymentOperationManager, pom)

    log.info("Registering payment operations")
    register_payment_operations()
    
    trans = new_transaction()
    destination = sysparam(trans).DEFAULT_PAYMENT_DESTINATION

    log.info("Creating domain objects for payment methods")
    for operation_name in pom.get_operation_names():
        operation = pom.get(operation_name)
        pm = PaymentMethod.selectOneBy(connection=trans,
                                       method_name=operation_name)
        if pm is None:
            pm = PaymentMethod(connection=trans,
                               destination=destination,
                               method_name=operation_name,
                               description=None,
                               max_installments=1)
        pm.description = operation.description
        pm.max_installments = operation.max_installments

    trans.commit(close=True)

def get_admin_user(conn):
    """Retrieves the current administrator user for the system
    @param conn: a database connection
    @returns: the admin user for the system
    """
    return Person.iselectOneBy(IUser, username=USER_ADMIN_DEFAULT_NAME,
                               connection=conn)

def ensure_sellable_constants():
    """ Create native sellable constants. """
    log.info("Creating sellable units")
    trans = new_transaction()
    unit_list = [("Kg", UnitType.WEIGHT),
                 ("Lt", UnitType.LITERS),
                 ("m ", UnitType.METERS)]
    for desc, enum in unit_list:
        SellableUnit(description=desc,
                     unit_index=int(enum),
                     connection=trans)

    log.info("Creating sellable tax constants")
    for enum in [TaxType.SUBSTITUTION,
                 TaxType.EXEMPTION,
                 TaxType.NONE,
                 TaxType.SERVICE]:
        desc = describe_constant(enum)
        constant = SellableTaxConstant(description=desc,
                                       tax_type=int(enum),
                                       tax_value=None,
                                       connection=trans)

    trans.commit(close=True)

def user_has_usesuper(trans):
    """This method checks if the currently logged in postgres user has
    `usesuper' access which is necessary for certain operations

    @param trans: a database connection
    @returns: if the user has `usesuper' access
    """

    results = trans.queryOne(
        'SELECT usesuper FROM pg_user WHERE usename=CURRENT_USER')
    return results[0] == 1

def _create_procedural_languages():
    "Creates procedural SQL languages we're going to use in scripts"

    trans = new_transaction()

    log.info('Creating procedural SQL languages')
    results = trans.queryAll('SELECT lanname FROM pg_language')
    languages = [item[0] for item in results]
    if 'plpgsql' in languages:
        return

    if not user_has_usesuper(trans):
        raise StoqlibError(
            "The current database user does not have super user rights")

    # Create the plpgsql language
    trans.query('CREATE LANGUAGE plpgsql')
    trans.commit(close=True)

def create_base_schema():
    log.info('Creating base schema')

    settings = get_utility(IDatabaseSettings)

    log.info('Creating base schema')

    # A Base schema shared between all RDBMS implementations
    schema = environ.find_resource('sql', 'schema-2.sql')
    if execute_sql(schema) != 0:
        error('Failed to create base schema')

    try:
        schema = environ.find_resource('sql', '%s-schema.sql' % settings.rdbms)
        if execute_sql(schema) != 0:
            error('Failed to create %s specific schema' % (settings.rdbms,))
    except EnvironmentError:
        pass

    log.info('Creating views')
    schema = environ.find_resource('sql', 'views.sql')
    if execute_sql(schema) != 0:
        error('Failed to create views schema')

    migration = StoqlibSchemaMigration()
    migration.apply_all_patches()

def create_default_profiles():
    trans = new_transaction()

    log.info("Creating user default profiles")
    UserProfile.create_profile_template(trans, 'Administrator', True)
    UserProfile.create_profile_template(trans, 'Manager', True)
    UserProfile.create_profile_template(trans, 'Salesperson', False)

    trans.commit(close=True)

def _install_invoice_templates():
    log.info("Installing invoice templates")
    importer = InvoiceImporter()
    importer.feed_file(environ.find_resource('csv', 'invoices.csv'))

@argcheck(bool, bool)
def initialize_system(delete_only=False, verbose=False):
    """Call all the necessary methods to startup Stoq applications for
    every purpose: production usage, testing or demonstration
    """

    log.info("Initialize_system(%r, %r)" % (delete_only, verbose))
    settings = get_utility(IDatabaseSettings)
    clean_database(settings.dbname)
    create_base_schema()
    _register_payment_methods()
    ensure_sellable_constants()
    ensure_system_parameters()
    create_default_profiles()
    _install_invoice_templates()
