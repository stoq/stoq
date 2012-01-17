-- #2263: Suporte para impressão de boletos bancarios
ALTER TABLE bank_account RENAME COLUMN account TO bank_account;
ALTER TABLE bank_account RENAME COLUMN bank_id TO bank_number;
ALTER TABLE bank_account RENAME COLUMN branch TO bank_branch;
ALTER TABLE bank_account ADD COLUMN account_id bigint UNIQUE REFERENCES account(id);
ALTER TABLE bank_account ADD COLUMN bank_type bigint;

DROP TABLE person_adapt_to_bank_branch;
DROP TABLE bank;

CREATE TABLE bill_option (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    option text,
    value text,
    bank_account_id bigint REFERENCES bank_account(id)
);

ALTER TABLE check_data RENAME COLUMN bank_data_id TO bank_account_id;
