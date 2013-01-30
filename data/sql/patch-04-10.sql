-- bug 5376 - Centro de custos
-- bug 5378 - Registrar transação em centro de custo para saídas de estoque

CREATE TABLE cost_center (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    name text NOT NULL,
    description text,
    budget numeric(20, 2) CONSTRAINT positive_budget CHECK (budget >= 0),
    is_active boolean NOT NULL DEFAULT TRUE
);

CREATE TABLE cost_center_entry (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    cost_center_id bigint NOT NULL REFERENCES cost_center(id) ON UPDATE CASCADE,
    payment_id bigint UNIQUE REFERENCES payment(id) ON UPDATE CASCADE,
    stock_transaction_id bigint UNIQUE REFERENCES stock_transaction_history(id)
        ON UPDATE CASCADE,
    CONSTRAINT stock_transaction_or_payment
        CHECK ((payment_id IS NULL AND stock_transaction_id IS NOT NULL) OR
               (payment_id IS NOT NULL AND stock_transaction_id IS NULL))
);

ALTER TABLE sale
    ADD COLUMN cost_center_id bigint REFERENCES cost_center(id);

ALTER TABLE stock_decrease
    ADD COLUMN cost_center_id bigint REFERENCES cost_center(id);
