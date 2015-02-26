CREATE TYPE returned_sale_status AS ENUM ('pending', 'confirmed');
ALTER TABLE returned_sale
    ADD COLUMN status returned_sale_status,
    ADD COLUMN confirm_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    ADD COLUMN confirm_date timestamp;
