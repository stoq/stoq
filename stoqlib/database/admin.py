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
import logging
import os
import tempfile

from kiwi.component import provide_utility
from kiwi.currency import currency
from kiwi.environ import environ

from stoqdrivers.enum import TaxType, UnitType
from stoqdrivers.constants import describe_constant

from stoqlib.database.expr import TransactionTimestamp
from stoqlib.database.interfaces import ICurrentBranch, ICurrentUser
from stoqlib.database.migration import StoqlibSchemaMigration
from stoqlib.database.runtime import get_default_store, new_store
from stoqlib.database.settings import db_settings
from stoqlib.domain.person import (Branch, Company, Employee, EmployeeRole,
                                   Individual, LoginUser, Person, SalesPerson)
from stoqlib.domain.person import EmployeeRoleHistory
from stoqlib.domain.profile import ProfileSettings, UserProfile
from stoqlib.domain.sellable import SellableTaxConstant, SellableUnit
from stoqlib.exceptions import StoqlibError
from stoqlib.importers.invoiceimporter import InvoiceImporter
from stoqlib.lib.message import error
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.template import render_template_string
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = logging.getLogger(__name__)
create_log = logging.getLogger('stoqlib.database.create')
USER_ADMIN_DEFAULT_NAME = u'admin'


def ensure_admin_user(administrator_password):
    log.info("Creating administrator user")

    default_store = get_default_store()
    user = get_admin_user(default_store)

    if user is None:
        store = new_store()
        person = Person(name=_(u'Administrator'), store=store)

        # Dependencies to create an user.
        role = EmployeeRole(name=_(u'System Administrator'), store=store)
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

        profile = store.find(UserProfile, name=_(u'Administrator')).one()
        # Backwards compatibility. this profile used to be in english
        # FIXME: Maybe its safe to assume the first profile in the table is
        # the admin.
        if not profile:
            profile = store.find(UserProfile, name=u'Administrator').one()

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

    sysparam.set_object(store, 'MAIN_COMPANY', branch)

    provide_utility(ICurrentBranch, branch)
    admin = get_admin_user(store)
    admin.add_access_to(branch)

    return branch


def populate_initial_data(store):
    from stoqlib.domain.system import SystemTable
    generation = store.find(SystemTable).max(SystemTable.generation)
    if generation < 4:
        # FIXME: Initial data can (and needs to) only be sourced on schemas
        #        greater or equal than 4. Remove this in the future.
        return

    log.info('Populating initial data')
    initial_data = environ.get_resource_filename('stoq', 'sql', 'initial.sql')
    if db_settings.execute_sql(initial_data) != 0:
        error(u'Failed to populate initial data')


def register_payment_methods(store):
    """Registers the payment methods and creates persistent
    domain classes associated with them.
    """
    from stoqlib.domain.payment.method import PaymentMethod
    from stoqlib.domain.payment.operation import get_payment_operation_manager

    log.info("Registering payment operations")
    pom = get_payment_operation_manager()

    log.info("Creating domain objects for payment methods")
    account_id = sysparam.get_object_id('IMBALANCE_ACCOUNT')
    assert account_id
    for operation_name in pom.get_operation_names():
        operation = pom.get(operation_name)
        pm = store.find(PaymentMethod, method_name=operation_name).one()
        if pm is None:
            pm = PaymentMethod(store=store,
                               method_name=operation_name,
                               destination_account_id=account_id,
                               max_installments=operation.max_installments)


def register_accounts(store):
    # FIXME: If you need to run this in a patch, you need to
    #        make sure that .find().one() is fixed bellow, as accounts
    #        with the same names are allowed.
    #        It's for now okay to run this when creating a new
    #        database.

    from stoqlib.domain.account import Account
    log.info("Creating Accounts")
    for name, atype in [(_(u"Assets"), Account.TYPE_ASSET),
                        (_(u"Banks"), Account.TYPE_BANK),
                        (_(u"Equity"), Account.TYPE_EQUITY),
                        (_(u"Expenses"), Account.TYPE_EXPENSE),
                        (_(u"Imbalance"), Account.TYPE_BANK),
                        (_(u"Income"), Account.TYPE_INCOME),
                        (_(u"Tills"), Account.TYPE_CASH),
                        ]:
        # FIXME: This needs to rewritten to not use .find().one(),
        #        see comment above.
        account = store.find(Account, description=name).one()
        if not account:
            account = Account(store=store, description=name)
        account.account_type = atype

    sysparam.set_object(
        store,
        'BANKS_ACCOUNT',
        store.find(Account, description=_(u"Banks")).one())
    sysparam.set_object(
        store,
        'TILLS_ACCOUNT',
        store.find(Account, description=_(u"Tills")).one())
    sysparam.set_object(
        store,
        'IMBALANCE_ACCOUNT',
        store.find(Account, description=_(u"Imbalance")).one())


