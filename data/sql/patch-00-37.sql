-- #3596: empty address street number should be allowed
ALTER TABLE address DROP CONSTRAINT positive_number;
ALTER TABLE address RENAME COLUMN number TO streetnumber;
ALTER TABLE address ADD CONSTRAINT positive_streetnumber CHECK (streetnumber > 0);
