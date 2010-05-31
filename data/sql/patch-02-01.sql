ALTER TABLE purchase_order
    ADD COLUMN product_type integer default 0 CONSTRAINT valid_product_type CHECK (product_type >= 0 and product_type < 2);
