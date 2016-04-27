--
-- Copyright (C) 2006-2014 Async Open Source
--
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public License
-- as published by the Free Software Foundation; either version 2
-- of the License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
--
--
-- Author(s): Stoq Team <stoq-devel@async.com.br>
--

-- FIXME: Patched not applied:
--          patch-05-19
--          patch-05-20
--          patch-05-21
--          patch-05-22
--          patch-05-23
--          patch-05-24
--          patch-05-25
--          patch-05-26
--          patch-05-27
--          patch-05-28
--          patch-05-29

--
-- Extensions
--

-- We use UUID table IDS which is included since PostgreSQL 8.3
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- We use pg_trgm to accelerate indices when using LIKE/ILIKE comparisons,
-- which is included since PostgreSQL 8.4
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

--
--  Data types
--

CREATE TYPE sale_status AS ENUM ('initial', 'quote', 'ordered', 'confirmed',
                                 'cancelled', 'returned', 'renegotiated');
CREATE TYPE payment_status AS ENUM ('preview', 'pending', 'paid',
                                    'reviewing', 'confirmed', 'cancelled');
CREATE TYPE payment_type AS ENUM ('in', 'out');
CREATE TYPE work_order_status AS ENUM ('opened', 'cancelled', 'waiting',
                                       'in-progress', 'finished', 'delivered');
CREATE TYPE work_order_package_status AS ENUM ('opened', 'sent', 'received');
CREATE TYPE credit_card_type AS ENUM ('credit', 'debit', 'credit-inst-store',
                                      'credit-inst-provider', 'debit-pre-dated');
CREATE TYPE payment_category_type AS ENUM ('payable', 'receivable');
CREATE TYPE account_type AS ENUM ('bank', 'cash', 'asset', 'credit',
                                  'income', 'expense', 'equity' );
CREATE TYPE event_type AS ENUM ('system', 'user', 'order', 'sale', 'payment');
CREATE TYPE inventory_status AS ENUM ('open', 'closed', 'cancelled');
CREATE TYPE loan_status AS ENUM ('open', 'closed');
CREATE TYPE credit_check_status AS ENUM ('included', 'not-included');
CREATE TYPE marital_status AS ENUM ('single', 'married', 'divorced',
                                    'widowed', 'separeted', 'cohabitation');
CREATE TYPE individual_gender AS ENUM ('male', 'female');
CREATE TYPE client_status AS ENUM ('solvent', 'indebt', 'insolvent', 'inactive');
CREATE TYPE supplier_status AS ENUM ('active', 'inactive', 'blocked');
CREATE TYPE employee_status AS ENUM ('normal', 'away', 'vacation', 'off');
CREATE TYPE stock_transaction_history_type AS ENUM ('initial', 'sell',
    'returned-sale', 'cancelled-sale', 'received-purchase', 'returned-loan',
    'loan', 'production-allocated', 'production-produced',
    'production-returned', 'stock-decrease', 'transfer-from', 'transfer-to',
    'inventory-adjust', 'production-sent', 'imported', 'consignment-returned',
    'wo-used', 'wo-returned-to-stock', 'sale-reserved');
CREATE TYPE product_quality_test_type AS ENUM ('boolean', 'decimal');
CREATE TYPE production_order_status AS ENUM ('opened', 'waiting', 'producing',
    'closed', 'quality-assurance', 'cancelled');
CREATE TYPE purchase_order_status AS ENUM ('quoting', 'pending', 'confirmed',
                                           'consigned', 'cancelled','closed');
CREATE TYPE purchase_order_freight_type AS ENUM ('fob', 'cif');
CREATE TYPE receiving_order_status AS ENUM ('pending', 'closed');
CREATE TYPE receiving_order_freight_type AS ENUM ('fob-payment', 'fob-installments',
                                            'cif-unknown', 'cif-invoice');
CREATE TYPE delivery_status AS ENUM ('initial', 'sent', 'received');
CREATE TYPE sellable_status AS ENUM ('available', 'closed');
CREATE TYPE stock_decrease_status AS ENUM ('initial', 'confirmed');
CREATE TYPE till_status AS ENUM ('pending', 'open', 'closed');
CREATE TYPE transfer_order_status AS ENUM ('pending', 'sent', 'received');
CREATE TYPE account_transaction_operation_type AS ENUM ('in', 'out');
CREATE TYPE returned_sale_status AS ENUM ('pending', 'confirmed');

--
-- Tables that are not syncronized
--

CREATE TABLE branch_synchronization (
    id serial NOT NULL PRIMARY KEY,
    sync_time timestamp  NOT NULL,
    policy text NOT NULL
);

CREATE TABLE city_location (
    id serial NOT NULL PRIMARY KEY,
    country text,
    city text,
    state text,
    city_code integer,
    state_code integer,
    UNIQUE (country, state, city)
);

CREATE TABLE event (
    id serial NOT NULL PRIMARY KEY,
    date timestamp NOT NULL,
    event_type event_type NOT NULL,
    description varchar NOT NULL
);

CREATE TABLE transaction_entry (
    id serial NOT NULL PRIMARY KEY,
    te_time timestamp NOT NULL,
    dirty boolean DEFAULT TRUE
);

--
-- Domain tables
-- Everything below is synchronized and should have a uuid column
--

CREATE TABLE attachment (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text NOT NULL,
    mimetype text,
    blob bytea
);
CREATE RULE update_te AS ON UPDATE TO attachment DO ALSO SELECT update_te(old.te_id);

CREATE TABLE person (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text,
    phone_number text,
    mobile_number text,
    fax_number text,
    email text,
    notes text
);
CREATE RULE update_te AS ON UPDATE TO person DO ALSO SELECT update_te(old.te_id);

CREATE TABLE client_category (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text UNIQUE,
    max_discount numeric(10,2) DEFAULT 0 CONSTRAINT valid_max_discount
        CHECK (max_discount BETWEEN 0 AND 100)
);
CREATE RULE update_te AS ON UPDATE TO client_category DO ALSO SELECT update_te(old.te_id);

