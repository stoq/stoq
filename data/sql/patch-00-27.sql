-- #2258: Implementar diálogo de transferência de estoque

CREATE TABLE transfer_order (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    open_date timestamp NOT NULL,
    receival_date timestamp,

    source_branch_id bigint NOT NULL REFERENCES person_adapt_to_branch(id),
    destination_branch_id bigint NOT NULL REFERENCES person_adapt_to_branch(id),
    source_responsible_id bigint NOT NULL REFERENCES person_adapt_to_employee(id),
    destination_responsible_id bigint NOT NULL REFERENCES person_adapt_to_employee(id)
    );

CREATE TABLE transfer_order_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    sellable_id bigint NOT NULL REFERENCES asellable(id),
    transfer_order_id bigint NOT NULL REFERENCES transfer_order(id),
    quantity numeric(10,2) NOT NULL CONSTRAINT positive_quantity CHECK (quantity > 0)
    );
