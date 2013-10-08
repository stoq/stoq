ALTER TABLE work_order RENAME COLUMN equipment TO description;
ALTER TABLE work_order ADD COLUMN sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE;
