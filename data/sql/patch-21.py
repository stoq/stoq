# #3487: Don't inherit from InheritableModel for Fiscal book entries

def apply_patch(trans):
    for view_name in ['icms_ipi_view', 'iss_view']:
        if trans.viewExists(view_name):
            trans.dropView(view_name)

    if trans.tableExists('fiscal_book_entry'):
        return

    table_name = 'abstract_fiscal_book_entry'
    if not trans.tableHasColumn(table_name, 'ipi_value'):
        for column in [
            'entry_type integer',
            'te_created_id bigint REFERENCES transaction_entry(id)',
            'te_modified_id bigint REFERENCES transaction_entry(id)',
            'icms_value numeric(10,2)',
            'iss_value numeric(10,2)',
            'ipi_value numeric(10,2)']:
            trans.query("ALTER TABLE %s ADD COLUMN %s" % (table_name, column))

    trans.query("""
UPDATE abstract_fiscal_book_entry
   SET te_created_id = inheritable_model.te_created_id,
       te_modified_id = inheritable_model.te_modified_id
  FROM inheritable_model
 WHERE inheritable_model.child_name = 'AbstractFiscalBookEntry';
DELETE FROM inheritable_model WHERE child_name = 'AbstractFiscalBookEntry';

UPDATE abstract_fiscal_book_entry
   SET entry_type = 0,
       icms_value = icms_ipi_book_entry.icms_value,
       ipi_value = icms_ipi_book_entry.ipi_value
  FROM icms_ipi_book_entry
 WHERE abstract_fiscal_book_entry.id = icms_ipi_book_entry.id;

UPDATE abstract_fiscal_book_entry
   SET entry_type = 1,
       iss_value = iss_book_entry.iss_value
  FROM iss_book_entry
 WHERE abstract_fiscal_book_entry.id = iss_book_entry.id;""")

    trans.query("""
ALTER TABLE abstract_fiscal_book_entry DROP COLUMN child_name;
DROP TABLE icms_ipi_book_entry;
DROP TABLE iss_book_entry;
ALTER TABLE abstract_fiscal_book_entry RENAME TO fiscal_book_entry;
ALTER TABLE abstract_fiscal_book_entry_id_seq RENAME TO fiscal_book_entry_id_seq;
""")
