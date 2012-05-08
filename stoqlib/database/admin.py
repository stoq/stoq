# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Administration

Helper functions related to administration of the database, creating
tables, removing tables and configuring administration user.
"""

import glob
import os
import sys

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
from stoqlib.database.orm import const
from stoqlib.database.runtime import get_connection, new_transaction
from stoqlib.domain.person import (Branch, Company, Employee, EmployeeRole,
                                   Individual, LoginUser, Person, SalesPerson)
from stoqlib.domain.person import EmployeeRoleHistory
from stoqlib.domain.profile import ProfileSettings, UserProfile
from stoqlib.domain.sellable import SellableTaxConstant, SellableUnit
from stoqlib.exceptions import StoqlibError
from stoqlib.importers.invoiceimporter import InvoiceImporter
from stoqlib.lib.crashreport import collect_traceback
from stoqlib.lib.message import error
from stoqlib.lib.parameters import sysparam, ensure_system_parameters
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = Logger('stoqlib.admin')
create_log = Logger('stoqlib.database.create')
USER_ADMIN_DEFAULT_NAME = 'admin'


def ensure_admin_user(administrator_password):
    log.info("Creating administrator user")

    conn = get_connection()
    user = get_admin_user(conn)
    if user is None:
        trans = new_transaction()
        person = Person(name=_('Administrator'), connection=trans)

        # Dependencies to create an user.
        role = EmployeeRole(name=_('System Administrator'), connection=trans)
        Individual(person=person, connection=trans)
        employee = Employee(person=person, role=role, connection=trans)
        EmployeeRoleHistory(connection=trans,
                            role=role,
                            employee=employee,
                            is_active=True,
                            salary=currency(800))

        # This is usefull when testing a initial database. Admin user actually
        # must have all the facets.
        SalesPerson(person=person, connection=trans)

        profile = UserProfile.selectOneBy(name=_('Administrator'), connection=trans)
        # Backwards compatibility. this profile used to be in english
        # FIXME: Maybe its safe to assume the first profile in the table is
        # the admin.
        if not profile:
            profile = UserProfile.selectOneBy(name='Administrator', connection=trans)

        log.info("Attaching a LoginUser (%s)" % (USER_ADMIN_DEFAULT_NAME, ))
        LoginUser(person=person,
                  username=USER_ADMIN_DEFAULT_NAME,
                  password=administrator_password,
                  profile=profile, connection=trans)

        trans.commit(close=True)

    # Fetch the user again, this time from the right connection
    user = get_admin_user(conn)
    assert user

    user.set_password(administrator_password)

    # We can't provide the utility until it's actually in the database
    log.info('providing utility ICurrentUser')
    provide_utility(ICurrentUser, user)


def create_main_branch(trans, name):
    """Creates a new branch and sets it as the main branch for the system
    :param trans: a database transaction
    :param name: name of the new branch
    """
    person = Person(name=name, connection=trans)
    Company(person=person, connection=trans)
    branch = Branch(person=person, connection=trans)
    trans.commit()

    sysparam(trans).MAIN_COMPANY = branch.id

    provide_utility(ICurrentBranch, branch)

    return branch


def register_payment_methods(trans):
    """Registers the payment methods and creates persistent
    domain classes associated with them.
    """
    from stoqlib.domain.payment.method import PaymentMethod
    from stoqlib.domain.payment.operation import get_payment_operation_manager

    log.info("Registering payment operations")
    pom = get_payment_operation_manager()

    log.info("Creating domain objects for payment methods")
    account = sysparam(trans).IMBALANCE_ACCOUNT
    for operation_name in pom.get_operation_names():
        operation = pom.get(operation_name)
        pm = PaymentMethod.selectOneBy(connection=trans,
                                       method_name=operation_name)
        if pm is None:
            pm = PaymentMethod(connection=trans,
                               method_name=operation_name,
                               description=None,
                               destination_account=account,
                               max_installments=1)
        pm.description = operation.description
        pm.max_installments = operation.max_installments


def register_accounts(trans):
    # FIXME: If you need to run this in a patch, you need to
    #        make sure that selectOneBy is fixed, as accounts
    #        with the same names are allowed.
    #        It's for now okay to run this when creating a new
    #        database.

    from stoqlib.domain.account import Account
    log.info("Creating Accounts")
    for name, atype in [(_("Assets"), Account.TYPE_ASSET),
                        (_("Banks"), Account.TYPE_BANK),
                        (_("Equity"), Account.TYPE_EQUITY),
                        (_("Expenses"), Account.TYPE_EXPENSE),
                        (_("Imbalance"), Account.TYPE_BANK),
                        (_("Income"), Account.TYPE_INCOME),
                        (_("Tills"), Account.TYPE_CASH),
                        ]:
        # FIXME: This needs to rewritten to not use selectOneBy,
        #        see comment above.
        account = Account.selectOneBy(connection=trans,
                                      description=name)
        if not account:
            account = Account(connection=trans,
                              description=name)
        account.account_type = atype

    sparam = sysparam(trans)
    sparam.BANKS_ACCOUNT = Account.selectOneBy(
        connection=trans, description=_("Banks")).id
    sparam.TILLS_ACCOUNT = Account.selectOneBy(
        connection=trans, description=_("Tills")).id
    sparam.IMBALANCE_ACCOUNT = Account.selectOneBy(
        connection=trans, description=_("Imbalance")).id


def _ensure_card_providers():
    """ Creates a list of default card providers """
    log.info("Creating Card Providers")
    from stoqlib.domain.person import CreditProvider

    providers = ['VISANET', 'REDECARD', 'AMEX', 'HIPERCARD',
                 'BANRISUL', 'PAGGO', 'CREDISHOP', 'CERTIF']

    trans = new_transaction()
    for name in providers:
        person = CreditProvider.get_provider_by_provider_id(
                        name, trans)
        if person:
            continue

        person = Person(name=name, connection=trans)
        Company(person=person, connection=trans)
        CreditProvider(person=person,
                       short_name=name,
                       provider_id=name,
                       open_contract_date=const.NOW(),
                       connection=trans)
    trans.commit(close=True)


def get_admin_user(conn):
    """Retrieves the current administrator user for the system
    :param conn: a database connection
    :returns: the admin user for the system
    """
    return LoginUser.selectOneBy(username=USER_ADMIN_DEFAULT_NAME,
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
        SellableTaxConstant(description=desc,
                            tax_type=int(enum),
                            tax_value=None,
                            connection=trans)

    trans.commit(close=True)


def user_has_usesuper(trans):
    """This method checks if the currently logged in postgres user has
    `usesuper' access which is necessary for certain operations

    :param trans: a database connection
    :returns: if the user has `usesuper' access
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
            _("The current database user does not have super user rights"))

    # Create the plpgsql language
    trans.query('CREATE LANGUAGE plpgsql')
    trans.commit(close=True)


