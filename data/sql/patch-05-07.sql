ALTER TABLE till ADD COLUMN observations text,
                 ADD COLUMN responsible_open_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
                 ADD COLUMN responsible_close_id uuid REFERENCES login_user(id) ON UPDATE CASCADE;
