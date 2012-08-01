-- Increase invoice_number's lenght from 6 to 9 digits.

-- sale
ALTER TABLE sale DROP CONSTRAINT positive_invoice_number;
ALTER TABLE sale ADD CONSTRAINT valid_invoice_number
    CHECK (invoice_number > 0 AND invoice_number < 999999999);

-- receiving_order
ALTER TABLE receiving_order DROP CONSTRAINT valid_invoice_number;
ALTER TABLE receiving_order ADD CONSTRAINT valid_invoice_number
    CHECK (invoice_number > 0 AND invoice_number < 999999999);

-- renegotiation_data
UPDATE renegotiation_data SET invoice_number = NULL
    WHERE invoice_number <= 0 or invoice_number >= 999999999;
ALTER TABLE renegotiation_data ADD CONSTRAINT valid_invoice_number
    CHECK (invoice_number > 0 AND invoice_number < 999999999);

-- inventory
ALTER TABLE inventory DROP CONSTRAINT positive_invoice_number;
ALTER TABLE inventory ADD CONSTRAINT valid_invoice_number
    CHECK (invoice_number > 0 AND invoice_number < 999999999);

-- Drop payment_method's description column as it's not used anymore
ALTER TABLE payment_method DROP COLUMN description;
