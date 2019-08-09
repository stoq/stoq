CREATE TABLE access_token (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1() NOT NULL,
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    token text UNIQUE NOT NULL,
    issue_date timestamp NOT NULL,
    revoked boolean DEFAULT FALSE,
    user_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,
    station_id uuid NOT NULL REFERENCES branch_station(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO access_token DO ALSO SELECT update_te(old.te_id, 'access_token');
