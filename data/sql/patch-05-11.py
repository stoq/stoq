# -*- coding: utf-8 -*-
creating_types = """
CREATE TYPE payment_status AS ENUM ('preview', 'pending', 'paid',
                                    'reviewing', 'confirmed', 'cancelled');
CREATE TYPE payment_type AS ENUM ('in', 'out');
CREATE TYPE work_order_status AS ENUM ('opened', 'cancelled', 'waiting',
                                       'in-progress', 'finished', 'delivered');
CREATE TYPE work_order_package_status AS ENUM ('opened', 'sent', 'received');
CREATE TYPE credit_card_type AS ENUM ('credit', 'debit', 'credit-inst-store',
                                      'credit-inst-provider', 'debit-pre-dated');
CREATE TYPE payment_category_type AS ENUM ('payable', 'receivable');
CREATE TYPE account_type AS ENUM ('bank', 'cash', 'asset', 'credit',
                                  'income', 'expense', 'equity' );
CREATE TYPE event_type AS ENUM ('system', 'user', 'order', 'sale', 'payment');
CREATE TYPE inventory_status AS ENUM ('open', 'closed', 'cancelled');
CREATE TYPE loan_status AS ENUM ('open', 'closed');
CREATE TYPE credit_check_status AS ENUM ('included', 'not-included');
CREATE TYPE marital_status AS ENUM ('single', 'married', 'divorced',
                                    'widowed', 'separeted', 'cohabitation');
CREATE TYPE individual_gender AS ENUM ('male', 'female');
CREATE TYPE client_status AS ENUM ('solvent', 'indebt', 'insolvent', 'inactive');
CREATE TYPE supplier_status AS ENUM ('active', 'inactive', 'blocked');
CREATE TYPE employee_status AS ENUM ('normal', 'away', 'vacation', 'off');
CREATE TYPE stock_transaction_history_type AS ENUM ('initial', 'sell',
    'returned-sale', 'cancelled-sale', 'received-purchase', 'returned-loan',
    'loan', 'production-allocated', 'production-produced',
    'production-returned', 'stock-decrease', 'transfer-from', 'transfer-to',
    'inventory-adjust', 'production-sent', 'imported', 'consignment-returned',
    'wo-used', 'wo-returned-to-stock', 'sale-reserved');
CREATE TYPE product_quality_test_type AS ENUM ('boolean', 'decimal');
CREATE TYPE production_order_status AS ENUM ('opened', 'waiting', 'producing',
    'closed', 'quality-assurance', 'cancelled');
CREATE TYPE purchase_order_status AS ENUM ('quoting', 'pending', 'confirmed',
                                           'consigned', 'cancelled','closed');
CREATE TYPE purchase_order_freight_type AS ENUM ('fob', 'cif');
CREATE TYPE receiving_order_status AS ENUM ('pending', 'closed');
CREATE TYPE receiving_order_freight_type AS ENUM ('fob-payment', 'fob-installments',
                                            'cif-unknown', 'cif-invoice');
CREATE TYPE delivery_status AS ENUM ('initial', 'sent', 'received');
CREATE TYPE sellable_status AS ENUM ('available', 'closed');
CREATE TYPE stock_decrease_status AS ENUM ('initial', 'confirmed');
CREATE TYPE till_status AS ENUM ('pending', 'open', 'closed');
CREATE TYPE transfer_order_status AS ENUM ('pending', 'sent', 'received');
CREATE TYPE account_transaction_operation_type AS ENUM ('in', 'out');
"""

payment_statuses = {0: 'preview', 1: 'pending', 2: 'paid', 3: 'reviewing',
                    4: 'confirmed', 5: 'cancelled'}
card_types = {0: 'credit', 1: 'debit', 2: 'credit-inst-store',
              3: 'credit-inst-provider', 4: 'debit-pre-dated'}

