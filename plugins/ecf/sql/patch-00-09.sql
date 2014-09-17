ALTER TABLE ecf_printer ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE ecf_document_history ALTER COLUMN te_id SET DEFAULT new_te();

CREATE RULE update_te AS ON UPDATE TO ecf_printer DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO ecf_document_history DO ALSO SELECT update_te(old.te_id);

