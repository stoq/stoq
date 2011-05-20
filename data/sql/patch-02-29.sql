-- #4361: Create transactions when receiving payments

ALTER TABLE payment DROP COLUMN destination_id;
ALTER TABLE payment_method DROP COLUMN destination_id;
DROP TABLE credit_provider_group_data;
DROP TABLE payment_method_details;
DROP TABLE payment_destination;

ALTER TABLE payment_method ADD COLUMN destination_account_id
  bigint NOT NULL REFERENCES account(id);
