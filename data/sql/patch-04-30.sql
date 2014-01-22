-- #5559: Add new columns to product.

ALTER TABLE product ADD COLUMN brand text;

ALTER TABLE product ADD COLUMN family text;

-- Manufacturer column was removed in patch 03-18, but the schema 04 was creating that column.
ALTER TABLE product DROP COLUMN IF EXISTS manufacturer;
