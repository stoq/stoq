-- FIXME: add to schema-NEXT
CREATE TABLE event (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp NOT NULL,
    event_type integer NOT NULL,
    description varchar NOT NULL
);

