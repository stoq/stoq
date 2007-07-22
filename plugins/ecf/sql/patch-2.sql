-- #3289: Remove is_valid_model from domain classes where it's unused
ALTER TABLE ecf_printer DROP COLUMN is_valid_model;
ALTER TABLE device_constant DROP COLUMN is_valid_model;
