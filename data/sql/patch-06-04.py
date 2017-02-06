# -*- coding: utf-8 -*-

# Note to whoever will create schema-07: some tables are missing the update_te rule:
# product_cofins_template
# product_pis_template
# invoice_item_pis
# invoice_item_cofins


query = """
ALTER TABLE {table} ALTER COLUMN te_id SET DEFAULT new_te('{table}');
CREATE OR REPLACE RULE update_te AS ON UPDATE TO {table} DO ALSO SELECT
  update_te(old.te_id, '{table}');
"""

rules_query = """
-- Returns a default te_id for the domain tables
CREATE OR REPLACE FUNCTION new_te(table_name text DEFAULT '') RETURNS integer AS $$
    DECLARE te_id integer;
BEGIN
    INSERT INTO transaction_entry (te_time) VALUES (STATEMENT_TIMESTAMP()) RETURNING id INTO te_id;
    PERFORM pg_notify('new_te', te_id::text || ',' || table_name);
    RETURN te_id;
END;
$$ LANGUAGE plpgsql;

-- Updates the transaction entry for the given id
CREATE OR REPLACE FUNCTION update_te(te_id bigint, table_name text DEFAULT '') RETURNS void AS $$
BEGIN
    UPDATE transaction_entry SET te_time = STATEMENT_TIMESTAMP(), sync_status = DEFAULT
        WHERE id = $1;
    PERFORM pg_notify('update_te', te_id::text || ',' || table_name);
END;
$$ LANGUAGE plpgsql;
"""

tables_query = """
SELECT c.relname as rule_table
FROM pg_rewrite r JOIN pg_class c ON r.ev_class = c.oid
WHERE r.rulename = 'update_te';
"""


def apply_patch(store):
    store.execute(rules_query)
    tables = store.execute(tables_query).get_all()

    for (table,) in tables + [('product_cofins_template',), ('invoice_item_pis',),
                              ('invoice_item_cofins',), ('product_pis_template',)]:
        store.execute(query.format(table=table))

    # Drop the old functions
    store.execute("""
        DROP FUNCTION new_te();
        DROP FUNCTION update_te(bigint);
    """)
