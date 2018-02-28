ALTER TABLE payment_category ADD account_id uuid REFERENCES account(id) ON UPDATE CASCADE;
