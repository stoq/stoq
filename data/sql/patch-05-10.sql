ALTER TABLE sale ADD COLUMN paid boolean default False;
UPDATE sale SET paid = True WHERE status = 2;

UPDATE sale SET status = 1 WHERE status = 2;

ALTER TABLE sale DROP CONSTRAINT valid_status;

CREATE TYPE sale_status AS ENUM ('initial', 'quote', 'ordered', 'confirmed',
                                 'cancelled', 'returned', 'renegotiated');
-- Copying the column status, reset its value and change the type of column
ALTER TABLE sale ADD COLUMN temp_status integer;
UPDATE sale SET temp_status = status;
UPDATE sale SET status = NULL;
ALTER TABLE sale ALTER COLUMN status TYPE sale_status USING 'initial';

-- Setting back the column status with its new value
UPDATE sale SET status = 'quote' WHERE temp_status = 6;
UPDATE sale SET status = 'ordered' WHERE temp_status = 4;
UPDATE sale SET status = 'confirmed' WHERE temp_status = 1;
UPDATE sale SET status = 'cancelled' WHERE temp_status = 3;
UPDATE sale SET status = 'returned' WHERE temp_status = 5;
UPDATE sale SET status = 'renegotiated' WHERE temp_status = 7;

-- Removing the temporary column created.
ALTER TABLE sale DROP COLUMN temp_status;
ALTER TABLE sale ALTER COLUMN status SET NOT NULL;
