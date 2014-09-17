ALTER TABLE book_publisher ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE book ALTER COLUMN te_id SET DEFAULT new_te();

CREATE RULE update_te AS ON UPDATE TO book_publisher DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO book DO ALSO SELECT update_te(old.te_id);

