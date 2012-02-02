ALTER TABLE payment_category ADD COLUMN category_type integer;
UPDATE payment_category SET category_type = 0 WHERE category_type IS NULL;
ALTER TABLE payment_category ADD CONSTRAINT valid_category_type
     CHECK (category_type >= 0 AND category_type <= 1);