# table, column, column type, constraint, default value, not null, drop default
tables = [
    ('payment', 'status', 'payment_status',
     'valid_status', 'preview', False, False,
     payment_statuses),
    ('payment', 'payment_type', 'payment_type', 'valid_payment_type', 'in',
     False, False,
     {0: 'in', 1: 'out'}),
    ('work_order', 'status', 'work_order_status',
     'valid_status', 'opened', False, False,
     {0: 'opened', 1: 'cancelled', 2: 'waiting', 3: 'in-progress',
      4: 'finished', 5: 'delivered'}),
    ('work_order_package', 'status', 'work_order_package_status', 'valid_status',
     'opened', True, False,
     {0: 'opened', 1: 'sent', 2: 'received'}),
    ('credit_card_data', 'card_type', 'credit_card_type', 'valid_status',
     'credit', False, False,
     card_types),
    ('card_operation_cost', 'card_type', 'credit_card_type', 'valid_status',
     'credit', False, False,
     card_types),
    ('account', 'account_type', 'account_type', False, 'bank', False, False,
     {0: 'bank', 1: 'cash', 2: 'asset', 3: 'credit', 4: 'income',
      5: 'expense', 6: 'equity'}),
    ('event', 'event_type', 'event_type', False, 'system', True, False,
     {0: 'system', 1: 'user', 2: 'order', 3: 'sale', 4: 'payment'}),
    ('inventory', 'status', 'inventory_status',
     'valid_status', 'open', False, False,
     {0: 'open', 1: 'closed', 2: 'cancelled'}),
    ('loan', 'status', 'loan_status', 'valid_status', 'open', False, False,
     {0: 'open', 1: 'closed'}),
    ('credit_check_history', 'status', 'credit_check_status', 'valid_status',
     'included', True, False,
     {0: 'included', 1: 'not-included'}),
    ('individual', 'marital_status', 'marital_status', 'valid_marital_status',
     'single', False, False,
     {0: 'single', 1: 'married', 2: 'divorced', 3: 'widowed',
      4: 'separeted', 5: 'cohabitation'}),
    ('individual', 'gender', 'individual_gender',
     'valid_gender', 'male', False, False,
     {0: 'male', 1: 'female'}),
    ('client', 'status', 'client_status',
     'valid_status', 'solvent', False, False,
     {0: 'solvent', 1: 'indebt', 2: 'insolvent', 3: 'inactive'}),
    ('supplier', 'status', 'supplier_status',
     'valid_status', 'active', False, False,
     {0: 'active', 1: 'inactive', 2: 'blocked'}),
    ('employee', 'status', 'employee_status',
     'valid_status', 'normal', False, False,
     {0: 'normal', 1: 'away', 2: 'vacation', 3: 'off'}),
    ('stock_transaction_history', 'type', 'stock_transaction_history_type',
     'type_range', 'initial', False, False,
     {0: 'initial', 1: 'sell', 2: 'returned-sale', 3: 'cancelled-sale',
      4: 'received-purchase', 5: 'returned-loan', 6: 'loan',
      7: 'production-allocated', 8: 'production-produced',
      9: 'production-returned', 10: 'stock-decrease', 11: 'transfer-from',
      12: 'transfer-to', 13: 'inventory-adjust', 14: 'production-sent',
      15: 'imported', 16: 'consignment-returned', 17: 'wo-used',
      18: 'wo-returned-to-stock', 19: 'sale-reserved'}),
    ('product_quality_test', 'test_type', 'product_quality_test_type', False,
     'boolean', False, False,
     {0: 'boolean', 1: 'decimal'}),
    ('production_order', 'status', 'production_order_status', 'valid_status',
     'opened', False, False,
     {0: 'opened', 1: 'waiting', 2: 'producing', 3: 'closed',
      4: 'quality-assurance', 5: 'cancelled'}),
    ('purchase_order', 'status', 'purchase_order_status', 'valid_status',
     'quoting', False, False,
     {0: 'cancelled', 1: 'quoting', 2: 'pending', 3: 'confirmed',
      4: 'closed', 5: 'consigned'}),
    ('purchase_order', 'freight_type', 'purchase_order_freight_type',
     'valid_freight_type', 'fob', False, False,
     {0: 'fob', 1: 'cif'}),
    ('receiving_order', 'status', 'receiving_order_status', 'valid_status',
     'pending', False, False,
     {0: 'pending', 1: 'closed'}),
    ('delivery', 'status', 'delivery_status',
     'valid_status', 'initial', False, False,
     {0: 'initial', 1: 'sent', 2: 'received'}),
    ('sellable', 'status', 'sellable_status',
     'valid_status', 'available', False, False,
     {0: 'available', 1: 'closed'}),
    ('stock_decrease', 'status', 'stock_decrease_status', 'valid_status',
     'initial', False, False,
     {0: 'initial', 1: 'confirmed'}),
    ('till', 'status', 'till_status', 'valid_status', 'pending', False, False,
     {0: 'pending', 1: 'open', 2: 'closed'}),
    ('transfer_order', 'status', 'transfer_order_status', 'valid_status',
     'pending', False, False,
     {0: 'pending', 1: 'sent', 2: 'received'}),
    ('payment_change_history', 'last_status', 'payment_status', False,
     'preview', False, False,
     payment_statuses),
    ('payment_change_history', 'new_status', 'payment_status', False,
     'preview', False, False,
     payment_statuses),
    ('payment_category', 'category_type', 'payment_category_type',
     'valid_category_type', 'payable', False, True,
     {0: 'payable', 1: 'receivable'}),
    ('receiving_order', 'freight_type', 'receiving_order_freight_type',
     False, 'fob-payment', False, True,
     {0: 'fob-payment', 1: 'fob-installments', 2: 'cif-unknown', 3: 'cif-invoice'}),
    ('account_transaction', 'operation_type', 'account_transaction_operation_type',
     'valid_operation_type', 'in', False, False,
     {0: 'in', 1: 'out'})
]

base_query = """
ALTER TABLE {table} ADD COLUMN temp_{column} integer;
UPDATE {table} SET temp_{column} = {column};
UPDATE {table} SET {column} = NULL;
ALTER TABLE {table} ALTER COLUMN {column} TYPE {column_type} USING '{new_default}';
"""

updating_query = """
UPDATE {table} SET {column} = '{new_value}' WHERE temp_{column} = {old_value};
"""


def apply_patch(store):
    store.execute(creating_types)
    for (table, column, column_type, constraint,
         new_default, not_null, drop_default, values) in tables:
        query = ""
        # Dropping NOT NULL modifiers
        if not_null:
            query += "ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL;"

        if drop_default:
            query += "ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT;"
        # Dropping the constraint for that column
        if constraint:
            query += "ALTER TABLE {table} DROP CONSTRAINT {constraint};"

        # Updating the values
        query += base_query
        store.execute(query.format(table=table, column=column,
                                   column_type=column_type,
                                   constraint=constraint,
                                   new_default=new_default))

        # Updating the values from integer to the new type
        for old_value, new_value in values.items():
            store.execute(updating_query.format(table=table, column=column,
                                                old_value=old_value,
                                                new_value=new_value))

        # Setting back modifier NOT NULL and remove temp_columns
        query = """
            ALTER TABLE {table} DROP COLUMN temp_{column};
            ALTER TABLE {table} ALTER COLUMN {column} SET NOT NULL;
        """
        if drop_default:
            query += """
                ALTER TABLE {table}
                    ALTER COLUMN {column} SET DEFAULT '{new_default}';
            """
        store.execute(query.format(table=table, column=column,
                                   new_default=new_default))
