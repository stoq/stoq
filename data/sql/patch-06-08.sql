CREATE TABLE message (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    content text DEFAULT '',
    created_at timestamp DEFAULT NOW(),
    expire_at timestamp,
    created_by_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,
    user_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    profile_id uuid REFERENCES user_profile(id) ON UPDATE CASCADE,
    branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE
);

CREATE RULE update_te AS ON UPDATE TO message DO ALSO SELECT update_te(old.te_id);
