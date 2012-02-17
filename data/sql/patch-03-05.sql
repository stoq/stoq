-- Remove all bogus PersonAdaptTo-prefixes
ALTER TABLE person_adapt_to_branch RENAME TO branch;
ALTER SEQUENCE person_adapt_to_branch_id_seq RENAME TO branch_id_seq;

ALTER TABLE person_adapt_to_client RENAME TO client;
ALTER SEQUENCE person_adapt_to_client_id_seq RENAME TO client_id_seq;

ALTER TABLE person_adapt_to_company RENAME TO company;
ALTER SEQUENCE person_adapt_to_company_id_seq RENAME TO company_id_seq;

ALTER TABLE person_adapt_to_credit_provider RENAME TO credit_provider;
ALTER SEQUENCE person_adapt_to_credit_provider_id_seq RENAME TO credit_provider_id_seq;

ALTER TABLE person_adapt_to_employee RENAME TO employee;
ALTER SEQUENCE person_adapt_to_employee_id_seq RENAME TO employee_id_seq;

ALTER TABLE person_adapt_to_individual RENAME TO individual;
ALTER SEQUENCE person_adapt_to_individual_id_seq RENAME TO individual_id_seq;

-- user is a keyword in postgres, so rename to login_user
ALTER TABLE person_adapt_to_user RENAME TO login_user;
ALTER SEQUENCE person_adapt_to_user_id_seq RENAME TO login_user_id_seq;

ALTER TABLE person_adapt_to_sales_person RENAME TO sales_person;
ALTER SEQUENCE person_adapt_to_sales_person_id_seq RENAME TO sales_person_id_seq;

ALTER TABLE person_adapt_to_supplier RENAME TO supplier;
ALTER SEQUENCE person_adapt_to_supplier_id_seq RENAME TO supplier_id_seq;

ALTER TABLE person_adapt_to_transporter RENAME TO transporter;
ALTER SEQUENCE person_adapt_to_transporter_id_seq RENAME TO transporter_id_seq;
