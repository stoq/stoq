-- Create loan and loan_item tables.

CREATE TABLE  loan (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    open_date timestamp,
    close_date timestamp,
    expire_date timestamp,
    status integer CONSTRAINT valid_status CHECK (status >= 0 AND status < 6),
    notes text,
    client_id bigint REFERENCES person_adapt_to_client(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE loan_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    sale_quantity numeric(10,2) CONSTRAINT positive_sale_quantity CHECK (sale_quantity >= 0),
    return_quantity numeric(10,2) CONSTRAINT positive_return_quantity CHECK (return_quantity >= 0),
    price numeric(10,2) CONSTRAINT positive_price CHECK (price >= 0),
    loan_id bigint REFERENCES loan(id),
    sellable_id bigint REFERENCES sellable(id)
);
