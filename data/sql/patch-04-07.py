# Migrating transaction_entry data to new format.


def apply_patch(store):
    consts = store.execute("""
        SELECT table_name, constraint_name FROM information_schema.key_column_usage
         WHERE column_name = 'te_modified_id' OR column_name = 'te_created_id';
    """).get_all()

    recreate = []

    for table, constraint_name in consts:

        if constraint_name.endswith('_te_created_id_fkey'):
            # Remove the te_created_id from all columns
            store.execute("ALTER TABLE %s DROP COLUMN te_created_id" % (table,),
                          noresult=True)

            # Flag the objects that are really used, so we can remove obsolete
            # transaction entries latter (these are entries from objects that wore
            # probably removed)
            query = """UPDATE transaction_entry t SET type = 3
                      FROM %(table)s o WHERE o.te_modified_id = t.id;
             """ % dict(table=table)
            store.execute(query)

        elif constraint_name.endswith('_te_modified_id_key'):
            # Rename the index to reflect new name
            new_constraint_name = constraint_name.replace('te_modified_id', 'te_id')
            q = """ALTER INDEX %s RENAME TO %s""" % (constraint_name, new_constraint_name)
            store.execute(q, noresult=True)
        elif constraint_name.endswith('_te_modified_id_fkey'):
            # Rename table_te_modified_id_fkey > table_te_id_fkey
            store.execute("ALTER TABLE %s DROP CONSTRAINT %s" %
                          (table, constraint_name), noresult=True)
            recreate.append((table, constraint_name))

    store.execute('DELETE FROM transaction_entry WHERE type != 3;', noresult=True)
    store.execute('ALTER TABLE transaction_entry DROP COLUMN "type";', noresult=True)
    store.execute('''ALTER TABLE transaction_entry
                     ADD COLUMN dirty boolean DEFAULT true;''', noresult=True)

    # Recreate the constraints after the delete, otherwise that operation may
    # take a really long time
    for table, constraint_name in recreate:
        # Rename te_modified_id to te_id
        store.execute('ALTER TABLE %s RENAME te_modified_id TO te_id' % table,
                      noresult=True)

        new_constraint_name = constraint_name.replace('te_modified_id', 'te_id')
        q = """ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (te_id)
               REFERENCES transaction_entry(id)""" % (table, new_constraint_name)
        store.execute(q, noresult=True)

    store.commit()
