-- Adding sale context

CREATE TABLE context (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text NOT NULL UNIQUE,
    start_time time,
    end_time time,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO context DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sale_context (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    sale_id uuid NOT NULL UNIQUE REFERENCES sale(id) ON UPDATE CASCADE,
    context_id uuid NOT NULL REFERENCES context(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO sale_context DO ALSO SELECT update_te(old.te_id);

-- Default table price for branch. (this used to be a parameter)
ALTER TABLE branch ADD COLUMN default_client_category_id uuid REFERENCES client_category(id) ON UPDATE CASCADE;

-- Sellable
ALTER TABLE sellable ADD COLUMN short_description text DEFAULT '';

-- Credit provider
ALTER TABLE credit_provider
    ADD COLUMN sort_order int DEFAULT 0,
    ADD COLUMN visible boolean DEFAULT true;
