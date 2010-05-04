-- IDEALE: Support for payment comment

CREATE TABLE payment_comment (
    id serial NOT NULL PRIMARY KEY,

    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    date timestamp,
    comment text,
    payment_id bigint REFERENCES payment(id),
    author_id bigint REFERENCES person_adapt_to_user(id)
);
