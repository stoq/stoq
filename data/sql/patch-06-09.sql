ALTER TABLE individual
    ADD COLUMN responsible_id uuid REFERENCES individual(id) ON UPDATE CASCADE;
