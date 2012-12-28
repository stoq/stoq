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

from kiwi.component import provide_utility
from kiwi.currency import currency
from kiwi.environ import environ
from kiwi.log import Logger

from stoqdrivers.enum import TaxType, UnitType
from stoqdrivers.constants import describe_constant

from stoqlib.database.interfaces import ICurrentBranch, ICurrentUser
from stoqlib.database.migration import StoqlibSchemaMigration
from stoqlib.database.orm import const
from stoqlib.database.runtime import get_default_store, new_store
from stoqlib.database.settings import db_settings
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

    default_store = get_default_store()
    user = get_admin_user(default_store)

    if user is None:
        store = new_store()
        person = Person(name=_('Administrator'), store=store)

        # Dependencies to create an user.
        role = EmployeeRole(name=_('System Administrator'), store=store)
        Individual(person=person, store=store)
        employee = Employee(person=person, role=role, store=store)
        EmployeeRoleHistory(store=store,
                            role=role,
                            employee=employee,
                            is_active=True,
                            salary=currency(800))

        # This is usefull when testing a initial database. Admin user actually
        # must have all the facets.
        SalesPerson(person=person, store=store)

        profile = store.find(UserProfile, name=_('Administrator')).one()
        # Backwards compatibility. this profile used to be in english
        # FIXME: Maybe its safe to assume the first profile in the table is
        # the admin.
        if not profile:
            profile = store.find(UserProfile, name='Administrator').one()

        log.info("Attaching a LoginUser (%s)" % (USER_ADMIN_DEFAULT_NAME, ))
        LoginUser(person=person,
                  username=USER_ADMIN_DEFAULT_NAME,
                  password=administrator_password,
                  profile=profile, store=store)

        store.commit(close=True)

    # Fetch the user again, this time from the right connection
    user = get_admin_user(default_store)
    assert user

    user.set_password(administrator_password)

    # We can't provide the utility until it's actually in the database
    log.info('providing utility ICurrentUser')
    provide_utility(ICurrentUser, user)


def create_main_branch(store, name):
    """Creates a new branch and sets it as the main branch for the system
    :param store: a store
    :param name: name of the new branch
    """
    person = Person(name=name, store=store)
    Company(person=person, store=store)
    branch = Branch(person=person, store=store)

    sysparam(store).MAIN_COMPANY = branch.id

    provide_utility(ICurrentBranch, branch)
    admin = get_admin_user(store.store)
    admin.add_access_to(branch)

    return branch


def populate_initial_data(store):
    from stoqlib.domain.system import SystemTable
    generation = SystemTable.select(store=store).max(SystemTable.q.generation)
    if generation < 4:
        # FIXME: Initial data can (and needs to) only be sourced on schemas
        #        greater or equal than 4. Remove this in the future.
        return

    log.info('Populating initial data')
    initial_data = environ.find_resource('sql', 'initial.sql')
    if db_settings.execute_sql(initial_data) != 0:
        error('Failed to populate initial data')


def register_payment_methods(store):
    """Registers the payment methods and creates persistent
    domain classes associated with them.
    """
    from stoqlib.domain.payment.method import PaymentMethod
    from stoqlib.domain.payment.operation import get_payment_operation_manager

    log.info("Registering payment operations")
    pom = get_payment_operation_manager()

    log.info("Creating domain objects for payment methods")
    account = sysparam(store).IMBALANCE_ACCOUNT
    for operation_name in pom.get_operation_names():
        operation = pom.get(operation_name)
        pm = store.find(PaymentMethod, method_name=operation_name).one()
        if pm is None:
            pm = PaymentMethod(store=store,
                               method_name=operation_name,
                               destination_account=account,
                               max_installments=operation.max_installments)


def register_accounts(store):
    # FIXME: If you need to run this in a patch, you need to
    #        make sure that .find().one() is fixed bellow, as accounts
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
        # FIXME: This needs to rewritten to not use .find().one(),
        #        see comment above.
        account = store.find(Account, description=name).one()
        if not account:
            account = Account(store=store, description=name)
        account.account_type = atype

    sparam = sysparam(store)
    sparam.BANKS_ACCOUNT = store.find(Account, description=_("Banks")).one().id
    sparam.TILLS_ACCOUNT = store.find(Account, description=_("Tills")).one().id
    sparam.IMBALANCE_ACCOUNT = store.find(Account,
                                          description=_("Imbalance")).one().id


