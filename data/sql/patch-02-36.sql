-- FIXME: add to schema-NEXT
CREATE TABLE client_category_price (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    sellable_id bigint REFERENCES sellable(id),
    category_id bigint REFERENCES client_category(id),
    price numeric(10,2) CONSTRAINT positive_price CHECK (price >= 0),
    max_discount numeric(10,2),
    commission numeric(10,2),
    UNIQUE (sellable_id, category_id)
);

ALTER TABLE sale ADD COLUMN client_category_id bigint
    REFERENCES client_category(id);

