ALTER TABLE product_component
    ADD COLUMN price numeric(20, 2),
    ADD CONSTRAINT positive_price CHECK(price >= 0);

-- FIXME update schema-next
