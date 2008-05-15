-- 3606: Wizard para criação de produto composto

CREATE TABLE product_component (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    product_id bigint REFERENCES product(id),
    component_id bigint REFERENCES product(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT different_products CHECK (product_id != component_id)
);