CREATE TABLE client (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    status client_status NOT NULL,
    days_late integer CONSTRAINT positive_days_late
        CHECK (days_late >= 0),
    credit_limit numeric(20, 2) CONSTRAINT positive_credit_limit
        CHECK (credit_limit >= 0)
        DEFAULT 0,
    salary numeric(20,2) DEFAULT 0 CONSTRAINT positive_salary
        CHECK(salary >= 0),
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE,
    category_id uuid REFERENCES client_category(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO client DO ALSO SELECT update_te(old.te_id);


CREATE TABLE company (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    is_active boolean,
    cnpj text,
    fancy_name text,
    state_registry text,
    city_registry text,
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO company DO ALSO SELECT update_te(old.te_id);


CREATE TABLE individual (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    is_active boolean,
    cpf text,
    rg_number text,
    birth_date timestamp,
    occupation text,
    marital_status marital_status NOT NULL,
    father_name text,
    mother_name text,
    rg_expedition_date timestamp,
    rg_expedition_local text,
    gender individual_gender NOT NULL,
    spouse_name text,
    birth_location_id bigint REFERENCES city_location(id) ON UPDATE CASCADE,
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO individual DO ALSO SELECT update_te(old.te_id);

CREATE TABLE employee_role (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text NOT NULL UNIQUE
);
CREATE RULE update_te AS ON UPDATE TO employee_role DO ALSO SELECT update_te(old.te_id);

CREATE TABLE work_permit_data (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    number text,
    series_number text,
    pis_number text,
    pis_bank text,
    pis_registry_date timestamp
);
CREATE RULE update_te AS ON UPDATE TO work_permit_data DO ALSO SELECT update_te(old.te_id);

CREATE TABLE military_data (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    number text,
    series_number text,
    category text
);
CREATE RULE update_te AS ON UPDATE TO military_data DO ALSO SELECT update_te(old.te_id);

CREATE TABLE voter_data (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    number text,
    section text,
    "zone" text
);
CREATE RULE update_te AS ON UPDATE TO voter_data DO ALSO SELECT update_te(old.te_id);

CREATE TABLE bank_account (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    -- bank_account bigint UNIQUE REFERENCES account(id) ON UPDATE CASCADE,
    bank_number integer CONSTRAINT positive_bank_number
        CHECK (bank_number >= 0),
    bank_branch text,
    bank_account text,
    bank_type bigint
);
CREATE RULE update_te AS ON UPDATE TO bank_account DO ALSO SELECT update_te(old.te_id);

CREATE TABLE bill_option (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    option text,
    value text,
    bank_account_id uuid REFERENCES bank_account(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO bill_option DO ALSO SELECT update_te(old.te_id);

CREATE TABLE employee (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    is_active boolean,
    admission_date timestamp,
    expire_vacation timestamp,
    salary numeric(20, 2),
    status employee_status NOT NULL,
    registry_number text,
    education_level text,
    dependent_person_number integer CONSTRAINT positive_dependent_person_number
        CHECK (dependent_person_number >= 0),
    role_id uuid REFERENCES employee_role(id) ON UPDATE CASCADE,
    workpermit_data_id uuid REFERENCES work_permit_data(id) ON UPDATE CASCADE,
    military_data_id uuid REFERENCES military_data(id) ON UPDATE CASCADE,
    voter_data_id uuid REFERENCES voter_data(id) ON UPDATE CASCADE,
    bank_account_id uuid REFERENCES bank_account(id) ON UPDATE CASCADE,
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO employee DO ALSO SELECT update_te(old.te_id);

CREATE TABLE branch (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    manager_id uuid REFERENCES employee(id) ON UPDATE CASCADE,
    is_active boolean,
    crt integer DEFAULT 1,
    acronym text UNIQUE CONSTRAINT acronym_not_empty
        CHECK (acronym != ''),
    can_execute_foreign_work_orders boolean DEFAULT false,
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO branch DO ALSO SELECT update_te(old.te_id);

ALTER TABLE branch_synchronization
    ADD COLUMN branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE;

ALTER TABLE employee ADD COLUMN branch_id uuid REFERENCES branch(id)
    ON UPDATE CASCADE;


CREATE TABLE sales_person (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    comission numeric(10, 2) CONSTRAINT positive_comission
        CHECK (comission >= 0),
    comission_type integer CONSTRAINT check_valid_comission_type
        CHECK (comission_type >= 0 AND comission_type < 7),
    is_active boolean,
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO sales_person DO ALSO SELECT update_te(old.te_id);

CREATE TABLE supplier (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    is_active boolean,
    status supplier_status NOT NULL,
    product_desc text,
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO supplier DO ALSO SELECT update_te(old.te_id);

CREATE TABLE transporter (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    is_active boolean,
    open_contract_date timestamp,
    freight_percentage numeric(10, 2) NOT NULL
        CONSTRAINT positive_freight_percentage
        CHECK (freight_percentage >= 0),
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO transporter DO ALSO SELECT update_te(old.te_id);

CREATE TABLE user_profile (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text,
    max_discount numeric(10, 2) DEFAULT 0
);
CREATE RULE update_te AS ON UPDATE TO user_profile DO ALSO SELECT update_te(old.te_id);

CREATE TABLE login_user (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    username text NOT NULL UNIQUE,
    pw_hash text,
    is_active boolean,
    profile_id uuid REFERENCES user_profile(id) ON UPDATE CASCADE,
    person_id uuid UNIQUE REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO login_user DO ALSO SELECT update_te(old.te_id);

CREATE TABLE user_branch_access (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    user_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    UNIQUE (user_id, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO user_branch_access DO ALSO SELECT update_te(old.te_id);

CREATE TABLE client_salary_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    date timestamp,
    new_salary decimal(20,2) DEFAULT 0 CONSTRAINT positive_new_salary
                                           CHECK(new_salary >= 0),
    old_salary decimal(20,2) DEFAULT 0 CONSTRAINT positive_old_salary
                                           CHECK(old_salary >= 0),
    user_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    client_id uuid REFERENCES client(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO client_salary_history DO ALSO SELECT update_te(old.te_id);


CREATE TABLE product_tax_template (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text,
    tax_type integer
);
CREATE RULE update_te AS ON UPDATE TO product_tax_template DO ALSO SELECT update_te(old.te_id);

CREATE TABLE image (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    image bytea,
    thumbnail bytea,
    description text
);
CREATE RULE update_te AS ON UPDATE TO image DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sellable_tax_constant (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    tax_type integer CONSTRAINT valid_tax_type
        CHECK (tax_type >= 41 AND tax_type < 46),
    tax_value numeric(10, 2)
);
CREATE RULE update_te AS ON UPDATE TO sellable_tax_constant DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sellable_category (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    suggested_markup numeric(10, 2),
    salesperson_commission numeric(10, 2),
    category_id uuid REFERENCES sellable_category(id) ON UPDATE CASCADE,
    tax_constant_id uuid REFERENCES sellable_tax_constant(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO sellable_category DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sellable_unit (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    unit_index integer CONSTRAINT positive_unit_index
        CHECK(unit_index >= 0),
    allow_fraction boolean DEFAULT TRUE
);
CREATE RULE update_te AS ON UPDATE TO sellable_unit DO ALSO SELECT update_te(old.te_id);

CREATE TABLE cfop_data (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    code text,
    description text
);
CREATE RULE update_te AS ON UPDATE TO cfop_data DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sellable (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    barcode text,
    code text,
    status sellable_status NOT NULL,
    description text,
    cost numeric(20, 8) CONSTRAINT positive_cost
        CHECK (cost >= 0),
    base_price numeric(20, 2) CONSTRAINT positive_price
        CHECK (base_price >= 0),
    notes text,
    max_discount numeric(10, 2),
    commission numeric(10, 2),
    on_sale_price numeric(20, 2) CONSTRAINT positive_on_sale_price
       CHECK (on_sale_price >= 0),
    on_sale_start_date timestamp,
    on_sale_end_date timestamp,
    image_id uuid UNIQUE REFERENCES image(id) ON UPDATE CASCADE,
    unit_id uuid REFERENCES sellable_unit(id) ON UPDATE CASCADE,
    category_id uuid REFERENCES sellable_category(id) ON UPDATE CASCADE,
    tax_constant_id uuid REFERENCES sellable_tax_constant(id) ON UPDATE CASCADE,
    default_sale_cfop_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO sellable DO ALSO SELECT update_te(old.te_id);

-- Those indexes are created to accelerate searchs with lots of sellables
-- using like/ilike comparisons
CREATE INDEX sellable_description_idx ON sellable
    USING gist (description gist_trgm_ops);
CREATE INDEX sellable_description_normalized_idx ON sellable
    USING gist (stoq_normalize_string(description) gist_trgm_ops);

CREATE TABLE product_icms_template (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_tax_template_id uuid UNIQUE REFERENCES product_tax_template(id) ON UPDATE CASCADE,
    bc_include_ipi boolean DEFAULT TRUE,
    bc_st_include_ipi boolean DEFAULT TRUE,
    cst integer,
    csosn integer,
    orig integer,
    mod_bc integer,
    mod_bc_st integer,
    p_cred_sn numeric(10, 2),
    p_cred_sn_valid_until timestamp DEFAULT NULL,
    p_icms numeric(10, 2),
    p_icms_st numeric(10, 2),
    p_mva_st numeric(10, 2),
    p_red_bc numeric(10, 2),
    p_red_bc_st numeric(10, 2)
);
CREATE RULE update_te AS ON UPDATE TO product_icms_template DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_ipi_template (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_tax_template_id uuid UNIQUE REFERENCES product_tax_template(id) ON UPDATE CASCADE,
    cl_enq text,
    cnpj_prod text,
    c_selo text,
    q_selo integer,
    c_enq text,
    calculo integer,
    cst integer,
    p_ipi numeric(10, 2),
    q_unid numeric(16, 4)
);
CREATE RULE update_te AS ON UPDATE TO product_ipi_template DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_manufacturer (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text UNIQUE
);
CREATE RULE update_te AS ON UPDATE TO product_manufacturer DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    consignment boolean NOT NULL DEFAULT FALSE,
    location text,
    part_number text,
    family text,
    brand text,
    model text,
    ncm text,
    ex_tipi text,
    genero text,
    production_time integer DEFAULT 0,
    manage_stock boolean DEFAULT TRUE,
    is_composed boolean DEFAULT FALSE,
    is_grid boolean DEFAULT FALSE,
    is_package boolean DEFAULT FALSE,
    width numeric(10, 2) CONSTRAINT positive_width
        CHECK (width >= 0),
    height numeric(10, 2) CONSTRAINT positive_height
        CHECK (height >= 0),
    depth numeric(10, 2) CONSTRAINT positive_depth
        CHECK (depth >= 0),
    weight numeric(10, 2) CONSTRAINT positive_weight
        CHECK (weight >= 0),
    icms_template_id uuid REFERENCES product_icms_template(id) ON UPDATE CASCADE,
    ipi_template_id uuid REFERENCES product_ipi_template(id) ON UPDATE CASCADE,
    manufacturer_id uuid REFERENCES product_manufacturer(id) ON UPDATE CASCADE,
    parent_id uuid REFERENCES product(id)  ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO product DO ALSO SELECT update_te(old.te_id);

CREATE TABLE grid_group (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text
);
CREATE RULE update_te AS ON UPDATE TO grid_group DO ALSO SELECT update_te(old.te_id);

CREATE TABLE grid_attribute (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    group_id uuid REFERENCES grid_group(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO grid_attribute DO ALSO SELECT update_te(old.te_id);

CREATE TABLE grid_option (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
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


CREATE TABLE product_component (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_id uuid REFERENCES product(id) ON UPDATE CASCADE,
    component_id uuid REFERENCES product(id) ON UPDATE CASCADE,
    design_reference text,
    quantity numeric(20, 3)
        CONSTRAINT positive_quantity CHECK (quantity > 0),
        CONSTRAINT different_products CHECK (product_id != component_id)
);
CREATE RULE update_te AS ON UPDATE TO product_component DO ALSO SELECT update_te(old.te_id);

CREATE TABLE storable (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_id uuid UNIQUE REFERENCES product(id) ON UPDATE CASCADE,
    is_batch boolean DEFAULT False,
    minimum_quantity numeric(20, 3) DEFAULT 0
        CONSTRAINT positive_minimum_quantity CHECK (minimum_quantity >= 0),
    maximum_quantity numeric(20, 3) DEFAULT 0
        CONSTRAINT positive_maximum_quantity CHECK (maximum_quantity >= 0)
);
CREATE RULE update_te AS ON UPDATE TO storable DO ALSO SELECT update_te(old.te_id);

CREATE TABLE storable_batch (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    batch_number text UNIQUE NOT NULL,
    create_date timestamp NOT NULL,
    expire_date timestamp,
    notes text,

    storable_id uuid NOT NULL REFERENCES storable(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO storable_batch DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_stock_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    stock_cost numeric(20, 8),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    storable_id uuid REFERENCES storable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    UNIQUE (branch_id, storable_id, batch_id)
);
CREATE RULE update_te AS ON UPDATE TO product_stock_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_supplier_info (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    supplier_code text,
    base_cost numeric(20, 8) CONSTRAINT positive_base_cost
        CHECK (base_cost >= 0),
    notes text,
    is_main_supplier boolean,
    icms numeric(10, 2) CONSTRAINT positive_icms
        CHECK (icms >= 0),
    lead_time integer DEFAULT 1 CONSTRAINT positive_lead_time
        CHECK (lead_time > 0),
    minimum_purchase numeric(20, 3) DEFAULT 1,
    supplier_id uuid NOT NULL REFERENCES supplier(id) ON UPDATE CASCADE,
    product_id uuid NOT NULL REFERENCES product(id) ON UPDATE CASCADE,
    CONSTRAINT unique_supplier_code UNIQUE (supplier_id, product_id, supplier_code)
);
CREATE RULE update_te AS ON UPDATE TO product_supplier_info DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity_sold numeric(20, 3) CONSTRAINT positive_quantity_sold
        CHECK (quantity_sold >= 0),
    quantity_received numeric(20, 3) CONSTRAINT positive_quantity_received
        CHECK (quantity_received >= 0),
    quantity_transfered numeric(20, 3) CONSTRAINT positive_quantity_transfered
        CHECK (quantity_transfered >= 0),
    quantity_consumed numeric(20, 3) CONSTRAINT positive_consumed
        CHECK (quantity_consumed > 0),
    quantity_produced numeric(20, 3) CONSTRAINT positive_produced
        CHECK (quantity_produced > 0),
    quantity_lost numeric(20, 3) CONSTRAINT positive_lost
        CHECK (quantity_lost > 0),
    sold_date timestamp,
    received_date timestamp,
    production_date timestamp,
    decreased_date timestamp,
    quantity_decreased numeric(20, 3) CONSTRAINT positive_decreased
        CHECK (quantity_decreased > 0),
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO product_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE service (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO service DO ALSO SELECT update_te(old.te_id);

CREATE TABLE payment_renegotiation (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    open_date timestamp,
    close_date timestamp,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 3),
    discount_value numeric(20, 2) CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    surcharge_value numeric(20, 2) CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0),
    total numeric(20, 2) CONSTRAINT positive_total
        CHECK (total >= 0),
    notes text,
    client_id uuid REFERENCES client(id) ON UPDATE CASCADE,
    responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    -- group_id uuid REFERENCES payment_group(id) ON UPDATE CASCADE
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO payment_renegotiation DO ALSO SELECT update_te(old.te_id);

CREATE TABLE payment_group (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    payer_id uuid REFERENCES person(id) ON UPDATE CASCADE,
    renegotiation_id uuid REFERENCES payment_renegotiation(id) ON UPDATE CASCADE,
    recipient_id uuid REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO payment_group DO ALSO SELECT update_te(old.te_id);

ALTER TABLE payment_renegotiation ADD COLUMN group_id uuid
    REFERENCES payment_group(id) ON UPDATE CASCADE;

CREATE TABLE payment_flow_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    history_date timestamp,
    to_receive numeric(20, 2) CONSTRAINT positive_value_to_receive
        CHECK (to_receive >= 0),
    received numeric(20, 2),
    to_pay numeric(20, 2) CONSTRAINT positive_value_to_pay
        CHECK (to_pay >= 0),
    paid numeric(20, 2),
    to_receive_payments integer,
    received_payments integer,
    to_pay_payments integer,
    paid_payments integer,
    balance_expected numeric(20, 2),
    balance_real numeric(20, 2)
);
CREATE RULE update_te AS ON UPDATE TO payment_flow_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE stock_transaction_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    date timestamp,
    stock_cost numeric(20, 8) CONSTRAINT positive_cost
        CHECK (stock_cost >= 0),
    quantity numeric(20, 3),
    type stock_transaction_history_type NOT NULL,
    object_id uuid,
    responsible_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,
    product_stock_item_id uuid NOT NULL REFERENCES product_stock_item(id)
        ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO stock_transaction_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE purchase_order (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    status purchase_order_status NOT NULL,
    open_date timestamp NOT NULL,
    quote_deadline timestamp,
    expected_receival_date timestamp,
    expected_pay_date timestamp,
    receival_date timestamp,
    confirm_date timestamp,
    notes text,
    salesperson_name text,
    freight_type purchase_order_freight_type NOT NULL,
    expected_freight numeric(20, 2) CONSTRAINT positive_expected_freight
        CHECK (expected_freight >= 0),
    surcharge_value numeric(20, 2) CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0),
    discount_value numeric(20, 2) CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    consigned boolean DEFAULT FALSE,
    supplier_id uuid REFERENCES supplier(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    transporter_id uuid REFERENCES transporter(id) ON UPDATE CASCADE,
    responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    group_id uuid REFERENCES payment_group(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO purchase_order DO ALSO SELECT update_te(old.te_id);

CREATE TABLE purchase_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    quantity_received numeric(20, 3) CONSTRAINT positive_quantity_received
        CHECK (quantity_received >= 0),
    base_cost numeric(20, 8) CONSTRAINT positive_base_cost
        CHECK (base_cost >= 0),
    cost numeric(20, 8) CONSTRAINT positive_cost
        CHECK (cost >= 0),
    expected_receival_date timestamp,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    order_id uuid REFERENCES purchase_order(id) ON UPDATE CASCADE,
    parent_item_id uuid REFERENCES purchase_item(id) ON UPDATE CASCADE,
    quantity_sold numeric(20, 3) CONSTRAINT positive_quantity_sold
        CHECK (quantity_sold >= 0 AND
               quantity_sold <= quantity_received)
        DEFAULT 0,
    quantity_returned numeric(20, 3) CONSTRAINT positive_quantity_returned
        CHECK (quantity_returned >= 0 AND
               quantity_returned <= quantity_received - quantity_sold)
        DEFAULT 0
);
CREATE RULE update_te AS ON UPDATE TO purchase_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE quote_group (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO quote_group DO ALSO SELECT update_te(old.te_id);

CREATE TABLE quotation (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,

    purchase_id uuid REFERENCES purchase_order(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    group_id uuid REFERENCES quote_group(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO quotation DO ALSO SELECT update_te(old.te_id);

CREATE TABLE branch_station (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text UNIQUE,
    is_active boolean,
    branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO branch_station DO ALSO SELECT update_te(old.te_id);

CREATE TABLE till (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    status till_status NOT NULL,
    initial_cash_amount numeric(20, 2) CONSTRAINT positive_initial_cash_amount
        CHECK (initial_cash_amount >= 0),
    final_cash_amount numeric(20, 2) CONSTRAINT positive_final_cash_amount
        CHECK (final_cash_amount >= 0),
    opening_date timestamp,
    closing_date timestamp,
    observations text,
    station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE,
    responsible_open_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    responsible_close_id uuid REFERENCES login_user(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO till DO ALSO SELECT update_te(old.te_id);

CREATE TABLE client_category_price (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    category_id uuid REFERENCES client_category(id) ON UPDATE CASCADE,
    price numeric(10,2) CONSTRAINT positive_price CHECK (price >= 0),
    max_discount numeric(10,2),
    commission numeric(10,2),
    UNIQUE (sellable_id, category_id)
);
CREATE RULE update_te AS ON UPDATE TO client_category_price DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sale (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    coupon_id integer,
    invoice_number integer CONSTRAINT valid_invoice_number
        CHECK (invoice_number > 0 AND invoice_number <= 999999999)
        DEFAULT NULL UNIQUE,
    service_invoice_number integer,
    status sale_status NOT NULL,
    discount_value numeric(20, 2) CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    surcharge_value numeric(20, 2) CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0),
    total_amount numeric(20, 2) CONSTRAINT positive_total_amount
        CHECK (total_amount >= 0),
    open_date timestamp,
    close_date timestamp,
    confirm_date timestamp,
    cancel_date timestamp,
    return_date timestamp,
    expire_date timestamp,
    operation_nature text,
    paid boolean DEFAULT false,
    client_id uuid REFERENCES client(id) ON UPDATE CASCADE,
    client_category_id uuid REFERENCES client_category(id) ON UPDATE CASCADE,
    cfop_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE,
    salesperson_id uuid REFERENCES sales_person(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    group_id uuid REFERENCES payment_group(id) ON UPDATE CASCADE,
    transporter_id uuid REFERENCES transporter(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO sale DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sale_comment (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    date timestamp,
    comment text,
    sale_id uuid NOT NULL REFERENCES sale(id) ON UPDATE CASCADE,
    author_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO sale_comment DO ALSO SELECT update_te(old.te_id);

CREATE TABLE invoice_item_icms (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    bc_include_ipi boolean DEFAULT TRUE,
    bc_st_include_ipi boolean DEFAULT TRUE,
    cst integer,
    csosn integer,
    mod_bc integer,
    mod_bc_st integer,
    orig integer,
    p_cred_sn numeric(10, 2),
    p_mva_st numeric(10, 2),
    p_icms numeric(10, 2),
    p_icms_st numeric(10, 2),
    p_red_bc numeric(10, 2),
    p_red_bc_st numeric(10, 2),
    v_bc numeric(20, 2),
    v_bc_st numeric(20, 2),
    v_bc_st_ret numeric(20, 2),
    v_cred_icms_sn numeric(20, 2),
    v_icms numeric(20, 2),
    v_icms_st numeric(20, 2),
    v_icms_st_ret numeric(20, 2)
);
CREATE RULE update_te AS ON UPDATE TO invoice_item_icms DO ALSO SELECT update_te(old.te_id);

CREATE TABLE invoice_item_ipi (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    cl_enq text,
    cnpj_prod text,
    c_selo text,
    q_selo integer,
    c_enq text,
    calculo integer,
    cst integer,
    p_ipi numeric(10, 2),
    q_unid numeric(16, 4),
    v_ipi numeric(20, 2),
    v_bc numeric(20, 2),
    v_unid numeric(20, 4)
);
CREATE RULE update_te AS ON UPDATE TO invoice_item_ipi DO ALSO SELECT update_te(old.te_id);

CREATE TABLE sale_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    quantity_decreased numeric(20, 3) DEFAULT 0
        CONSTRAINT valid_quantity_decreased CHECK (quantity_decreased <= quantity),
    base_price numeric(20, 2) CONSTRAINT positive_base_price
        CHECK (base_price >= 0),
    price numeric(20, 2) CONSTRAINT positive_price
        CHECK (price >= 0),
    notes text,
    estimated_fix_date timestamp,
    completion_date timestamp,
    average_cost numeric(20, 8) DEFAULT 0,
    sale_id uuid REFERENCES sale(id) ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    icms_info_id uuid REFERENCES invoice_item_icms(id) ON UPDATE CASCADE,
    ipi_info_id uuid REFERENCES invoice_item_ipi(id) ON UPDATE CASCADE,
    cfop_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE,
    parent_item_id uuid REFERENCES sale_item(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO sale_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE returned_sale (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    identifier serial NOT NULL,
    status returned_sale_status NOT NULL,
    return_date timestamp,
    confirm_date timestamp,
    reason text,
    invoice_number integer CONSTRAINT valid_invoice_number
        CHECK (invoice_number > 0 AND invoice_number <= 999999999)
        DEFAULT NULL UNIQUE,
    responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    confirm_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    sale_id uuid REFERENCES sale(id) ON UPDATE CASCADE,
    new_sale_id uuid UNIQUE REFERENCES sale(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO returned_sale DO ALSO SELECT update_te(old.te_id);

CREATE TABLE returned_sale_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    price numeric(20, 2) CONSTRAINT positive_price
        CHECK (price >= 0),
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    sale_item_id uuid REFERENCES sale_item(id) ON UPDATE CASCADE,
    returned_sale_id uuid REFERENCES returned_sale(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO returned_sale_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE address (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    street text,
    streetnumber integer CONSTRAINT positive_streetnumber
        CHECK (streetnumber > 0),
    district text,
    postal_code text,
    complement text,
    is_main_address boolean,
    person_id uuid REFERENCES person(id) ON UPDATE CASCADE,
    city_location_id bigint REFERENCES city_location(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO address DO ALSO SELECT update_te(old.te_id);

CREATE TABLE delivery (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    status delivery_status NOT NULL,
    open_date timestamp,
    deliver_date timestamp,
    receive_date timestamp,
    tracking_code text,
    address_id uuid REFERENCES address(id) ON UPDATE CASCADE,
    transporter_id uuid REFERENCES transporter(id) ON UPDATE CASCADE,
    service_item_id uuid REFERENCES sale_item(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO delivery DO ALSO SELECT update_te(old.te_id);

ALTER TABLE sale_item ADD COLUMN delivery_id uuid
    REFERENCES delivery(id) ON UPDATE CASCADE;

CREATE TABLE calls (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    date timestamp,
    message text,
    description text,
    person_id uuid REFERENCES person(id) ON UPDATE CASCADE,
    attendant_id uuid REFERENCES login_user(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO calls DO ALSO SELECT update_te(old.te_id);

CREATE TABLE account (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    account_type account_type NOT NULL,
    description text NOT NULL,
    code text,
    parent_id uuid REFERENCES account(id) ON UPDATE CASCADE,
    station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO account DO ALSO SELECT update_te(old.te_id);

ALTER TABLE bank_account ADD COLUMN account_id uuid
    UNIQUE REFERENCES account(id) ON UPDATE CASCADE;

CREATE TABLE payment_method (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    is_active boolean,
    daily_interest numeric(10, 2) CONSTRAINT valid_daily_interest
        CHECK (daily_interest >= 0 AND daily_interest <= 100),
    penalty numeric(10, 2) CONSTRAINT penalty_percent
        CHECK (penalty >= 0 AND penalty <= 100),
    method_name text UNIQUE,
    payment_day integer CONSTRAINT valid_payment_day
        CHECK (payment_day >= 1 AND payment_day <= 28),
    closing_day integer CONSTRAINT valid_closing_day
        CHECK (closing_day >= 1 AND closing_day <= 28),
    max_installments integer CONSTRAINT positive_max_installments
        CHECK (max_installments > 0),
    destination_account_id uuid REFERENCES account(id) ON UPDATE CASCADE NOT NULL
);
CREATE RULE update_te AS ON UPDATE TO payment_method DO ALSO SELECT update_te(old.te_id);

CREATE TABLE payment_category (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    name text UNIQUE,
    category_type payment_category_type DEFAULT 'payable' NOT NULL,
    color text
);
CREATE RULE update_te AS ON UPDATE TO payment_category DO ALSO SELECT update_te(old.te_id);

CREATE TABLE payment (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    payment_type payment_type NOT NULL,
    status payment_status NOT NULL,
    open_date timestamp,
    due_date timestamp,
    paid_date timestamp,
    cancel_date timestamp,
    paid_value numeric(20, 2) CONSTRAINT positive_paid_value
        CHECK (paid_value >= 0),
    base_value numeric(20, 2) CONSTRAINT positive_base_value
        CHECK (base_value >= 0),
    value numeric(20, 2) CONSTRAINT positive_value
        CHECK (value >= 0),
    interest numeric(20, 2) CONSTRAINT interest_percent
        CHECK (interest >= 0),
    discount numeric(20, 2) CONSTRAINT positive_discount
        CHECK (discount >= 0),
    description text,
    payment_number text,
    penalty numeric(20, 2),
    bill_received boolean DEFAULT FALSE,
    attachment_id uuid UNIQUE REFERENCES attachment(id) ON UPDATE CASCADE,
    method_id uuid REFERENCES payment_method(id) ON UPDATE CASCADE,
    group_id uuid REFERENCES payment_group(id) ON UPDATE CASCADE,
    till_id uuid REFERENCES till(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    category_id uuid REFERENCES payment_category(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO payment DO ALSO SELECT update_te(old.te_id);

CREATE TABLE payment_comment (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    date timestamp,
    comment text,
    payment_id uuid REFERENCES payment(id) ON UPDATE CASCADE,
    author_id uuid REFERENCES login_user(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO payment_comment DO ALSO SELECT update_te(old.te_id);

CREATE TABLE check_data (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    payment_id uuid REFERENCES payment(id) ON UPDATE CASCADE,
    bank_account_id uuid REFERENCES bank_account(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO check_data DO ALSO SELECT update_te(old.te_id);

CREATE TABLE card_payment_device (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    monthly_cost numeric(20, 2),
    description text
);
CREATE RULE update_te AS ON UPDATE TO card_payment_device DO ALSO SELECT update_te(old.te_id);

CREATE TABLE credit_provider (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    is_active boolean,
    max_installments integer DEFAULT 12 CONSTRAINT valid_max_installments
        CHECK (max_installments > 0),
    short_name text,
    provider_id text,
    open_contract_date timestamp,
    default_device_id uuid REFERENCES card_payment_device(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO credit_provider DO ALSO SELECT update_te(old.te_id);

CREATE TABLE card_operation_cost (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    device_id uuid REFERENCES card_payment_device(id) ON UPDATE CASCADE,
    provider_id uuid REFERENCES credit_provider(id) ON UPDATE CASCADE,
    card_type credit_card_type NOT NULL,
    installment_start integer CONSTRAINT positive_installment_start
        CHECK (installment_start>=1),
    installment_end integer CONSTRAINT positive_installment_end
        CHECK (installment_end>=1),
    payment_days integer CHECK (payment_days >= 0),
    fee numeric(10, 2),
    fare numeric(20, 2),
    CONSTRAINT valid_installment_range CHECK (installment_start <= installment_end)
);
CREATE RULE update_te AS ON UPDATE TO card_operation_cost DO ALSO SELECT update_te(old.te_id);

CREATE TABLE credit_card_data (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    auth integer DEFAULT NULL,
    nsu integer DEFAULT NULL,
    installments integer DEFAULT 1,
    card_type credit_card_type NOT NULL,
    entrance_value numeric(20, 2) DEFAULT 0,
    fee numeric(10, 2) NOT NULL DEFAULT 0,
    fee_value numeric(20, 2) DEFAULT 0,
    fare numeric(20, 2) DEFAULT 0,
    payment_id uuid UNIQUE REFERENCES payment(id) ON UPDATE CASCADE,
    provider_id uuid REFERENCES credit_provider(id) ON UPDATE CASCADE,
    device_id uuid REFERENCES card_payment_device(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO credit_card_data DO ALSO SELECT update_te(old.te_id);

CREATE TABLE payment_change_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    change_reason text,
    last_due_date timestamp,
    change_date timestamp,
    new_due_date timestamp,
    last_status payment_status NOT NULL,
    new_status payment_status NOT NULL,
    payment_id uuid REFERENCES payment(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO payment_change_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE fiscal_sale_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    sale_id uuid REFERENCES sale(id) ON UPDATE CASCADE,
    document_type integer CONSTRAINT valid_type
        CHECK (document_type = 0 OR document_type = 1),
    document text,
    coo integer,
    document_counter integer
);
CREATE RULE update_te AS ON UPDATE TO fiscal_sale_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE device_settings (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    "type" integer CONSTRAINT valid_type
        CHECK (type >= 0 AND type < 4),
    brand text,
    model text,
    device_name text,
    is_active boolean,
    station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE,
    UNIQUE (device_name, station_id)
);
CREATE RULE update_te AS ON UPDATE TO device_settings DO ALSO SELECT update_te(old.te_id);


-- FIXME: This should be in ecf plugin
CREATE TABLE device_constant (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    constant_type integer CONSTRAINT valid_constant_type
        CHECK (constant_type >= 0 AND constant_type < 3),
    constant_name text,
    constant_value numeric(10, 2) CONSTRAINT positive_constant_value
        CHECK (constant_value >= 0),
    constant_enum integer
        CHECK ((constant_enum >= 0 AND constant_enum < 8) OR
               (constant_enum >= 20 AND constant_enum < 25) OR
               (constant_enum >= 40 AND constant_enum < 46)),
    device_value bytea,
    device_settings_id uuid REFERENCES device_settings(id) ON UPDATE CASCADE
    -- FIXME: This is needed by the ECF plugin which doesn't have
    --        infrastructure to deal with schema generations
    ,is_valid_model bool
);
CREATE RULE update_te AS ON UPDATE TO device_constant DO ALSO SELECT update_te(old.te_id);

CREATE TABLE employee_role_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    began timestamp,
    ended timestamp,
    salary numeric(20, 2),
    role_id uuid REFERENCES employee_role(id) ON UPDATE CASCADE,
    employee_id uuid REFERENCES employee(id) ON UPDATE CASCADE,
    is_active boolean
);
CREATE RULE update_te AS ON UPDATE TO employee_role_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE contact_info (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    contact_info text,
    person_id uuid REFERENCES person(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO contact_info DO ALSO SELECT update_te(old.te_id);

CREATE TABLE parameter_data (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    field_name text NOT NULL UNIQUE,
    field_value text,
    is_editable boolean
);
CREATE RULE update_te AS ON UPDATE TO parameter_data DO ALSO SELECT update_te(old.te_id);

CREATE TABLE profile_settings (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    app_dir_name text,
    has_permission boolean,
    user_profile_id uuid REFERENCES user_profile(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO profile_settings DO ALSO SELECT update_te(old.te_id);

CREATE TABLE cost_center (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    name text NOT NULL,
    description text,
    budget numeric(20, 2) CONSTRAINT positive_budget CHECK (budget >= 0),
    is_active boolean NOT NULL DEFAULT TRUE
);
CREATE RULE update_te AS ON UPDATE TO cost_center DO ALSO SELECT update_te(old.te_id);

ALTER TABLE sale ADD COLUMN
    cost_center_id uuid REFERENCES cost_center(id) ON UPDATE CASCADE;

CREATE TABLE cost_center_entry (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    cost_center_id uuid NOT NULL REFERENCES cost_center(id) ON UPDATE CASCADE,
    payment_id uuid UNIQUE REFERENCES payment(id) ON UPDATE CASCADE,
    stock_transaction_id uuid UNIQUE REFERENCES stock_transaction_history(id)
        ON UPDATE CASCADE,
    CONSTRAINT stock_transaction_or_payment
        CHECK ((payment_id IS NULL AND stock_transaction_id IS NOT NULL) OR
               (payment_id IS NOT NULL AND stock_transaction_id IS NULL))
);
CREATE RULE update_te AS ON UPDATE TO cost_center_entry DO ALSO SELECT update_te(old.te_id);

CREATE TABLE receiving_order (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    status receiving_order_status NOT NULL,
    receival_date timestamp,
    confirm_date timestamp,
    notes text,
    freight_total numeric(20, 2) CONSTRAINT positive_freight_total
        CHECK (freight_total >= 0),
    surcharge_value numeric(20, 2) CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0),
    discount_value numeric(20, 2) CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    icms_total numeric(20, 2),
    ipi_total numeric(20, 2),
    freight_type receiving_order_freight_type DEFAULT 'fob-payment' NOT NULL,
    invoice_number integer CONSTRAINT valid_invoice_number
        CHECK (invoice_number > 0 AND invoice_number <= 999999999),
    invoice_total numeric(20, 2),
    cfop_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE,
    responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    supplier_id uuid REFERENCES supplier(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    transporter_id uuid REFERENCES transporter(id) ON UPDATE CASCADE,
    secure_value numeric(20, 2) CONSTRAINT positive_secure_value
        CHECK (secure_value >= 0),
    expense_value numeric(20, 2) CONSTRAINT positive_expense_value
        CHECK (expense_value >= 0),
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO receiving_order DO ALSO SELECT update_te(old.te_id);

CREATE TABLE receiving_order_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    cost numeric(20, 8) CONSTRAINT positive_cost
        CHECK (cost >= 0),
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    receiving_order_id uuid REFERENCES receiving_order(id) ON UPDATE CASCADE,
    purchase_item_id uuid REFERENCES purchase_item(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO receiving_order_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE purchase_receiving_map (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    purchase_id uuid REFERENCES purchase_order(id) ON UPDATE CASCADE,
    receiving_id uuid REFERENCES receiving_order(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO purchase_receiving_map DO ALSO SELECT update_te(old.te_id);

CREATE TABLE till_entry (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    date timestamp,
    description text,
    value numeric(20, 2),
    till_id uuid NOT NULL REFERENCES till(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    payment_id uuid REFERENCES payment(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO till_entry DO ALSO SELECT update_te(old.te_id);

CREATE TABLE fiscal_book_entry (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    entry_type integer,
    icms_value numeric(20, 2),
    iss_value numeric(20, 2),
    ipi_value numeric(20, 2),
    date timestamp,
    is_reversal boolean,
    invoice_number integer CONSTRAINT valid_invoice_number
        CHECK (invoice_number >= 0 AND invoice_number <= 999999999),
    cfop_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    drawee_id uuid REFERENCES person(id) ON UPDATE CASCADE,
    payment_group_id uuid REFERENCES payment_group(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO fiscal_book_entry DO ALSO SELECT update_te(old.te_id);

CREATE TABLE fiscal_day_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    emission_date date CONSTRAINT past_emission_date
        CHECK (emission_date <= DATE(NOW())),
    station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE,
    serial text,
    serial_id integer,
    coupon_start integer CONSTRAINT positive_coupon_start
        CHECK (coupon_start > 0),
    coupon_end integer CONSTRAINT positive_coupon_end
        CHECK (coupon_end > 0),
    cro integer CONSTRAINT positive_cro
        CHECK (cro > 0),
    crz integer CONSTRAINT positive_crz
        CHECK (crz > 0),
    period_total numeric(20, 2) CONSTRAINT positive_period_total
        CHECK (period_total >= 0),
    total numeric(20, 2) CONSTRAINT positive_total
        CHECK (total >= 0),
    -- FIXME: Not in domain class
    tax_total numeric(10, 2) CONSTRAINT positive_tax_total
        CHECK (tax_total >= 0),
    CONSTRAINT coupon_start_lower_than_coupon_end
        CHECK (coupon_start <= coupon_end),
    reduction_date timestamp
);
CREATE RULE update_te AS ON UPDATE TO fiscal_day_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE fiscal_day_tax (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    code text CONSTRAINT valid_code
        CHECK (code ~ '^([0-9][0-9][0-9][0-9]|I|F|N|ISS|DESC|CANC)$'),
    value numeric(20, 2) CONSTRAINT positive_value
        CHECK (value >= 0),
    fiscal_day_history_id uuid REFERENCES fiscal_day_history(id) ON UPDATE CASCADE,
    type text
);
CREATE RULE update_te AS ON UPDATE TO fiscal_day_tax DO ALSO SELECT update_te(old.te_id);


CREATE TABLE installed_plugin (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    plugin_name text UNIQUE NOT NULL,
    plugin_version integer CONSTRAINT positive_plugin_version
        CHECK (plugin_version >= 0)
);
CREATE RULE update_te AS ON UPDATE TO installed_plugin DO ALSO SELECT update_te(old.te_id);


CREATE TABLE plugin_egg (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    plugin_name text UNIQUE NOT NULL,
    egg_md5sum text DEFAULT NULL,
    egg_content bytea DEFAULT NULL
);
CREATE RULE update_te AS ON UPDATE TO plugin_egg DO ALSO SELECT update_te(old.te_id);

CREATE TABLE commission_source (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    direct_value numeric(10, 2) NOT NULL CONSTRAINT positive_value
        CHECK (direct_value >= 0),
    installments_value numeric(10, 2) NOT NULL CONSTRAINT positive_installments_value
        CHECK (installments_value >= 0),
    category_id uuid REFERENCES sellable_category(id) ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    -- only one reference will exist at a time: category_id or sellable_id
    -- never both or none of them
    CONSTRAINT check_exist_one_fkey
        CHECK (category_id IS NOT NULL AND sellable_id IS NULL OR
               category_id IS NULL AND sellable_id IS NOT NULL)
);
CREATE RULE update_te AS ON UPDATE TO commission_source DO ALSO SELECT update_te(old.te_id);

CREATE TABLE commission (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    value numeric(20, 2) NOT NULL,
    commission_type integer NOT NULL,
    sale_id uuid NOT NULL REFERENCES sale(id) ON UPDATE CASCADE,
    payment_id uuid NOT NULL UNIQUE REFERENCES payment(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO commission DO ALSO SELECT update_te(old.te_id);

CREATE TABLE transfer_order (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    open_date timestamp NOT NULL,
    receival_date timestamp,
    invoice_number integer,
    status transfer_order_status NOT NULL,
    comments text,
    source_branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    destination_branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    source_responsible_id uuid NOT NULL REFERENCES employee(id) ON UPDATE CASCADE,
    destination_responsible_id uuid REFERENCES employee(id) ON UPDATE CASCADE,
    UNIQUE (identifier, source_branch_id)
);
CREATE RULE update_te AS ON UPDATE TO transfer_order DO ALSO SELECT update_te(old.te_id);

CREATE TABLE transfer_order_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    sellable_id uuid NOT NULL REFERENCES sellable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    transfer_order_id uuid REFERENCES transfer_order(id) ON UPDATE CASCADE,
    quantity numeric(20, 3) NOT NULL CONSTRAINT positive_quantity
        CHECK (quantity > 0),
    stock_cost numeric(20, 8) NOT NULL DEFAULT 0 CONSTRAINT positive_stock_cost
        CHECK (stock_cost >= 0)
);
CREATE RULE update_te AS ON UPDATE TO transfer_order_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE invoice_layout (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description varchar NOT NULL,
    width bigint NOT NULL CONSTRAINT positive_width
        CHECK (width > 0),
    height bigint NOT NULL CONSTRAINT positive_height
        CHECK (height > 0)
);
CREATE RULE update_te AS ON UPDATE TO invoice_layout DO ALSO SELECT update_te(old.te_id);

CREATE TABLE invoice_field (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    field_name varchar NOT NULL,
    layout_id uuid REFERENCES invoice_layout(id) ON UPDATE CASCADE,
    x bigint NOT NULL CONSTRAINT positive_x
        CHECK (x >= 0),
    y bigint NOT NULL CONSTRAINT positive_y
        CHECK (y >= 0),
    width bigint NOT NULL CONSTRAINT positive_width
        CHECK (width > 0),
    height bigint NOT NULL CONSTRAINT positive_height
        CHECK (height > 0)
);
CREATE RULE update_te AS ON UPDATE TO invoice_field DO ALSO SELECT update_te(old.te_id);

CREATE TABLE invoice_printer (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    device_name varchar NOT NULL,
    description varchar NOT NULL,
    station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE,
    layout_id uuid REFERENCES invoice_layout(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO invoice_printer DO ALSO SELECT update_te(old.te_id);

CREATE TABLE inventory (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    status inventory_status NOT NULL,
    open_date timestamp NOT NULL,
    close_date timestamp,
    invoice_number integer CONSTRAINT valid_invoice_number
        CHECK (invoice_number > 0 AND invoice_number <= 999999999),
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    responsible_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO inventory DO ALSO SELECT update_te(old.te_id);

CREATE TABLE inventory_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_id uuid NOT NULL REFERENCES product(id) ON UPDATE CASCADE,
    recorded_quantity numeric(20, 3) CONSTRAINT positive_recorded_quantity
        CHECK (recorded_quantity >= 0),
    actual_quantity numeric(20, 3) CONSTRAINT positive_actual_quantity
        CHECK (actual_quantity >= 0),
    counted_quantity numeric(20, 3) CONSTRAINT positive_counted_quantity
        CHECK (counted_quantity >= 0),
    inventory_id uuid NOT NULL REFERENCES inventory(id) ON UPDATE CASCADE,
    reason text,
    product_cost numeric(20, 8) CONSTRAINT positive_product_cost
        CHECK (product_cost >= 0),
    is_adjusted boolean NOT NULL DEFAULT false,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    cfop_data_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO inventory_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE production_order (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    status production_order_status NOT NULL,
    open_date timestamp,
    close_date timestamp,
    expected_start_date timestamp,
    start_date timestamp,
    cancel_date timestamp,
    description text,
    responsible_id uuid REFERENCES employee(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO production_order DO ALSO SELECT update_te(old.te_id);

CREATE TABLE production_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
       CHECK (quantity >= 0),
    produced numeric(20, 3) DEFAULT 0 CONSTRAINT positive_produced
       CHECK (produced >= 0),
    lost numeric(20, 3) DEFAULT 0 CONSTRAINT positive_lost
       CHECK (lost >= 0),
    product_id uuid REFERENCES product(id) ON UPDATE CASCADE,
    order_id uuid REFERENCES production_order(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO production_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE production_material (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    needed numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (needed > 0),
    consumed numeric(20, 3) DEFAULT 0 CONSTRAINT positive_consumed
        CHECK (consumed >= 0),
    allocated numeric(20, 3) DEFAULT 0 CONSTRAINT positive_allocated
        CHECK (allocated >= 0),
    to_purchase numeric(20, 3) CONSTRAINT positive_purchase_quantity
        CHECK (to_purchase >= 0),
    to_make numeric(20, 3) CONSTRAINT positive_make_quantity
        CHECK (to_make >= 0),
    lost numeric(20, 3) DEFAULT 0 CONSTRAINT positive_lost
        CHECK (lost >= 0),
    order_id uuid REFERENCES production_order(id) ON UPDATE CASCADE,
    product_id uuid REFERENCES product(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO production_material DO ALSO SELECT update_te(old.te_id);

CREATE TABLE production_service (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    service_id uuid REFERENCES service(id) ON UPDATE CASCADE,
    order_id uuid REFERENCES production_order(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO production_service DO ALSO SELECT update_te(old.te_id);

CREATE TABLE loan (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    open_date timestamp,
    close_date timestamp,
    expire_date timestamp,
    status loan_status NOT NULL,
    notes text,
    removed_by text,
    client_id uuid REFERENCES client(id) ON UPDATE CASCADE,
    client_category_id uuid REFERENCES client_category(id) ON UPDATE CASCADE,
    responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO loan DO ALSO SELECT update_te(old.te_id);

CREATE TABLE loan_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    sale_quantity numeric(20, 3) CONSTRAINT positive_sale_quantity
        CHECK (sale_quantity >= 0),
    return_quantity numeric(20, 3) CONSTRAINT positive_return_quantity
        CHECK (return_quantity >= 0),
    price numeric(20, 2) CONSTRAINT positive_price
        CHECK (price >= 0),
    base_price numeric(20, 2) CONSTRAINT positive_base_price
        CHECK (base_price >= 0),
    loan_id uuid REFERENCES loan(id) ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO loan_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE stock_decrease (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    confirm_date timestamp,
    status stock_decrease_status NOT NULL,
    invoice_number integer,
    reason text,
    notes text,
    responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    removed_by_id uuid REFERENCES employee(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    person_id uuid REFERENCES person(id) ON UPDATE CASCADE,
    cfop_id uuid REFERENCES cfop_data(id) ON UPDATE CASCADE,
    group_id uuid REFERENCES payment_group(id) ON UPDATE CASCADE,
    cost_center_id uuid REFERENCES cost_center(id) ON UPDATE CASCADE,
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO stock_decrease DO ALSO SELECT update_te(old.te_id);

CREATE TABLE stock_decrease_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
       CHECK (quantity >= 0),
    cost numeric(20, 8) DEFAULT 0,
    stock_decrease_id uuid REFERENCES stock_decrease(id) ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO stock_decrease_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE work_order_category (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    name text UNIQUE NOT NULL,
    color text
);
CREATE RULE update_te AS ON UPDATE TO work_order_category DO ALSO SELECT update_te(old.te_id);

CREATE TABLE work_order (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    identifier serial NOT NULL,
    status work_order_status NOT NULL,
    description text,
    estimated_hours numeric(10,2),
    estimated_cost numeric(20,2),
    estimated_start timestamp,
    estimated_finish timestamp,
    open_date timestamp,
    approve_date timestamp,
    finish_date timestamp,
    is_rejected boolean NOT NULL DEFAULT FALSE,
    defect_reported text,
    defect_detected text,
    quantity integer DEFAULT 1,
    branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    quote_responsible_id uuid REFERENCES employee(id) ON UPDATE CASCADE,
    execution_responsible_id uuid REFERENCES employee(id) ON UPDATE CASCADE,
    category_id uuid REFERENCES work_order_category(id) ON UPDATE CASCADE,
    client_id uuid REFERENCES client(id) ON UPDATE CASCADE,
    sale_id uuid REFERENCES sale(id) ON UPDATE CASCADE,
    current_branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE,
    execution_branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE,
    supplier_order text;
    UNIQUE (identifier, branch_id)
);
CREATE RULE update_te AS ON UPDATE TO work_order DO ALSO SELECT update_te(old.te_id);

CREATE TABLE work_order_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    quantity numeric(20,3),
    quantity_decreased numeric(20,3),
    price numeric(20,2),
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    sale_item_id uuid REFERENCES sale_item(id) ON UPDATE CASCADE,
    order_id uuid REFERENCES work_order(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO work_order_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE work_order_package (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    identifier text NOT NULL,
    status work_order_package_status NOT NULL,
    send_date timestamp,
    receive_date timestamp,
    send_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    receive_responsible_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    destination_branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE,
    source_branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    CONSTRAINT different_branches CHECK (source_branch_id != destination_branch_id)
);
CREATE RULE update_te AS ON UPDATE TO work_order_package DO ALSO SELECT update_te(old.te_id);

CREATE TABLE work_order_package_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    order_id uuid NOT NULL REFERENCES work_order(id) ON UPDATE CASCADE,
    package_id uuid NOT NULL REFERENCES work_order_package(id) ON UPDATE CASCADE,
    UNIQUE (order_id, package_id)
);
CREATE RULE update_te AS ON UPDATE TO work_order_package_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE work_order_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    date timestamp NOT NULL,
    what text NOT NULL,
    old_value text,
    new_value text,
    notes text,
    user_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,
    work_order_id uuid NOT NULL REFERENCES work_order(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO work_order_history DO ALSO SELECT update_te(old.te_id);

CREATE TABLE account_transaction (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    code text,
    operation_type account_transaction_operation_type NOT NULL,
    value numeric(20, 2) CONSTRAINT positive_value
        CHECK (value >= 0),
    source_account_id uuid REFERENCES account(id) ON UPDATE CASCADE NOT NULL,
    account_id uuid REFERENCES account(id) ON UPDATE CASCADE NOT NULL,
    date timestamp NOT NULL,
    payment_id uuid REFERENCES payment(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO account_transaction DO ALSO SELECT update_te(old.te_id);

CREATE TABLE ui_form (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    form_name text UNIQUE
);
CREATE RULE update_te AS ON UPDATE TO ui_form DO ALSO SELECT update_te(old.te_id);

CREATE TABLE ui_field (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    description text,
    field_name text,
    mandatory boolean,
    visible boolean,
    ui_form_id uuid REFERENCES ui_form(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO ui_field DO ALSO SELECT update_te(old.te_id);

CREATE TABLE product_quality_test (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_id uuid REFERENCES product(id) ON UPDATE CASCADE,
    test_type product_quality_test_type NOT NULL,
    description text,
    notes text,
    success_value text
);
CREATE RULE update_te AS ON UPDATE TO product_quality_test DO ALSO SELECT update_te(old.te_id);

CREATE TABLE production_produced_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    order_id uuid REFERENCES production_order(id) ON UPDATE CASCADE,
    product_id uuid REFERENCES product(id) ON UPDATE CASCADE,
    produced_by_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    produced_date timestamp,
    serial_number integer,
    entered_stock boolean,
    test_passed boolean,
    UNIQUE (product_id, serial_number)
);
CREATE RULE update_te AS ON UPDATE TO production_produced_item DO ALSO SELECT update_te(old.te_id);

CREATE TABLE production_item_quality_result (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),

    produced_item_id uuid REFERENCES production_produced_item(id) ON UPDATE CASCADE,
    quality_test_id uuid REFERENCES product_quality_test(id) ON UPDATE CASCADE,
    tested_by_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    tested_date timestamp,

    result_value text,
    test_passed boolean
);
CREATE RULE update_te AS ON UPDATE TO production_item_quality_result DO ALSO SELECT update_te(old.te_id);

-- TODO: Mudar o nome identifier
CREATE TABLE credit_check_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    creation_date timestamp,
    check_date timestamp,
    identifier text,
    status credit_check_status NOT NULL,
    notes text,
    client_id uuid REFERENCES client(id) ON UPDATE CASCADE,
    user_id uuid REFERENCES login_user(id) ON UPDATE CASCADE
);
CREATE RULE update_te AS ON UPDATE TO credit_check_history DO ALSO SELECT update_te(old.te_id);


-- Add new tables above this line when creating a new schema generation,
-- unless they are referenced by other tables above.

-- Finally create the system_table which we use to verify that the schema
-- is properly created.

CREATE TABLE system_table (
    id serial NOT NULL PRIMARY KEY,
    updated timestamp,
    patchlevel integer CONSTRAINT positive_patchlevel
        CHECK (patchlevel >= 0),
    generation integer CONSTRAINT positive_generation
        CHECK (generation >= 0)
);

INSERT INTO system_table (updated, patchlevel, generation)
     VALUES (CURRENT_TIMESTAMP, 0, 6);
