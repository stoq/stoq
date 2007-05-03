CREATE TABLE product_history (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity_sold numeric(10, 2) CONSTRAINT positive_quantity_sold CHECK (quantity_sold >= 0),
    quantity_received numeric(10, 2) CONSTRAINT positive_quantity_received CHECK (quantity_received >= 0),
    sold_date timestamp,
    received_date timestamp,
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    sellable_id bigint REFERENCES asellable(id)
);
