CREATE TYPE returned_sale_status AS ENUM ('pending', 'confirmed', 'cancelled');
ALTER TABLE returned_sale
    ADD COLUMN status returned_sale_status,
    ADD COLUMN confirm_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    ADD COLUMN confirm_date timestamp,
    ADD COLUMN undo_date timestamp,
    ADD COLUMN undo_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    ADD COLUMN undo_reason text;
UPDATE returned_sale SET confirm_responsible_id = responsible_id, confirm_date = return_date, status='confirmed';
