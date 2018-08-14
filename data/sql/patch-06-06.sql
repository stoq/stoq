ALTER TABLE work_order
    ADD COLUMN check_responsible_id UUID REFERENCES employee(id) ON UPDATE CASCADE;
