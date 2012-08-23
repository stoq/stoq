# XXX
# Some tables (like branch) are weak referenced by parameters.
# Changing the id would break the parameter

#: Gets all foreign key references.
#: The ref_table is the referenced table. The other 3 columns are the constraint
#: name, the table that references ref_table, and the column that has the
#: reference to ref_table.id
# Based on queries from http://stackoverflow.com/questions/5347050/sql-to-list-all-the-tables-that-reference-a-particular-column-in-a-table
query = """
SELECT ccu.table_name as ref_table, rc.constraint_name,
       tc.table_name AS table_name, kcu.column_name
FROM information_schema.referential_constraints AS rc
    JOIN information_schema.table_constraints AS tc
    USING(constraint_catalog, constraint_schema, constraint_name)
    JOIN information_schema.key_column_usage AS kcu
    USING(constraint_catalog, constraint_schema, constraint_name)
    JOIN information_schema.key_column_usage AS ccu
    ON(ccu.constraint_catalog=rc.unique_constraint_catalog
        AND ccu.constraint_schema=rc.unique_constraint_schema
        AND ccu.constraint_name=rc.unique_constraint_name)
WHERE ccu.table_name != 'transaction_entry' AND ccu.column_name='id';
"""

#: This query will remove the old constraint and recreate it as is, but with ON
#: UPDATE CASCADE
fix_query = """
ALTER TABLE %(table_name)s DROP CONSTRAINT %(const_name)s;
ALTER TABLE %(table_name)s ADD CONSTRAINT %(const_name)s
    FOREIGN KEY (%(column_name)s) REFERENCES %(ref_table)s(id) ON UPDATE CASCADE;
"""


def apply_patch(trans):
    references = trans.queryAll(query)

    for (ref_table, constraint_name, table_name, column_name) in references:
        trans.query(fix_query % dict(table_name=table_name,
                                     const_name=constraint_name,
                                     column_name=column_name,
                                     ref_table=ref_table))
