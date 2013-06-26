-- #5559: Add new columns to product.

ALTER TABLE product ADD COLUMN brand text;

ALTER TABLE product ADD COLUMN family text;

-- leftover from patch 03-18
ALTER TABLE product DROP COLUMN manufacturer;
