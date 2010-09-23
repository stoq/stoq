-- Manual stock decrease

CREATE TABLE stock_decrease (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    confirm_date timestamp,
    status integer CONSTRAINT valid_status CHECK (status >= 0 AND status < 8),
    reason text,
    notes text,
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    removed_by_id bigint REFERENCES person_adapt_to_employee(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);


CREATE TABLE stock_decrease_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    stock_decrease_id bigint REFERENCES stock_decrease(id),
    sellable_id bigint REFERENCES sellable(id)
);


ALTER TABLE product_history
    ADD COLUMN decreased_date timestamp,
    ADD COLUMN quantity_decreased numeric(10, 2)
        CONSTRAINT positive_decreased CHECK (quantity_decreased > 0);

