# -*- coding: utf-8 -*-
# #2126: Initial implementation for work orders (aka "Ordem de serviço" in pt_BR)

from stoqlib.database.properties import UnicodeCol, IntCol, BoolCol
from stoqlib.migration.domainv2 import Domain


class ProfileSettings(Domain):
    __storm_table__ = 'profile_settings'

    app_dir_name = UnicodeCol()
    has_permission = BoolCol(default=False)
    user_profile_id = IntCol()


class UserProfile(Domain):
    __storm_table__ = 'user_profile'

    name = UnicodeCol()

    def add_application_reference(self, app_name, has_permission):
        store = self.store
        ProfileSettings(store=store, app_dir_name=app_name,
                        has_permission=has_permission, user_profile_id=self.id)

    def check_app_permission(self, app_name):
        store = self.store
        return bool(store.find(ProfileSettings, app_dir_name=app_name,
                               user_profile_id=self.id, has_permission=True).one())


_SQL_CMD = """
  -- Update stock_transaction_history. Migrate TYPE_CONSIGNMENT_RETURNED and
  -- alter it's valid range to support it and TYPE_WORK_ORDER_USED.
  ALTER TABLE stock_transaction_history
    DROP CONSTRAINT type_range;
  ALTER TABLE stock_transaction_history
    ADD CONSTRAINT type_range CHECK (type >= 0 and type <= 17);
  UPDATE stock_transaction_history SET type = 16 WHERE type is NULL;

  CREATE TABLE work_order_category (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    name text UNIQUE NOT NULL,
    color text
  );

  CREATE TABLE work_order (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    identifier serial NOT NULL,
    status integer CONSTRAINT valid_status
      CHECK (status >= 0 AND status <= 5),
    equipment text,
    estimated_hours numeric(10,2),
    estimated_cost numeric(20,2),
    estimated_start timestamp,
    estimated_finish timestamp,
    open_date timestamp,
    approve_date timestamp,
    finish_date timestamp,
    defect_reported text,
    defect_detected text,
    branch_id bigint REFERENCES branch(id) ON UPDATE CASCADE,
    quote_responsible_id bigint REFERENCES login_user(id) ON UPDATE CASCADE,
    execution_responsible_id bigint REFERENCES login_user(id) ON UPDATE CASCADE,
    category_id bigint REFERENCES work_order_category(id) ON UPDATE CASCADE,
    client_id bigint REFERENCES client(id) ON UPDATE CASCADE,
    sale_id bigint REFERENCES sale(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
  );

  CREATE TABLE work_order_item (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    quantity numeric(20,3),
    price numeric(20,2),
    sellable_id bigint REFERENCES sellable(id) ON UPDATE CASCADE,
    order_id bigint REFERENCES work_order(id) ON UPDATE CASCADE
  );
  """


def apply_patch(store):
    store.execute(_SQL_CMD)

    # Add permission to anyone with permission to admin or sales
    for profile in store.find(UserProfile):
        has_permission = any([profile.check_app_permission(u'admin'),
                              profile.check_app_permission(u'sales')])
        profile.add_application_reference(u'maintenance', has_permission)