def _ensure_card_providers():
    """ Creates a list of default card providers """
    log.info("Creating Card Providers")
    from stoqlib.domain.person import CreditProvider

    providers = ['VISANET', 'REDECARD', 'AMEX', 'HIPERCARD',
                 'BANRISUL', 'PAGGO', 'CREDISHOP', 'CERTIF']

    store = new_store()
    for name in providers:
        person = CreditProvider.get_provider_by_provider_id(
                        name, store)
        if not person.is_empty():
            continue

        person = Person(name=name, store=store)
        Company(person=person, store=store)
        CreditProvider(person=person,
                       short_name=name,
                       provider_id=name,
                       open_contract_date=const.NOW(),
                       store=store)
    store.commit(close=True)


def get_admin_user(store):
    """Retrieves the current administrator user for the system
    :param store:  store
    :returns: the admin user for the system
    """
    return store.find(LoginUser,
                      username=USER_ADMIN_DEFAULT_NAME).one()


def ensure_sellable_constants():
    """ Create native sellable constants. """
    log.info("Creating sellable units")
    store = new_store()
    unit_list = [("Kg", UnitType.WEIGHT),
                 ("Lt", UnitType.LITERS),
                 ("m ", UnitType.METERS)]
    for desc, enum in unit_list:
        SellableUnit(description=desc,
                     unit_index=int(enum),
                     store=store)

    log.info("Creating sellable tax constants")
    for enum in [TaxType.SUBSTITUTION,
                 TaxType.EXEMPTION,
                 TaxType.NONE,
                 TaxType.SERVICE]:
        desc = describe_constant(enum)
        SellableTaxConstant(description=desc,
                            tax_type=int(enum),
                            tax_value=None,
                            store=store)

    store.commit(close=True)


def user_has_usesuper(store):
    """This method checks if the currently logged in postgres user has
    ``usesuper`` access which is necessary for certain operations

    :param store: a store
    :returns: if the user has ``usesuper`` access
    """

    results = store.execute(
        'SELECT usesuper FROM pg_user WHERE usename=CURRENT_USER').get_one()
    return results[0] == 1


def _create_procedural_languages():
    "Creates procedural SQL languages we're going to use in scripts"

    store = new_store()
    store = store.store
    log.info('Creating procedural SQL languages')
    results = store.execute('SELECT lanname FROM pg_language').get_all()
    languages = [item[0] for item in results]
    if 'plpgsql' in languages:
        return

    if not user_has_usesuper(store):
        raise StoqlibError(
            _("The current database user does not have super user rights"))

    # Create the plpgsql language
    store.execute('CREATE LANGUAGE plpgsql')
    store.commit()
    store.close()


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

    # Functions
    functions = environ.find_resource('sql', 'functions.sql')
    if db_settings.execute_sql(functions) != 0:
        error('Failed to create functions')

    # A Base schema shared between all RDBMS implementations
    schema = _get_latest_schema()
    if db_settings.execute_sql(schema) != 0:
        error('Failed to create base schema')

    try:
        schema = environ.find_resource('sql', '%s-schema.sql' % db_settings.rdbms)
        if db_settings.execute_sql(schema) != 0:
            error('Failed to create %s specific schema' % (db_settings.rdbms, ))
    except EnvironmentError:
        pass

    migration = StoqlibSchemaMigration()
    migration.apply_all_patches()


def create_default_profiles():
    store = new_store()

    log.info("Creating user default profiles")
    UserProfile.create_profile_template(store, _('Administrator'), True)
    UserProfile.create_profile_template(store, _('Manager'), True)
    UserProfile.create_profile_template(store, _('Salesperson'), False)

    store.commit(close=True)


def create_default_profile_settings():
    store = new_store()
    profile = store.find(UserProfile, name=_('Salesperson')).one()
    # Not sure what is happening. If it doesnt exist, check if it was not
    # created in english. workaround for crash report 207 (bug 4587)
    if not profile:
        profile = store.find(UserProfile, name='Salesperson').one()
    assert profile
    ProfileSettings.set_permission(store, profile, 'pos', True)
    ProfileSettings.set_permission(store, profile, 'sales', True)
    ProfileSettings.set_permission(store, profile, 'till', True)
    store.commit(close=True)


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
        db_settings.clean_database(db_settings.dbname, force=force)
        create_base_schema()
        create_log("INIT START")
        store = new_store()
        populate_initial_data(store)
        register_accounts(store)
        register_payment_methods(store)
        from stoqlib.domain.uiform import create_default_forms
        create_default_forms(store)
        store.commit(close=True)
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
