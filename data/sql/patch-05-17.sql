ALTER TABLE product
    ADD COLUMN is_grid boolean DEFAULT FALSE,
    ADD COLUMN parent_id uuid REFERENCES product(id) ON UPDATE CASCADE;

CREATE TABLE grid_group (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    is_active boolean DEFAULT True
);
CREATE RULE update_te AS ON UPDATE TO grid_group DO ALSO SELECT update_te(old.te_id);

CREATE TABLE grid_attribute (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    is_active boolean DEFAULT True,
    group_id uuid REFERENCES grid_group(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO grid_attribute DO ALSO SELECT update_te(old.te_id);

CREATE TABLE grid_option (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    is_active boolean DEFAULT True,
    option_order integer,
    attribute_id uuid REFERENCES grid_attribute(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO grid_option DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_attribute (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_id uuid REFERENCES product(id) ON UPDATE CASCADE,
    attribute_id uuid REFERENCES grid_attribute(id) ON UPDATE CASCADE,
    UNIQUE (product_id, attribute_id)
);
CREATE RULE update_te AS ON UPDATE TO product_attribute DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_option_map (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_id uuid REFERENCES product(id) ON UPDATE CASCADE,
    attribute_id uuid REFERENCES grid_attribute(id) ON UPDATE CASCADE,
    option_id uuid REFERENCES grid_option(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO product_option_map DO ALSO SELECT update_te(old.te_id);
