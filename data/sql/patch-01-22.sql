-- #3603: Implementar esqueleto inicial da aplicação de produção.

CREATE TABLE production_order (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    status integer CONSTRAINT valid_status CHECK (status >= 0 AND status < 4),
    open_date timestamp,
    close_date timestamp,
    description text,
    responsible_id bigint REFERENCES person_adapt_to_employee(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);
