-- Rename column ids for person references
ALTER TABLE branch RENAME COLUMN original_id TO person_id;
ALTER TABLE client RENAME COLUMN original_id TO person_id;
ALTER TABLE company RENAME COLUMN original_id TO person_id;
ALTER TABLE credit_provider RENAME COLUMN original_id TO person_id;
ALTER TABLE employee RENAME COLUMN original_id TO person_id;
ALTER TABLE individual RENAME COLUMN original_id TO person_id;
ALTER TABLE login_user RENAME COLUMN original_id TO person_id;
ALTER TABLE sales_person RENAME COLUMN original_id TO person_id;
ALTER TABLE supplier RENAME COLUMN original_id TO person_id;
ALTER TABLE transporter RENAME COLUMN original_id TO person_id;
