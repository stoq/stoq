-- #3302: Add a tax constant to SellableCategory
ALTER TABLE sellable_category ADD COLUMN tax_constant_id bigint REFERENCES sellable_tax_constant(id);
