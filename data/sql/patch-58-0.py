#3813: Make a new schema generation

# Set the invalid values for te_created_id and te_modified_id to null.
# Such invalid values came from last schema changes and data migration.

def apply_patch(trans):
    columns = ["te_created_id", "te_modified_id"]
    tables = ['sellable',
              'sale_item',
              'product_stock_item',
              'payment_destination',
              'payment_method',
              'commission_source',
              'commission',
              'transfer_order',
              'transfer_order_item',
              'invoice_layout',
              'invoice_field',
              'invoice_printer',
              'inventory',
              'inventory_item',]
    for table in tables:
        for column in columns:
            trans.query("""
UPDATE %s SET %s = NULL
 WHERE %s IN (SELECT %s FROM %s GROUP BY %s HAVING COUNT(%s) > 1);
""" % (table, column, column, column, table, column, column))
