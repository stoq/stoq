ALTER TABLE sale_token ADD COLUMN name text;
ALTER TABLE sale_token ADD COLUMN branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE;
ALTER TABLE sale_token ADD COLUMN sale_id uuid REFERENCES sale(id) ON UPDATE CASCADE;