def _ensure_card_providers():
    """ Creates a list of default card providers """
    log.info("Creating Card Providers")
    from stoqlib.domain.payment.card import CreditProvider, CardPaymentDevice

    providers = [u'VISANET', u'REDECARD', u'AMEX', u'HIPERCARD',
                 u'BANRISUL', u'PAGGO', u'CREDISHOP', u'CERTIF']

    store = new_store()
    for name in providers:
        provider = CreditProvider.get_provider_by_provider_id(name, store)
        if not provider.is_empty():
            continue

        CreditProvider(short_name=name,
                       provider_id=name,
                       open_contract_date=TransactionTimestamp(),
                       store=store)
    devices = store.find(CardPaymentDevice)
    if devices.is_empty():
        CardPaymentDevice(store=store, description=_(u'Default'))
    store.commit(close=True)


def get_admin_user(store):
    """Retrieves the current administrator user for the system
    :param store:  store
    :returns: the admin user for the system
    """
    return store.find(LoginUser,
                      username=USER_ADMIN_DEFAULT_NAME).one()


def ensure_sellable_constants(store):
    """ Create native sellable constants. """
    log.info("Creating sellable units")
    unit_list = [(u"Kg", UnitType.WEIGHT),
                 (u"Lt", UnitType.LITERS),
                 (u"m ", UnitType.METERS)]
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
    resource = environ.get_resource_filename('stoq', 'sql')
    for filename in glob.glob(os.path.join(resource, schema_pattern)):
        schemas.append(filename)
    assert schemas
    schemas.sort()
    return schemas[-1]


def create_database_functions():
    """Create some functions we define on the database

    This will simply read data/sql/functions.sql and execute it
    """
    with tempfile.NamedTemporaryFile(suffix='stoqfunctions-') as tmp_f:
        functions = environ.get_resource_string('stoq', 'sql', 'functions.sql')
        tmp_f.write(render_template_string(functions))
        tmp_f.flush()
        if db_settings.execute_sql(tmp_f.name) != 0:
            error(u'Failed to create functions')


def create_base_schema():
    log.info('Creating base schema')
    create_log.info("SCHEMA")

    create_database_functions()

    # A Base schema shared between all RDBMS implementations
    schema = _get_latest_schema()
    if db_settings.execute_sql(schema) != 0:
        error(u'Failed to create base schema')

    migration = StoqlibSchemaMigration()
    migration.apply_all_patches()


def create_default_profiles():
    store = new_store()

    log.info("Creating user default profiles")
    UserProfile.create_profile_template(store, _(u'Administrator'), True)
    UserProfile.create_profile_template(store, _(u'Manager'), True)
    UserProfile.create_profile_template(store, _(u'Salesperson'), False)

    store.commit(close=True)


def create_default_profile_settings():
    store = new_store()
    profile = store.find(UserProfile, name=_(u'Salesperson')).one()
    # Not sure what is happening. If it doesnt exist, check if it was not
    # created in english. workaround for crash report 207 (bug 4587)
    if not profile:
        profile = store.find(UserProfile, name=u'Salesperson').one()
    assert profile
    ProfileSettings.set_permission(store, profile, u'pos', True)
    ProfileSettings.set_permission(store, profile, u'sales', True)
    ProfileSettings.set_permission(store, profile, u'till', True)
    store.commit(close=True)


def _install_invoice_templates():
    log.info("Installing invoice templates")
    importer = InvoiceImporter()
    importer.feed_file(environ.get_resource_filename('stoq', 'csv', 'invoices.csv'))
    importer.process()


def initialize_system(password=None, testsuite=False,
                      force=False, empty=False):
    """Call all the necessary methods to startup Stoq applications for
    every purpose: production usage, testing or demonstration
    :param force: When False, we will ask the user if he really wants to replace
      the existing database.
    :param empty: If we should create the database without any data. When we do
      this the database will not be really usable by stoq. This should be used
      to create a database for the syncronization server.
    """

    log.info("Initialize_system")
    try:
        db_settings.clean_database(db_settings.dbname, force=force)
        create_base_schema()
        create_log.info("INIT START")
        store = new_store()
        if not empty:
            populate_initial_data(store)
            register_accounts(store)
            register_payment_methods(store)
            from stoqlib.domain.uiform import create_default_forms
            create_default_forms(store)
            ensure_sellable_constants(store)
            sysparam.ensure_system_parameters(store)
            store.commit(close=True)
            _ensure_card_providers()
            create_default_profiles()
            _install_invoice_templates()

            if not testsuite:
                create_default_profile_settings()
                ensure_admin_user(password)
    except Exception:
        # if not testsuite:
        #     collect_traceback(sys.exc_info(), submit=True)
        # raise SystemExit("Could not initialize system: %r" % (e, ))
        raise
    create_log.info("INIT DONE")
