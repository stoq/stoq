
ALTER TABLE person_adapt_to_branch
    ADD COLUMN crt integer DEFAULT 1;

ALTER TABLE sale
    ADD COLUMN operation_nature text;
