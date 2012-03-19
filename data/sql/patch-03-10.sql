ALTER TABLE product_adapt_to_storable RENAME TO storable;
ALTER SEQUENCE product_adapt_to_storable_id_seq RENAME TO storable_id_seq;

ALTER TABLE storable RENAME COLUMN original_id TO product_id;
