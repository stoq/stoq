-- #3778: Criar grupo de cotação

CREATE TABLE quote_group (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
);


CREATE TABLE purchase_order_adapt_to_quote (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    original_id bigint REFERENCES purchase_order(id),
    group_id bigint REFERENCES quote_group(id)
);
