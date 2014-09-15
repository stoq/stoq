# -*- coding: utf-8 -*-
creating_types = """
CREATE TYPE device_constant_type AS ENUM ('unit', 'tax', 'payment');
CREATE TYPE fiscal_sale_history_document_type AS ENUM ('cpf', 'cnpj');
CREATE TYPE ecf_document_history_type AS ENUM ('memory-read', 'z-reduction',
                                               'summary');
"""

# table, column, column type, constraint, default value, drop default
tables = [
    ('device_constant', 'constant_type', 'device_constant_type',
     'valid_constant_type', 'unit', False,
     {0: 'unit', 1: 'tax', 2: 'payment'}),
    ('fiscal_sale_history', 'document_type', 'fiscal_sale_history_document_type',
     'valid_type', 'cpf', True,
     {0: 'cpf', 1: 'cnpj'}),
    ('ecf_document_history', 'type', 'ecf_document_history_type',
     'valid_type', 'memory-read', False,
     {0: 'memory-read', 1: 'z-reduction', 2: 'summary'}),
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
         new_default, drop_default, values) in tables:
        query = ""

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
