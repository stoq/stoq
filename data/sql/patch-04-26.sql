-- Add execution_branch_id columns on work_order
ALTER TABLE work_order
    ADD COLUMN execution_branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE;
