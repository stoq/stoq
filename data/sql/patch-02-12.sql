-- Add removed_by column in loan table

ALTER TABLE loan ADD COLUMN removed_by text;
