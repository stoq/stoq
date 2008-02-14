-- #3066: Implementar opção de alteracao da data de vencimento Contas a
-- Receber.

-- create payment_due_date_info table
CREATE TABLE payment_due_date_info (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    due_date_change_reason text,
    last_due_date timestamp,
    change_date timestamp,
    payment_id bigint REFERENCES payment(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id)
);
