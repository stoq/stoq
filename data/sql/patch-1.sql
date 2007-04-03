-- #2752: Rework database migration
DELETE FROM system_table;
ALTER TABLE system_table ADD COLUMN generation integer;
ALTER TABLE system_table RENAME COLUMN version TO patchlevel;
ALTER TABLE system_table RENAME COLUMN update_date TO updated;
