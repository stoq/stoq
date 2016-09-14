ALTER TABLE product
    ADD COLUMN yield_quantity numeric(20, 3) DEFAULT 1,
    ADD CONSTRAINT positive_yield CHECK(yield_quantity >= 0);
