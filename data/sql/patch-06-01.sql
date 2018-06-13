COMMIT;
ALTER TYPE till_status ADD VALUE 'verified';
BEGIN;

ALTER TABLE till ADD COLUMN verify_date timestamp;
ALTER TABLE till ADD COLUMN responsible_verify_id uuid REFERENCES login_user(id) ON UPDATE CASCADE;

CREATE TABLE till_summary (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    system_value numeric(20, 2) CONSTRAINT positive_system_value CHECK (system_value >= 0),
    user_value numeric(20, 2) CONSTRAINT positive_user_value CHECK (user_value >= 0),
    verify_value numeric(20, 2) CONSTRAINT positive_verify_value CHECK (verify_value >= 0),
    card_type credit_card_type,
    provider_id uuid REFERENCES credit_provider(id) ON UPDATE CASCADE,
    method_id uuid not null REFERENCES payment_method(id) ON UPDATE CASCADE,
    till_id uuid NOT NULL REFERENCES till(id) ON UPDATE CASCADE,
    -- We cannot create repeated entries for the same till
    UNIQUE (till_id, method_id, provider_id, card_type)
);
CREATE RULE update_te AS ON UPDATE TO till_summary DO ALSO SELECT update_te(old.te_id);
