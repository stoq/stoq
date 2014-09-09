ALTER TABLE book_publisher ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE book ALTER COLUMN te_id SET DEFAULT new_te();
