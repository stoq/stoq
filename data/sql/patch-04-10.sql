-- bug 5376 - Centro de custos

CREATE TABLE cost_center (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    name text NOT NULL,
    description text,
    budget numeric(20, 2) CONSTRAINT positive_budget CHECK (budget >= 0)
);

CREATE TABLE cost_center_entry (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    cost_center_id bigint NOT NULL UNIQUE REFERENCES cost_center(id) ON UPDATE CASCADE,
    payment_id bigint UNIQUE REFERENCES payment(id) ON UPDATE CASCADE,
    stock_transaction_id bigint UNIQUE REFERENCES stock_transaction_history(id)
        ON UPDATE CASCADE
);
