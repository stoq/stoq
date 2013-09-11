-- #5570: Migrate work_order's quote_responsible and execution_responsible
-- from a login_user to a employee. The migration is trivial since all
-- users should have an entry on employee too

-- quote_responsible_id
ALTER TABLE work_order
    DROP CONSTRAINT work_order_quote_responsible_id_fkey;

UPDATE work_order SET quote_responsible_id = employee.id
    FROM person
    JOIN employee ON person.id = employee.person_id
    JOIN login_user ON person.id = login_user.person_id
    WHERE work_order.quote_responsible_id = login_user.id;

ALTER TABLE work_order
    ADD CONSTRAINT work_order_quote_responsible_id_fkey
        FOREIGN KEY (quote_responsible_id) REFERENCES employee(id) ON UPDATE CASCADE;

-- execution_responsible_id
ALTER TABLE work_order
    DROP CONSTRAINT work_order_execution_responsible_id_fkey;

UPDATE work_order SET execution_responsible_id = employee.id
    FROM person
    JOIN employee ON person.id = employee.person_id
    JOIN login_user ON person.id = login_user.person_id
    WHERE work_order.execution_responsible_id = login_user.id;

ALTER TABLE work_order
    ADD CONSTRAINT work_order_execution_responsible_id_fkey
        FOREIGN KEY (execution_responsible_id) REFERENCES employee(id) ON UPDATE CASCADE;
