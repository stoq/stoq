-- Bug 3884 - Adicionar renegociação de dívidas.

CREATE TABLE payment_renegotiation (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    open_date timestamp,
    close_date timestamp,
    status integer CONSTRAINT valid_status CHECK (status >= 0 AND status < 3),
    discount_value numeric(10,2) CONSTRAINT positive_discount_value CHECK (discount_value >= 0),
    surcharge_value numeric(10,2) CONSTRAINT positive_surcharge_value CHECK (surcharge_value >= 0),
    total numeric(10, 2) CONSTRAINT positive_total CHECK (total >= 0),
    notes text,
    client_id bigint REFERENCES person_adapt_to_client(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    group_id bigint REFERENCES payment_group(id)
);

ALTER TABLE sale DROP CONSTRAINT valid_status;

ALTER TABLE sale ADD CONSTRAINT valid_status
    CHECK (status >= 0 AND status < 8);

ALTER TABLE payment_group
    ADD COLUMN renegotiation_id bigint REFERENCES payment_renegotiation(id);
