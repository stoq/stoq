-- #3372: Add a reference to a Branch in Sale.
ALTER TABLE sale ADD COLUMN branch_id bigint
     REFERENCES person_adapt_to_branch(id);
