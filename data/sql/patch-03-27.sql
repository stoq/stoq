ALTER TABLE client ADD COLUMN salary numeric(20,2) DEFAULT 0
    CONSTRAINT positive_salary CHECK(salary >= 0);

CREATE TABLE client_salary_history (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp,
    new_salary decimal(20,2) DEFAULT 0 CONSTRAINT positive_new_salary
                                           CHECK(new_salary >= 0),
    old_salary decimal(20,2) DEFAULT 0 CONSTRAINT positive_old_salary
                                           CHECK(old_salary >= 0),
    user_id bigint REFERENCES login_user(id) ON UPDATE CASCADE,
    client_id bigint REFERENCES client(id) ON UPDATE CASCADE
);
