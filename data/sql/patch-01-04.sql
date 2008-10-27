CREATE TABLE credit_card_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    payment_id bigint UNIQUE REFERENCES payment(id),
    card_type integer CONSTRAINT valid_status CHECK (card_type >= 0 AND card_type < 5),
    provider_id bigint REFERENCES person_adapt_to_credit_provider(id)
);

ALTER TABLE person_adapt_to_credit_provider
    ADD COLUMN payment_day integer
    CONSTRAINT valid_payment_day CHECK (payment_day <= 28);

ALTER TABLE person_adapt_to_credit_provider
    ADD COLUMN closing_day integer
    CONSTRAINT valid_closing_day CHECK (closing_day <= 28);

ALTER TABLE person_adapt_to_credit_provider
    ADD COLUMN max_installments integer
    CONSTRAINT valid_installments CHECK (closing_day > 0);

UPDATE person_adapt_to_credit_provider
    SET closing_day = 10, payment_day = 10,
        max_installments=12;
