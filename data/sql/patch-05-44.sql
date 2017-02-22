-- Fixing typo on marital_status -> enum('separeted')
UPDATE pg_enum SET enumlabel = 'separated' WHERE enumlabel='separeted';

-- Adding NULL option on individual_gender
ALTER TABLE individual ALTER COLUMN gender DROP NOT NULL;
ALTER TABLE individual ALTER COLUMN gender SET DEFAULT NULL;
