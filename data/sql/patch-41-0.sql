-- #3683: Add support for payment categories

-- Create payment_category
CREATE TABLE payment_category (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text UNIQUE,
    color text
);

ALTER TABLE payment ADD COLUMN category_id bigint 
      REFERENCES payment_category(id);
