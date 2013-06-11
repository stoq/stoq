-- Create work_order_package and work_order_package_item tables
-- Also, add a column for storing current_branch on work_order

CREATE TABLE work_order_package (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    identifier text NOT NULL,
    status integer NOT NULL CONSTRAINT valid_status
      CHECK (status >= 0 AND status <= 2),
    send_date timestamp,
    receive_date timestamp,
    send_responsible_id bigint REFERENCES login_user(id) ON UPDATE CASCADE,
    receive_responsible_id bigint REFERENCES login_user(id) ON UPDATE CASCADE,
    destination_branch_id bigint REFERENCES branch(id) ON UPDATE CASCADE,
    source_branch_id bigint NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    CONSTRAINT different_branches CHECK (source_branch_id != destination_branch_id)
);

CREATE TABLE work_order_package_item (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    order_id bigint NOT NULL REFERENCES work_order(id) ON UPDATE CASCADE,
    package_id bigint NOT NULL REFERENCES work_order_package(id) ON UPDATE CASCADE,
    UNIQUE (order_id, package_id)
);

ALTER TABLE work_order
    ADD COLUMN current_branch_id bigint REFERENCES branch(id) ON UPDATE CASCADE;

-- By default, current_branch is equal to branch
UPDATE work_order
    SET current_branch_id = branch_id;
