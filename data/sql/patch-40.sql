-- #3671 Add more information to z-reduction tables.

ALTER TABLE fiscal_day_history ADD COLUMN reduction_date timestamp;

-- For the entries that we don't have this information, set it to the last minute of the day.
UPDATE fiscal_day_history
    SET reduction_date = emission_date + interval '23:59 hours'
    WHERE reduction_date IS NULL;

ALTER TABLE fiscal_day_tax ADD COLUMN type text;

UPDATE fiscal_day_tax
    SET type = 'ISS' WHERE code = 'ISS';

UPDATE fiscal_day_tax
    SET type = 'ICMS' WHERE code != 'ISS';
