commit;
ALTER TYPE delivery_status ADD VALUE 'picked';
ALTER TYPE delivery_status ADD VALUE 'packed';
ALTER TYPE delivery_status ADD VALUE 'cancelled';
begin;

CREATE TYPE delivery_freight_type AS ENUM ('cif', 'fob', '3rdparty');

ALTER TABLE delivery
ADD COLUMN freight_type delivery_freight_type DEFAULT 'cif',
ADD COLUMN volumes_kind text,
ADD COLUMN volumes_quantity integer,
ADD COLUMN cancel_date timestamp,
ADD COLUMN pick_date timestamp,
ADD COLUMN pack_date timestamp,
ADD COLUMN cancel_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
ADD COLUMN pick_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
ADD COLUMN pack_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
ADD COLUMN send_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE;
ALTER TABLE delivery RENAME COLUMN deliver_date TO send_date;
