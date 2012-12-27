# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from stoqlib.database.settings import db_settings


def apply_patch(store):
    #
    # ADDING AN IDENTIFIER COLUMN.
    #

    # The id column is for internal use only, and when we need to show a
    # numeric representation of an object, we should use the identifier

    #: these are the tables that reference branch.
    tables = ['sale', 'payment_renegotiation', 'purchase_order',
              'receiving_order', 'inventory', 'production_order', 'loan',
              'stock_decrease', 'payment', 'till_entry', 'quote_group',
              'quotation']

    # This may be executed by a different user that created the database.
    # We cannot recreate the sequence if the table belongs to a different user.
    # We also have to commmit the transaction so the changes take effect
    query = '''ALTER TABLE %(table)s OWNER TO "%(user)s";'''
    for t in tables + ['transfer_order']:
        store.execute(query % dict(table=t, user=db_settings.username))
    store.commit()

    query = """
        ALTER TABLE %(table)s ADD COLUMN identifier serial;
        UPDATE %(table)s SET identifier = id;
        ALTER TABLE %(table)s ALTER identifier SET NOT NULL;
        ALTER TABLE %(table)s ADD CONSTRAINT %(table)s_identifier_key
             UNIQUE (identifier, branch_id);
        SELECT SETVAL('%(table)s_identifier_seq',
                      (SELECT max(identifier) from %(table)s));
    """

    for t in tables:
        store.execute(query % dict(table=t))

    #
    # FIXING TRANSFER_ORDER SPECIAL CASE
    #

    query = """
        ALTER TABLE transfer_order ADD COLUMN identifier serial;
        UPDATE transfer_order SET identifier = id;
        ALTER TABLE transfer_order ALTER identifier SET NOT NULL;
        ALTER TABLE transfer_order ADD CONSTRAINT transfer_order_identifier_key
             UNIQUE (identifier, source_branch_id, destination_branch_id);
        SELECT SETVAL('transfer_order_identifier_seq',
                      (SELECT max(identifier) from transfer_order));
    """
    store.execute(query)