def _get_latest_schema():
    schema_pattern = "schema-??.sql"
    schemas = []
    for resource in environ.get_resource_paths("sql"):
        for filename in glob.glob(os.path.join(resource, schema_pattern)):
            schemas.append(filename)
    assert schemas
    schemas.sort()
    return schemas[-1]


def create_base_schema():
    log.info('Creating base schema')
    create_log.info("SCHEMA")
    settings = get_utility(IDatabaseSettings)

    # Functions
    functions = environ.find_resource('sql', 'functions.sql')
    if execute_sql(functions) != 0:
        error('Failed to create functions')

    # A Base schema shared between all RDBMS implementations
    schema = _get_latest_schema()
    if execute_sql(schema) != 0:
        error('Failed to create base schema')

    try:
        schema = environ.find_resource('sql', '%s-schema.sql' % settings.rdbms)
        if execute_sql(schema) != 0:
            error('Failed to create %s specific schema' % (settings.rdbms, ))
    except EnvironmentError:
        pass

    migration = StoqlibSchemaMigration()
    migration.apply_all_patches()


def create_default_profiles():
    trans = new_transaction()

    log.info("Creating user default profiles")
    UserProfile.create_profile_template(trans, _('Administrator'), True)
    UserProfile.create_profile_template(trans, _('Manager'), True)
    UserProfile.create_profile_template(trans, _('Salesperson'), False)

    trans.commit(close=True)


def create_default_profile_settings():
    trans = new_transaction()
    profile = UserProfile.selectOneBy(name=_('Salesperson'), connection=trans)
    # Not sure what is happening. If it doesnt exist, check if it was not
    # created in english. workaround for crash report 207 (bug 4587)
    if not profile:
        profile = UserProfile.selectOneBy(name='Salesperson', connection=trans)
    assert profile
    ProfileSettings.set_permission(trans, profile, 'pos', True)
    ProfileSettings.set_permission(trans, profile, 'sales', True)
    ProfileSettings.set_permission(trans, profile, 'till', True)
    trans.commit(close=True)


def _install_invoice_templates():
    log.info("Installing invoice templates")
    importer = InvoiceImporter()
    importer.feed_file(environ.find_resource('csv', 'invoices.csv'))
    importer.process()


def initialize_system(password=None, testsuite=False,
                      force=False):
    """Call all the necessary methods to startup Stoq applications for
    every purpose: production usage, testing or demonstration
    """

    log.info("Initialize_system")
    try:
        settings = get_utility(IDatabaseSettings)
        clean_database(settings.dbname, force=force)
        create_base_schema()
        create_log("INIT START")
        trans = new_transaction()
        register_accounts(trans)
        register_payment_methods(trans)
        from stoqlib.domain.uiform import create_default_forms
        create_default_forms(trans)
        trans.commit(close=True)
        ensure_sellable_constants()
        ensure_system_parameters()
        _ensure_card_providers()
        create_default_profiles()
        _install_invoice_templates()

        if not testsuite:
            create_default_profile_settings()
            ensure_admin_user(password)
    except Exception, e:
        raise
        if not testsuite:
            collect_traceback(sys.exc_info(), submit=True)
        raise SystemExit("Could not initialize system: %r" % (e, ))
    create_log("INIT DONE")
