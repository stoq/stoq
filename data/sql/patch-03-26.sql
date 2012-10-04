CREATE TABLE credit_check_history (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    creation_date timestamp,
    check_date timestamp,
    identifier text,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 2),
    notes text,
    client_id bigint REFERENCES client(id) ON UPDATE CASCADE,
    user_id bigint REFERENCES login_user(id) ON UPDATE CASCADE
);

