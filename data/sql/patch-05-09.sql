-- Invert the source and destination accounts where transactions have negative values.
-- Before, the selected account when confirm a payment, was saved as source account.
-- Now, for negative values, the selected account must be save as destination.
UPDATE account_transaction SET account_id = source_account_id, source_account_id = account_id
    WHERE value < 0;

ALTER TABLE account_transaction ADD COLUMN operation_type integer
    CONSTRAINT valid_operation_type CHECK(operation_type IN (0,1));

UPDATE account_transaction set operation_type = 0 where value > 0;
UPDATE account_transaction set operation_type = 1 where value < 0;

-- Convert negative values to positive
UPDATE account_transaction SET value = abs(value) WHERE value < 0;

ALTER TABLE account_transaction DROP CONSTRAINT nonzero_value;
ALTER TABLE account_transaction ADD CONSTRAINT positive_value CHECK(value >= 0);
