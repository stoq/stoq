-- #3358: Sale rewrite
ALTER TABLE sale ADD COLUMN return_date timestamp;
ALTER TABLE renegotiation_data ADD COLUMN sale_id bigint UNIQUE REFERENCES sale(id);
ALTER TABLE sale
    DROP CONSTRAINT valid_status,
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 6);
ALTER TABLE sale DROP COLUMN renegotiation_data_id;

DROP TABLE renegotiation_adapt_to_change_installments;
DROP TABLE renegotiation_adapt_to_exchange;
DROP TABLE renegotiation_adapt_to_return_sale;
DROP TABLE abstract_renegotiation_adapter;
