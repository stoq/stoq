--
-- Copyright (C) 2006-2011 Async Open Source
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

--
-- Tables
--

CREATE TABLE transaction_entry (
    id serial NOT NULL PRIMARY KEY,
    te_time timestamp NOT NULL,
    user_id integer,
    station_id integer,
    "type" integer
);

CREATE TABLE person (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    phone_number text,
    mobile_number text,
    fax_number text,
    email text,
    notes text
);

CREATE TABLE client_category (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text UNIQUE
);

CREATE TABLE person_adapt_to_client (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
    days_late integer CONSTRAINT positive_days_late
        CHECK (days_late >= 0),
    credit_limit numeric(20, 2) CONSTRAINT positive_credit_limit
        CHECK (credit_limit >= 0)
        DEFAULT 0,
    original_id bigint UNIQUE REFERENCES person(id),
    category_id bigint REFERENCES client_category(id)
);

CREATE TABLE person_adapt_to_company (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    cnpj text,
    fancy_name text,
    state_registry text,
    city_registry text,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_credit_provider (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    provider_type integer CONSTRAINT valid_provider_type
        CHECK (provider_type >= 0 AND provider_type < 2),
    payment_day integer CONSTRAINT valid_payment_day
        CHECK (payment_day <= 28),
    closing_day integer CONSTRAINT valid_closing_day
        CHECK (closing_day <= 28),
    max_installments integer CONSTRAINT valid_max_installments
        CHECK (max_installments > 0),
    credit_installments_provider_fee numeric(10, 2) NOT NULL DEFAULT 0
       CONSTRAINT valid_installments_provider_fee
       CHECK (credit_installments_provider_fee >= 0 AND
              credit_installments_provider_fee <= 100),
    credit_installments_store_fee numeric(10, 2) NOT NULL DEFAULT 0
       CONSTRAINT valid_installments_store_fee
       CHECK (credit_installments_store_fee >= 0 AND
       credit_installments_store_fee <= 100),
    credit_fee numeric(10, 2) NOT NULL DEFAULT 0
       CONSTRAINT valid_credit_fee
       CHECK (credit_fee >= 0 AND credit_fee <= 100),
    debit_fee numeric(10, 2) NOT NULL DEFAULT 0
       CONSTRAINT valid_debit_fee
       CHECK (debit_fee >= 0 AND debit_fee <= 100),
    debit_pre_dated_fee numeric(10, 2) NOT NULL DEFAULT 0
       CONSTRAINT positive_debit_pre_dated
       CHECK (debit_pre_dated_fee >= 0 AND
              debit_pre_dated_fee <= 100),
    monthly_fee numeric(20, 2) CONSTRAINT positive_monthly_fee
        CHECK (monthly_fee >= 0)
        NOT NULL DEFAULT 0,
    short_name text,
    provider_id text,
    open_contract_date timestamp,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE city_location (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    country text,
    city text,
    state text,
    UNIQUE(country, state, city)
);

CREATE TABLE person_adapt_to_individual (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    cpf text,
    rg_number text,
    birth_date timestamp,
    occupation text,
    marital_status integer CONSTRAINT valid_marital_status
        CHECK (marital_status >= 0 AND marital_status < 6),
    father_name text,
    mother_name text,
    rg_expedition_date timestamp,
    rg_expedition_local text,
    gender integer CONSTRAINT valid_gender
        CHECK (gender >= 0 AND gender < 2),
    spouse_name text,
    birth_location_id bigint REFERENCES city_location(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE employee_role (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text NOT NULL UNIQUE
);

CREATE TABLE work_permit_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    series_number text,
    pis_number text,
    pis_bank text,
    pis_registry_date timestamp
);

CREATE TABLE military_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    series_number text,
    category text
);

CREATE TABLE voter_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    section text,
    "zone" text
);

CREATE TABLE bank_account (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    -- bank_account bigint UNIQUE REFERENCES account(id),
    bank_number integer CONSTRAINT positive_bank_number
        CHECK (bank_number >= 0),
    bank_branch text,
    bank_account text,
    bank_type bigint
);

CREATE TABLE bill_option (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    option text,
    value text,
    bank_account_id bigint REFERENCES bank_account(id)
);

CREATE TABLE person_adapt_to_employee (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    admission_date timestamp,
    expire_vacation timestamp,
    salary numeric(20, 2),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
    registry_number text,
    education_level text,
    dependent_person_number integer CONSTRAINT positive_dependent_person_number
        CHECK (dependent_person_number >= 0),
    role_id bigint REFERENCES employee_role(id),
    workpermit_data_id bigint REFERENCES work_permit_data(id),
    military_data_id bigint REFERENCES military_data(id),
    voter_data_id bigint REFERENCES voter_data(id),
    bank_account_id bigint REFERENCES bank_account(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_branch (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    manager_id bigint REFERENCES person_adapt_to_employee(id),
    is_active boolean,
    crt integer DEFAULT 1,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_sales_person (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    comission numeric(10, 2) CONSTRAINT positive_comission
        CHECK (comission >= 0),
    comission_type integer CONSTRAINT check_valid_comission_type
        CHECK (comission_type >= 0 AND comission_type < 7),
    is_active boolean,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_supplier (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 3),
    product_desc text,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_transporter (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    open_contract_date timestamp,
    freight_percentage numeric(10, 2) NOT NULL
        CONSTRAINT positive_freight_percentage
        CHECK (freight_percentage >= 0),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE user_profile (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text
);

CREATE TABLE person_adapt_to_user (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    username text NOT NULL UNIQUE,
    "password" text,
    is_active boolean,
    profile_id bigint REFERENCES user_profile(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE product_tax_template (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    tax_type integer
);


CREATE TABLE sellable_tax_constant (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    tax_type integer CONSTRAINT valid_tax_type
        CHECK (tax_type >= 41 AND tax_type < 46),
    tax_value numeric(10, 2)
);

CREATE TABLE sellable_category (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    suggested_markup numeric(10, 2),
    salesperson_commission numeric(10, 2),
    category_id bigint REFERENCES sellable_category(id),
    tax_constant_id bigint REFERENCES sellable_tax_constant(id)
);

CREATE TABLE sellable_unit (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    unit_index integer CONSTRAINT positive_unit_index
        CHECK(unit_index >= 0),
    allow_fraction boolean DEFAULT TRUE
);

CREATE TABLE cfop_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    code text,
    description text
);

CREATE TABLE sellable (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    barcode text,
    code text,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
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
    unit_id bigint REFERENCES sellable_unit(id),
    category_id bigint REFERENCES sellable_category(id),
    tax_constant_id bigint REFERENCES sellable_tax_constant(id),
    default_sale_cfop_id bigint REFERENCES cfop_data(id)
);

CREATE TABLE product_icms_template (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    product_tax_template_id bigint UNIQUE REFERENCES product_tax_template(id),
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

CREATE TABLE product_ipi_template (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    product_tax_template_id bigint UNIQUE REFERENCES product_tax_template(id),
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

CREATE TABLE product (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    consignment boolean NOT NULL DEFAULT FALSE,
    full_image bytea,
    image bytea,
    location text,
    part_number text,
    manufacturer text,
    ncm text,
    ex_tipi text,
    genero text,
    production_time integer DEFAULT 0,
    is_composed boolean DEFAULT FALSE,
    width numeric(10, 2) CONSTRAINT positive_width
        CHECK (width >= 0),
    height numeric(10, 2) CONSTRAINT positive_height
        CHECK (height >= 0),
    depth numeric(10, 2) CONSTRAINT positive_depth
        CHECK (depth >= 0),
    weight numeric(10, 2) CONSTRAINT positive_weight
        CHECK (weight >= 0),
    icms_template_id bigint REFERENCES product_icms_template(id),
    ipi_template_id bigint REFERENCES product_ipi_template(id),
    sellable_id bigint REFERENCES sellable(id)
);

CREATE TABLE product_component (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    product_id bigint REFERENCES product(id),
    component_id bigint REFERENCES product(id),
    design_reference text,
    quantity numeric(20, 3)
        CONSTRAINT positive_quantity CHECK (quantity > 0),
        CONSTRAINT different_products CHECK (product_id != component_id)
);

CREATE TABLE product_adapt_to_storable (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES product(id),
    minimum_quantity numeric(20, 3) DEFAULT 0
        CONSTRAINT positive_minimum_quantity CHECK (minimum_quantity >= 0),
    maximum_quantity numeric(20, 3) DEFAULT 0
        CONSTRAINT positive_maximum_quantity CHECK (maximum_quantity >= 0)
);

CREATE TABLE product_supplier_info (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    base_cost numeric(20, 8) CONSTRAINT positive_base_cost
        CHECK (base_cost >= 0),
    notes text,
    is_main_supplier boolean,
    icms numeric(10, 2) CONSTRAINT positive_icms
        CHECK (icms >= 0),
    lead_time integer DEFAULT 1 CONSTRAINT positive_lead_time
        CHECK (lead_time > 0),
    minimum_purchase numeric(20, 3) DEFAULT 1,
    supplier_id bigint NOT NULL REFERENCES person_adapt_to_supplier(id),
    product_id bigint NOT NULL REFERENCES product(id)
);

CREATE TABLE product_history (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
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
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    sellable_id bigint REFERENCES sellable(id)
);

CREATE TABLE service (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    sellable_id bigint REFERENCES sellable(id),
    image bytea
);

CREATE TABLE payment_renegotiation (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
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
    client_id bigint REFERENCES person_adapt_to_client(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id)
    -- group_id bigint REFERENCES payment_group(id)
);

CREATE TABLE payment_group (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
    payer_id bigint REFERENCES person(id),
    renegotiation_id bigint REFERENCES payment_renegotiation(id),
    recipient_id bigint REFERENCES person(id)
);

ALTER TABLE payment_renegotiation ADD COLUMN group_id bigint
    REFERENCES payment_group(id);

CREATE TABLE payment_flow_history (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
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

CREATE TABLE purchase_order (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 6),
    open_date timestamp,
    quote_deadline timestamp,
    expected_receival_date timestamp,
    expected_pay_date timestamp,
    receival_date timestamp,
    confirm_date timestamp,
    notes text,
    salesperson_name text,
    freight_type integer CONSTRAINT valid_freight_type
        CHECK (freight_type >= 0 AND freight_type < 2),
    expected_freight numeric(20, 2) CONSTRAINT positive_expected_freight
        CHECK (expected_freight >= 0),
    surcharge_value numeric(20, 2) CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0),
    discount_value numeric(20, 2) CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    consigned boolean DEFAULT FALSE,
    supplier_id bigint REFERENCES person_adapt_to_supplier(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    transporter_id bigint REFERENCES person_adapt_to_transporter(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    group_id bigint REFERENCES payment_group(id)
);

CREATE TABLE purchase_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    quantity_received numeric(20, 3) CONSTRAINT positive_quantity_received
        CHECK (quantity_received >= 0),
    base_cost numeric(20, 8) CONSTRAINT positive_base_cost
        CHECK (base_cost >= 0),
    cost numeric(20, 8) CONSTRAINT positive_cost
        CHECK (cost >= 0),
    expected_receival_date timestamp,
    sellable_id bigint REFERENCES sellable(id),
    order_id bigint REFERENCES purchase_order(id),
    quantity_sold numeric(20, 3) CONSTRAINT positive_quantity_sold
        CHECK (quantity_sold >= 0 AND
               quantity_sold <= quantity_received)
        DEFAULT 0,
    quantity_returned numeric(20, 3) CONSTRAINT positive_quantity_returned
        CHECK (quantity_returned >= 0 AND
               quantity_returned <= quantity_received - quantity_sold)
        DEFAULT 0
);

CREATE TABLE quote_group (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
);

CREATE TABLE quotation (
     id serial NOT NULL PRIMARY KEY,
     te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
     te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

     purchase_id bigint REFERENCES purchase_order(id),
     group_id bigint REFERENCES quote_group(id)
);

CREATE TABLE branch_station (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text UNIQUE,
    is_active boolean,
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE till (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 3),
    initial_cash_amount numeric(20, 2) CONSTRAINT positive_initial_cash_amount
        CHECK (initial_cash_amount >= 0),
    final_cash_amount numeric(20, 2) CONSTRAINT positive_final_cash_amount
        CHECK (final_cash_amount >= 0),
    opening_date timestamp,
    closing_date timestamp,
    station_id bigint REFERENCES branch_station(id)
);

CREATE TABLE client_category_price (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    sellable_id bigint REFERENCES sellable(id),
    category_id bigint REFERENCES client_category(id),
    price numeric(10,2) CONSTRAINT positive_price CHECK (price >= 0),
    max_discount numeric(10,2),
    commission numeric(10,2),
    UNIQUE (sellable_id, category_id)
);

CREATE TABLE sale (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    coupon_id integer,
    invoice_number integer CONSTRAINT positive_invoice_number
        CHECK (invoice_number > 0 AND invoice_number < 999999)
        DEFAULT NULL UNIQUE,
    service_invoice_number integer,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 8),
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
    notes text,
    client_id bigint REFERENCES person_adapt_to_client(id),
    client_category_id bigint REFERENCES client_category(id),
    cfop_id bigint REFERENCES cfop_data(id),
    salesperson_id bigint REFERENCES person_adapt_to_sales_person(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    group_id bigint REFERENCES payment_group(id),
    transporter_id bigint REFERENCES person_adapt_to_transporter(id)
);

CREATE TABLE sale_item_icms (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
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

CREATE TABLE sale_item_ipi (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
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

CREATE TABLE sale_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    base_price numeric(20, 2) CONSTRAINT positive_base_price
        CHECK (base_price >= 0),
    price numeric(20, 2) CONSTRAINT positive_price
        CHECK (price >= 0),
    notes text,
    estimated_fix_date timestamp,
    completion_date timestamp,
    average_cost numeric(20, 8) DEFAULT 0,
    sale_id bigint REFERENCES sale(id),
    sellable_id bigint REFERENCES sellable(id),
    icms_info_id bigint REFERENCES sale_item_icms(id),
    ipi_info_id bigint REFERENCES sale_item_ipi(id),
    cfop_id bigint REFERENCES cfop_data(id)
);

CREATE TABLE sale_item_adapt_to_delivery (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    address text,
    original_id bigint UNIQUE REFERENCES sale_item(id)
);

CREATE TABLE product_stock_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    stock_cost numeric(20, 8),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    logic_quantity numeric(20, 3) CONSTRAINT positive_logic_quantity
        CHECK (logic_quantity >= 0),
    storable_id bigint REFERENCES product_adapt_to_storable(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE address (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    street text,
    streetnumber integer CONSTRAINT positive_streetnumber
        CHECK (streetnumber > 0),
    district text,
    postal_code text,
    complement text,
    is_main_address boolean,
    person_id bigint REFERENCES person(id),
    city_location_id bigint REFERENCES city_location(id)
);

CREATE TABLE branch_synchronization (
    id serial NOT NULL PRIMARY KEY,
    sync_time timestamp  NOT NULL,
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    policy text NOT NULL
);

CREATE TABLE calls (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp,
    message text,
    description text,
    person_id bigint REFERENCES person(id),
    attendant_id bigint REFERENCES person_adapt_to_user(id)
);

CREATE TABLE card_installment_settings (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    payment_day integer
        CHECK (payment_day <= 28),
    closing_day integer
        CHECK (closing_day <= 28)
);

CREATE TABLE card_installments_provider_details (
    id serial NOT NULL PRIMARY KEY,
    max_installments_number integer CONSTRAINT positive_max_installments_number
        CHECK (max_installments_number > 0),
    installment_settings_id bigint REFERENCES card_installment_settings(id)
);

CREATE TABLE card_installments_store_details (
    id serial NOT NULL PRIMARY KEY,
    max_installments_number integer CONSTRAINT positive_max_installments_number
        CHECK (max_installments_number > 0),
    installment_settings_id bigint REFERENCES card_installment_settings(id)
);

CREATE TABLE account (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    account_type integer,
    description text NOT NULL,
    code text,
    parent_id bigint REFERENCES account(id),
    station_id bigint REFERENCES branch_station(id)
);

ALTER TABLE bank_account ADD COLUMN account_id bigint
    UNIQUE REFERENCES account(id);

CREATE TABLE payment_method (
    id serial NOT NULL PRIMARY KEY,
    is_active boolean,
    daily_penalty numeric(10, 2) CONSTRAINT valid_daily_penalty
        CHECK (daily_penalty >= 0 AND daily_penalty <= 100),
    interest numeric(10, 2) CONSTRAINT interest_percent
        CHECK (interest >= 0 AND interest <= 100),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    method_name text UNIQUE,
    description text,
    payment_day integer CONSTRAINT valid_payment_day
        CHECK (payment_day >= 1 AND payment_day <= 28),
    closing_day integer CONSTRAINT valid_closing_day
        CHECK (closing_day >= 1 AND closing_day <= 28),
    max_installments integer CONSTRAINT positive_max_installments
        CHECK (max_installments > 0),
    destination_account_id bigint REFERENCES account(id) NOT NULL
);

CREATE TABLE payment_category (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text UNIQUE,
    color text
);

CREATE TABLE payment (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 6),
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
    method_id bigint REFERENCES payment_method(id),
    group_id bigint REFERENCES payment_group(id),
    till_id bigint REFERENCES till(id),
    category_id bigint REFERENCES payment_category(id)
);

CREATE TABLE payment_comment (
    id serial NOT NULL PRIMARY KEY,

    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    date timestamp,
    comment text,
    payment_id bigint REFERENCES payment(id),
    author_id bigint REFERENCES person_adapt_to_user(id)
);

CREATE TABLE check_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    payment_id bigint REFERENCES payment(id),
    bank_account_id bigint REFERENCES bank_account(id)
);

CREATE TABLE credit_card_details (
    id serial NOT NULL PRIMARY KEY,
    installment_settings_id bigint REFERENCES card_installment_settings(id)
);

CREATE TABLE debit_card_details (
    id serial NOT NULL PRIMARY KEY,
    receive_days integer CONSTRAINT positive_receive_days
        CHECK (receive_days >= 0)
);

CREATE TABLE credit_card_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    auth integer DEFAULT NULL,
    nsu integer DEFAULT NULL,
    installments integer DEFAULT 1,
    card_type integer CONSTRAINT valid_status
        CHECK (card_type >= 0 AND card_type < 5),
    entrance_value numeric(20, 2) DEFAULT 0,
    fee numeric(10, 2) NOT NULL DEFAULT 0,
    fee_value numeric(20, 2) DEFAULT 0,
    payment_id bigint UNIQUE REFERENCES payment(id),
    provider_id bigint REFERENCES person_adapt_to_credit_provider(id)
);

CREATE TABLE payment_change_history (
    id serial NOT NULL PRIMARY KEY,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    change_reason text,
    last_due_date timestamp,
    change_date timestamp,
    new_due_date timestamp,
    last_status integer,
    new_status integer,
    payment_id bigint REFERENCES payment(id)
);

CREATE TABLE fiscal_sale_history (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    sale_id bigint REFERENCES sale(id),
    document_type integer CONSTRAINT valid_type
        CHECK (document_type = 0 OR document_type = 1),
    document text,
    coo integer,
    document_counter integer
);

CREATE TABLE device_settings (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    "type" integer CONSTRAINT valid_type
        CHECK (type >= 0 AND type < 4),
    brand text,
    model text,
    device_name text,
    is_active boolean,
    station_id bigint REFERENCES branch_station(id),
    UNIQUE (device_name, station_id)
);


-- FIXME: This should be in ecf plugin
CREATE TABLE device_constant (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
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
    device_settings_id bigint REFERENCES device_settings(id)
    -- FIXME: This is needed by the ECF plugin which doesn't have
    --        infrastructure to deal with schema generations
    ,is_valid_model bool
);

CREATE TABLE employee_role_history (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    began timestamp,
    ended timestamp,
    salary numeric(20, 2),
    role_id bigint REFERENCES employee_role(id),
    employee_id bigint REFERENCES person_adapt_to_employee(id),
    is_active boolean
);

CREATE TABLE liaison (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    phone_number text,
    person_id bigint REFERENCES person(id)
);

CREATE TABLE parameter_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    field_name text NOT NULL UNIQUE,
    field_value text,
    is_editable boolean
);

CREATE TABLE payment_adapt_to_in_payment (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment(id)
);

CREATE TABLE payment_adapt_to_out_payment (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment(id)
);

CREATE TABLE profile_settings (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    app_dir_name text,
    has_permission boolean,
    user_profile_id bigint REFERENCES user_profile(id)
);

CREATE TABLE receiving_order (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 2),
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
    freight_type integer DEFAULT 0,
    invoice_number integer CONSTRAINT valid_invoice_number
       CHECK (invoice_number >= 1 AND invoice_number <= 999999),
    invoice_total numeric(20, 2),
    cfop_id bigint REFERENCES cfop_data(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    supplier_id bigint REFERENCES person_adapt_to_supplier(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    purchase_id bigint NOT NULL REFERENCES purchase_order(id),
    transporter_id bigint REFERENCES person_adapt_to_transporter(id),
    secure_value numeric(20, 2) CONSTRAINT positive_secure_value
        CHECK (secure_value >= 0),
    expense_value numeric(20, 2) CONSTRAINT positive_expense_value
        CHECK (expense_value >= 0)
);

CREATE TABLE receiving_order_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    cost numeric(20, 8) CONSTRAINT positive_cost
        CHECK (cost >= 0),
    sellable_id bigint REFERENCES sellable(id),
    receiving_order_id bigint REFERENCES receiving_order(id),
    purchase_item_id bigint REFERENCES purchase_item(id)
);

CREATE TABLE renegotiation_data (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    reason text,
    paid_total numeric(20, 2)
        CHECK (paid_total >= 0),
    invoice_number integer,
    penalty_value numeric(20, 2),
    responsible_id bigint REFERENCES person(id),
    new_order_id bigint REFERENCES sale(id),
    sale_id bigint UNIQUE REFERENCES sale(id)
);

CREATE TABLE delivery_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    sellable_id bigint REFERENCES sellable(id),
    delivery_id bigint REFERENCES sale_item_adapt_to_delivery(id)
);

CREATE TABLE till_entry (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp,
    description text,
    value numeric(20, 2),
    till_id bigint NOT NULL REFERENCES till(id),
    payment_id integer
);

CREATE TABLE fiscal_book_entry (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    entry_type integer,
    icms_value numeric(20, 2),
    iss_value numeric(20, 2),
    ipi_value numeric(20, 2),
    date timestamp,
    is_reversal boolean,
    invoice_number integer CONSTRAINT positive_invoice_number
        CHECK (invoice_number >= 0),
    cfop_id bigint REFERENCES cfop_data(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    drawee_id bigint REFERENCES person(id),
    payment_group_id bigint REFERENCES payment_group(id)
);

CREATE TABLE fiscal_day_history (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    emission_date date CONSTRAINT past_emission_date
        CHECK (emission_date <= DATE(NOW())),
    station_id bigint REFERENCES branch_station(id),
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

CREATE TABLE fiscal_day_tax (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    code text CONSTRAINT valid_code
        CHECK (code ~ '^([0-9][0-9][0-9][0-9]|I|F|N|ISS|DESC|CANC)$'),
    value numeric(20, 2) CONSTRAINT positive_value
        CHECK (value >= 0),
    fiscal_day_history_id bigint REFERENCES fiscal_day_history(id),
    type text
);


CREATE TABLE installed_plugin (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    plugin_name text UNIQUE NOT NULL,
    plugin_version integer CONSTRAINT positive_plugin_version
        CHECK (plugin_version >= 0)
);

CREATE TABLE commission_source (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    direct_value numeric(10, 2) NOT NULL CONSTRAINT positive_value
        CHECK (direct_value >= 0),
    installments_value numeric(10, 2) NOT NULL CONSTRAINT positive_installments_value
        CHECK (installments_value >= 0),
    category_id bigint REFERENCES sellable_category(id),
    sellable_id bigint REFERENCES sellable(id),
    -- only one reference will exist at a time: category_id or sellable_id
    -- never both or none of them
    CONSTRAINT check_exist_one_fkey
        CHECK (category_id IS NOT NULL AND sellable_id IS NULL OR
               category_id IS NULL AND sellable_id IS NOT NULL)
);

CREATE TABLE commission (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    value numeric(20, 2) NOT NULL,
    commission_type integer NOT NULL,
    salesperson_id bigint NOT NULL REFERENCES person_adapt_to_sales_person(id),
    sale_id bigint NOT NULL REFERENCES sale(id),
    payment_id bigint NOT NULL UNIQUE REFERENCES payment(id)
);

CREATE TABLE transfer_order (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    open_date timestamp NOT NULL,
    receival_date timestamp,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 2),
    source_branch_id bigint NOT NULL REFERENCES person_adapt_to_branch(id),
    destination_branch_id bigint NOT NULL REFERENCES person_adapt_to_branch(id),
    source_responsible_id bigint NOT NULL REFERENCES person_adapt_to_employee(id),
    destination_responsible_id bigint NOT NULL REFERENCES person_adapt_to_employee(id)
);

CREATE TABLE transfer_order_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    sellable_id bigint NOT NULL REFERENCES sellable(id),
    transfer_order_id bigint NOT NULL REFERENCES transfer_order(id),
    quantity numeric(20, 3) NOT NULL CONSTRAINT positive_quantity
        CHECK (quantity > 0)
);

CREATE TABLE invoice_layout (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description varchar NOT NULL,
    width bigint NOT NULL CONSTRAINT positive_width
        CHECK (width > 0),
    height bigint NOT NULL CONSTRAINT positive_height
        CHECK (height > 0)
);

CREATE TABLE invoice_field (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    field_name varchar NOT NULL,
    layout_id bigint REFERENCES invoice_layout(id),
    x bigint NOT NULL CONSTRAINT positive_x
        CHECK (x >= 0),
    y bigint NOT NULL CONSTRAINT positive_y
        CHECK (y >= 0),
    width bigint NOT NULL CONSTRAINT positive_width
        CHECK (width > 0),
    height bigint NOT NULL CONSTRAINT positive_height
        CHECK (height > 0)
);

CREATE TABLE invoice_printer (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    device_name varchar NOT NULL,
    description varchar NOT NULL,
    station_id bigint REFERENCES branch_station(id),
    layout_id bigint REFERENCES invoice_layout(id)
);

CREATE TABLE inventory (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 and status < 3),
    open_date timestamp NOT NULL,
    close_date timestamp,
    invoice_number integer CONSTRAINT positive_invoice_number
        CHECK (invoice_number > 0  and invoice_number < 999999),
    branch_id bigint NOT NULL REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE inventory_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    product_id bigint NOT NULL REFERENCES product(id),
    recorded_quantity numeric(20, 3) CONSTRAINT positive_recorded_quantity
        CHECK (recorded_quantity >= 0),
    actual_quantity numeric(20, 3) CONSTRAINT positive_actual_quantity
        CHECK (actual_quantity >= 0),
    inventory_id bigint NOT NULL REFERENCES inventory(id),
    reason text,
    product_cost numeric(20, 8) CONSTRAINT positive_product_cost
        CHECK (product_cost >= 0),
    cfop_data_id bigint REFERENCES cfop_data(id)
);

CREATE TABLE production_order (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 5),
    open_date timestamp,
    close_date timestamp,
    expected_start_date timestamp,
    start_date timestamp,
    description text,
    responsible_id bigint REFERENCES person_adapt_to_employee(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE production_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
       CHECK (quantity >= 0),
    produced numeric(20, 3) DEFAULT 0 CONSTRAINT positive_produced
       CHECK (produced >= 0),
    lost numeric(20, 3) DEFAULT 0 CONSTRAINT positive_lost
       CHECK (lost >= 0),
    product_id bigint REFERENCES product(id),
    order_id bigint REFERENCES production_order(id)
);

CREATE TABLE production_material (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
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
    order_id bigint REFERENCES production_order(id),
    product_id bigint REFERENCES product(id)
);

CREATE TABLE production_service (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    service_id bigint REFERENCES service(id),
    order_id bigint REFERENCES production_order(id)
);

CREATE TABLE loan (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    open_date timestamp,
    close_date timestamp,
    expire_date timestamp,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 6),
    notes text,
    removed_by text,
    client_id bigint REFERENCES person_adapt_to_client(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE loan_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
        CHECK (quantity >= 0),
    sale_quantity numeric(20, 3) CONSTRAINT positive_sale_quantity
        CHECK (sale_quantity >= 0),
    return_quantity numeric(20, 3) CONSTRAINT positive_return_quantity
        CHECK (return_quantity >= 0),
    price numeric(20, 2) CONSTRAINT positive_price
        CHECK (price >= 0),
    loan_id bigint REFERENCES loan(id),
    sellable_id bigint REFERENCES sellable(id)
);

CREATE TABLE stock_decrease (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    confirm_date timestamp,
    status integer CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 8),
    reason text,
    notes text,
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    removed_by_id bigint REFERENCES person_adapt_to_employee(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    cfop_id bigint REFERENCES cfop_data(id)
);

CREATE TABLE stock_decrease_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(20, 3) CONSTRAINT positive_quantity
       CHECK (quantity >= 0),
    stock_decrease_id bigint REFERENCES stock_decrease(id),
    sellable_id bigint REFERENCES sellable(id)
);

CREATE TABLE account_transaction (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    code text,
    value numeric(20, 2) CONSTRAINT nonzero_value
        CHECK (value != 0),
    source_account_id bigint REFERENCES account(id) NOT NULL,
    account_id bigint REFERENCES account(id) NOT NULL,
    date timestamp NOT NULL,
    payment_id bigint REFERENCES payment(id)
);

CREATE TABLE ui_form (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    form_name text UNIQUE
);

CREATE TABLE ui_field (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    field_name text,
    mandatory boolean,
    visible boolean,
    ui_form_id bigint REFERENCES ui_form(id)
);

CREATE TABLE event (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp NOT NULL,
    event_type integer NOT NULL,
    description varchar NOT NULL
);

CREATE TABLE product_quality_test (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    product_id bigint REFERENCES product(id),
    test_type integer,
    description text,
    notes text,
    success_value text
);

CREATE TABLE production_produced_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    order_id bigint REFERENCES production_order(id),
    product_id bigint REFERENCES product(id),
    produced_by_id bigint REFERENCES person_adapt_to_user(id),
    produced_date timestamp,
    serial_number integer,
    entered_stock boolean,
    test_passed boolean,
    UNIQUE(product_id, serial_number)
);

CREATE TABLE production_item_quality_result (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    produced_item_id bigint REFERENCES production_produced_item(id),
    quality_test_id bigint REFERENCES product_quality_test(id),
    tested_by_id bigint REFERENCES person_adapt_to_user(id),
    tested_date timestamp,

    result_value text,
    test_passed boolean
);


-- Add new tables above this line when creating a new schema generation,
-- unless they are referenced by other tables above.

-- This is last to avoid cyclic references

ALTER TABLE transaction_entry
    ADD CONSTRAINT transaction_entry_user_id_fkey FOREIGN KEY
        (user_id) REFERENCES person_adapt_to_user (id),
    ADD CONSTRAINT transaction_entry_station_id_fkey FOREIGN KEY
        (station_id) REFERENCES branch_station (id);

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
     VALUES (CURRENT_TIMESTAMP, 0, 3);
