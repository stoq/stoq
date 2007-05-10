-- #3218: Geração de arquivo para sintegra
CREATE TABLE fiscal_day_history (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    emission_date date CONSTRAINT past_emission_date CHECK (emission_date <= DATE(NOW())),
    device_id bigint REFERENCES device_settings(id),
    serial text,
    serial_id integer,
    coupon_start integer CONSTRAINT positive_coupon_start CHECK (coupon_start > 0),
    coupon_end integer CONSTRAINT positive_coupon_end CHECK (coupon_end > 0),
    cro integer CONSTRAINT positive_cro CHECK (cro > 0),
    crz integer CONSTRAINT positive_crz CHECK (crz > 0),
    period_total numeric(10, 2) CONSTRAINT positive_period_total CHECK (period_total >= 0),
    total numeric(10, 2) CONSTRAINT positive_total CHECK (total >= 0),
    tax_total numeric(10, 2) CONSTRAINT positive_tax_total CHECK (tax_total >= 0),
    CONSTRAINT coupon_start_lower_than_coupon_end CHECK (coupon_start <= coupon_end)
);

CREATE TABLE fiscal_day_tax (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    code text CONSTRAINT valid_code CHECK (code ~ '^([0-9][0-9][0-9][0-9]|I|F|N|ISS|DESC|CANC)$'),
    value numeric(10, 2) CONSTRAINT positive_value CHECK (value >= 0),
    fiscal_day_history_id bigint REFERENCES fiscal_day_history(id)
);

