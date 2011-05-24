-- #4361: Create transactions when receiving payments

ALTER TABLE payment DROP COLUMN destination_id;
ALTER TABLE payment_method DROP COLUMN destination_id;
DROP TABLE IF EXISTS credit_provider_group_data;
DROP TABLE IF EXISTS payment_method_details;
DROP TABLE IF EXISTS payment_destination;

ALTER TABLE payment_method ADD COLUMN destination_account_id
  bigint REFERENCES account(id);
UPDATE payment_method SET destination_account_id = (SELECT field_value::int
    FROM parameter_data WHERE field_name = 'IMBALANCE_ACCOUNT');
ALTER TABLE payment_method ALTER COLUMN destination_account_id SET NOT NULL;
