# -*- coding: utf-8 -*-

# #2301: Financial application
from stoqlib.database.admin import register_accounts
from stoqlib.domain.profile import ProfileSettings

def apply_patch(trans):
    profiles = ProfileSettings.selectBy(app_dir_name='admin',
                                        connection=trans)
    for profile in profiles:
        ProfileSettings(app_dir_name='financial',
                       has_permission=profile.has_permission,
                       user_profile=profile.user_profile,
                       connection=trans)

    trans.query("""
CREATE TABLE account (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    description text NOT NULL,
    code text,
    parent_id bigint REFERENCES account(id),
    station_id bigint REFERENCES branch_station(id)
);""")

    trans.query("""
CREATE TABLE account_transaction (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    description text,
    code text,
    value numeric(10, 3) CONSTRAINT nonzero_value CHECK (value != 0),
    source_account_id bigint REFERENCES account(id) NOT NULL,
    account_id bigint REFERENCES account(id) NOT NULL,
    date timestamp NOT NULL,
    payment_id bigint REFERENCES payment(id)
);""")

    # Patch 2-30 introduces this
    try:
        from stoqlib.domain.account import Account
        Account.sqlmeta.delColumn('account_type')
    except KeyError:
        pass

    register_accounts(trans)
