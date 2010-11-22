--Create cards_taxes - bug4201

-- Before, provider_fee had percentual data type
-- With this change, monthly_fee has monetary data type
ALTER TABLE person_adapt_to_credit_provider
    RENAME COLUMN provider_fee TO monthly_fee;

ALTER TABLE person_adapt_to_credit_provider
    ADD COLUMN credit_fee numeric(10, 2) NOT NULL DEFAULT 0
    CONSTRAINT valid_credit_fee CHECK (credit_fee >= 0 AND credit_fee <= 100),
    ADD COLUMN debit_fee numeric(10, 2) NOT NULL DEFAULT 0
    CONSTRAINT valid_debit_fee CHECK (debit_fee >= 0 AND debit_fee <= 100),
    ADD COLUMN credit_installments_store_fee numeric(10, 2) NOT NULL DEFAULT 0
    CONSTRAINT valid_installments_store_fee CHECK (credit_installments_store_fee >= 0 AND credit_installments_store_fee <= 100),
    ADD COLUMN credit_installments_provider_fee numeric(10, 2) NOT NULL DEFAULT 0
    CONSTRAINT valid_installments_provider_fee CHECK (credit_installments_provider_fee >= 0 AND credit_installments_provider_fee <= 100),
    ADD COLUMN debit_pre_dated_fee numeric(10, 2) NOT NULL DEFAULT 0
    CONSTRAINT positive_debit_pre_dated CHECK (debit_pre_dated_fee >= 0 AND debit_pre_dated_fee <= 100);

ALTER TABLE credit_card_data
    ADD COLUMN fee numeric(10, 2) NOT NULL DEFAULT 0,
    ADD COLUMN fee_value numeric(10, 2) DEFAULT 0;
