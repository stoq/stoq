-- Add option to set if storables should be reserved automatically

ALTER TABLE optical_product ADD auto_reserve boolean DEFAULT true;
