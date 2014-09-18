# -*- coding: utf-8 -*-
creating_types = """
CREATE TYPE optical_product_type AS ENUM ('glass-frame', 'glass-lenses',
                                                  'contact-lenses');
CREATE TYPE optical_work_order_lens_type AS ENUM ('ophtalmic', 'contact');
CREATE TYPE optical_work_order_frame_type AS ENUM ('closed-ring', 'nylon',
                                                   '3-pieces');
CREATE TYPE optical_patient_history_user_type AS ENUM ('first-user', 'second-user',
                                             'ex-user');
CREATE TYPE optical_patient_measures_dominant_eye AS ENUM ('left', 'right');
"""

# table, column, column type, default value, drop_default
tables = [
    ('optical_product', 'optical_type', 'optical_product_type',
     'glass-frame', False,
     {0: 'glass-frame', 1: 'glass-lenses', 2: 'contact-lenses'}),
    ('optical_work_order', 'lens_type', 'optical_work_order_lens_type',
     'ophtalmic', False,
     {0: 'ophtalmic', 1: 'contact'}),
    ('optical_work_order', 'frame_type', 'optical_work_order_frame_type',
     'closed-ring', False,
     {0: 'closed-ring', 1: 'nylon', 2: '3-pieces'}),
    ('optical_patient_history', 'user_type', 'optical_patient_history_user_type',
     'first-user', True,
     {0: 'first-user', 1: 'second-user', 2: 'ex-user'}),
    ('optical_patient_measures', 'dominant_eye',
     'optical_patient_measures_dominant_eye', 'left', True,
     {0: 'left', 1: 'right'}),
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
    for (table, column, column_type, new_default, drop_default, values) in tables:
        query = ""
        # Dropping DEFAULT value modifier
        if drop_default:
            query += "ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT;"

        # Updating the values
        query += base_query
        store.execute(query.format(table=table, column=column,
                                   column_type=column_type,
                                   new_default=new_default))

        # Updating the values from integer to the new type
        for old_value, new_value in values.items():
            store.execute(updating_query.format(table=table, column=column,
                                                old_value=old_value,
                                                new_value=new_value))

        # Setting back DEFAULT values and remove temp_columns
        query = """
            ALTER TABLE {table} DROP COLUMN temp_{column};
        """
        if drop_default:
            query += """
                ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT '{new_default}';
            """
        store.execute(query.format(table=table, column=column,
                                   new_default=new_default))
