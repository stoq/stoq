--

ALTER TABLE sale ADD COLUMN invoice_number integer DEFAULT NULL UNIQUE
    CONSTRAINT positive_invoice_number CHECK (invoice_number > 0 AND invoice_number < 999999);
