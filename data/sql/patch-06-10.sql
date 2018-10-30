COMMIT;
ALTER TYPE credit_card_type ADD VALUE 'voucher';
BEGIN;

ALTER TABLE branch
    ADD COLUMN name text,
    ADD COLUMN certificate_id uuid REFERENCES certificate(id) ON UPDATE CASCADE;
-- TODO: update reference to certificate_id if there are some in the database

ALTER TABLE company
    ADD COLUMN parent_id uuid REFERENCES company(id) ON UPDATE CASCADE;

CREATE TABLE station_type (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    name text UNIQUE NOT NULL
);
CREATE RULE update_te AS ON UPDATE TO station_type DO ALSO SELECT update_te(old.te_id, 'station_type');

ALTER TABLE branch_station ADD COLUMN type_id uuid REFERENCES station_type(id) ON UPDATE CASCADE;

ALTER TABLE image
    ADD COLUMN keywords text,
    ADD COLUMN station_type_id uuid REFERENCES station_type(id) ON UPDATE CASCADE;

ALTER TABLE sellable_category
    ADD COLUMN color text,
    ADD COLUMN sort_order integer default 0;

ALTER TABLE sellable
    ADD COLUMN sort_order integer default 0,
    ADD COLUMN favorite boolean default false,
    ADD COLUMN keywords text;

-- To handle drawers that have an inverted logic
ALTER TABLE device_settings
    ADD COLUMN drawer_inverted boolean default false;

CREATE TABLE sellable_branch_override (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    status sellable_status,
    base_price numeric(20, 2) CONSTRAINT positive_price CHECK (base_price >= 0),
    max_discount numeric(10, 2),
    on_sale_price numeric(20, 2) CONSTRAINT positive_on_sale_price CHECK (on_sale_price >= 0),
    on_sale_start_date timestamp,
    on_sale_end_date timestamp,
    tax_constant_id uuid REFERENCES sellable_tax_constant(id) ON UPDATE CASCADE,
    default_sale_cfop_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE,

    price_last_updated timestamp,

    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    sellable_id uuid NOT NULL REFERENCES sellable(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO sellable_branch_override DO ALSO SELECT update_te(old.te_id, 'sellable_branch_override');


CREATE TABLE product_branch_override (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    location text,

    icms_template_id uuid REFERENCES product_icms_template(id) ON UPDATE CASCADE,
    ipi_template_id uuid REFERENCES product_ipi_template(id) ON UPDATE CASCADE,
    pis_template_id uuid REFERENCES product_pis_template(id) ON UPDATE CASCADE,
    cofins_template_id uuid REFERENCES product_cofins_template(id) ON UPDATE CASCADE,

    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    product_id uuid NOT NULL REFERENCES product(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO product_branch_override DO ALSO SELECT update_te(old.te_id, 'product_branch_override');

CREATE TABLE storable_branch_override (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    minimum_quantity numeric(20, 3) DEFAULT 0
        CONSTRAINT positive_minimum_quantity CHECK (minimum_quantity >= 0),
    maximum_quantity numeric(20, 3) DEFAULT 0
        CONSTRAINT positive_maximum_quantity CHECK (maximum_quantity >= 0),

    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    storable_id uuid NOT NULL REFERENCES storable(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO storable_branch_override DO ALSO SELECT update_te(old.te_id, 'storable_branch_override');


CREATE TABLE service_branch_override (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    city_taxation_code text,
    service_list_item_code text,
    p_iss numeric(10, 2),

    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    service_id uuid NOT NULL REFERENCES service(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO service_branch_override DO ALSO SELECT update_te(old.te_id, 'service_branch_override');
