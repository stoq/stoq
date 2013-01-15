# -*- coding: utf-8 -*-

from stoqlib.database.admin import register_accounts
from stoqlib.database.properties import IntCol
from stoqlib.domain.account import Account


def apply_patch(store):
    store.execute("""ALTER TABLE account ADD COLUMN account_type int;""")

    # We need to add back the account_type column removed in 2-27
    try:
        Account.sqlmeta.addColumn(IntCol('account_type', default=None))
    except KeyError:
        pass

    # Register the accounts again to set the account_type
    register_accounts(store)
