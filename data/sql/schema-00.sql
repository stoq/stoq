--
-- Copyright (C) 2006,2007 Async Open Source
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
-- Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
--                  Johan Dahlin                <jdahlin@async.com.br>
--

-- Schema shared between all databases we support

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
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    phone_number text,
    mobile_number text,
    fax_number text,
    email text,
    notes text
);

CREATE TABLE bank (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    short_name text,
    compensation_code text
);

CREATE TABLE person_adapt_to_bank_branch (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    bank_id bigint REFERENCES bank(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_branch (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    manager_id bigint REFERENCES person(id),
    is_active boolean,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_client (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    days_late integer,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_company (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    cnpj text,
    fancy_name text,
    state_registry text,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_credit_provider (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    provider_type integer,
    short_name text,
    provider_id text,
    open_contract_date timestamp,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE city_location (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    country text,
    city text,
    state text
);

CREATE TABLE person_adapt_to_individual (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    cpf text,
    rg_number text,
    birth_date timestamp,
    occupation text,
    marital_status integer,
    father_name text,
    mother_name text,
    rg_expedition_date timestamp,
    rg_expedition_local text,
    gender integer,
    spouse_name text,
    birth_location_id bigint REFERENCES city_location(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE employee_role (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text NOT NULL UNIQUE
);

CREATE TABLE work_permit_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
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
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    series_number text,
    category text
);

CREATE TABLE voter_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    section text,
    "zone" text
);

CREATE TABLE bank_account (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    bank_id integer,
    branch text,
    account text
);

CREATE TABLE person_adapt_to_employee (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    admission_date timestamp,
    expire_vacation timestamp,
    salary numeric(10,2),
    status integer,
    registry_number text,
    education_level text,
    dependent_person_number integer,
    role_id bigint REFERENCES employee_role(id),
    workpermit_data_id bigint REFERENCES work_permit_data(id),
    military_data_id bigint REFERENCES military_data(id),
    voter_data_id bigint REFERENCES voter_data(id),
    bank_account_id bigint REFERENCES bank_account(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_sales_person (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    comission numeric(10,2),
    comission_type integer,
    is_active boolean,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_supplier (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    status integer,
    product_desc text,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_transporter (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    open_contract_date timestamp,
    freight_percentage numeric(10,2),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE user_profile (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text
);

CREATE TABLE person_adapt_to_user (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    username text NOT NULL UNIQUE,
    "password" text,
    is_active boolean,
    profile_id bigint REFERENCES user_profile(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE product (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    image bytea
);

CREATE TABLE product_adapt_to_sellable (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES product(id)
);

CREATE TABLE product_adapt_to_storable (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint REFERENCES product(id)
);

CREATE TABLE product_supplier_info (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    base_cost numeric(10,2),
    notes text,
    is_main_supplier boolean,
    icms numeric(10,2),
    supplier_id bigint REFERENCES person_adapt_to_supplier(id),
    product_id bigint REFERENCES product(id)
);

CREATE TABLE service (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    image bytea
);

CREATE TABLE service_adapt_to_sellable (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES service(id)
);

CREATE TABLE base_sellable_info (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    price numeric(10,2),
    description text,
    max_discount numeric(10,2),
    commission numeric(10,2)
);

CREATE TABLE on_sale_info (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    on_sale_price numeric(10,2),
    on_sale_start_date timestamp,
    on_sale_end_date timestamp
);

CREATE TABLE asellable_category (
    -- Subclasses:
    --    base_sellable_category
    --    sellable_category
    id serial NOT NULL PRIMARY KEY,
    description text,
    suggested_markup numeric(10,2),
    salesperson_commission numeric(10,2),
    child_name character varying(255)
);

CREATE TABLE base_sellable_category (
    id serial NOT NULL PRIMARY KEY
);

CREATE TABLE sellable_category (
    id serial NOT NULL PRIMARY KEY,
    base_category_id bigint REFERENCES base_sellable_category(id)
);

CREATE TABLE sellable_unit (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    unit_index integer
);

CREATE TABLE sellable_tax_constant (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    tax_type integer,
    tax_value numeric(10,2)
);

CREATE TABLE asellable (
    -- Subclasses:
    --    product_adapt_to_sellable
    --    service_adapt_to_sellable
    --    gift_certificate_adapt_to_sellable
    id serial NOT NULL PRIMARY KEY,
    barcode text,
    status integer,
    cost numeric(10,2),
    notes text,
    unit_id bigint REFERENCES sellable_unit(id),
    base_sellable_info_id bigint REFERENCES base_sellable_info(id),
    on_sale_info_id bigint REFERENCES on_sale_info(id),
    category_id bigint REFERENCES sellable_category(id),
    tax_constant_id bigint REFERENCES sellable_tax_constant(id),
    child_name character varying(255)
);


CREATE TABLE purchase_order (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    open_date timestamp,
    quote_deadline timestamp,
    expected_receival_date timestamp,
    expected_pay_date timestamp,
    receival_date timestamp,
    confirm_date timestamp,
    notes text,
    salesperson_name text,
    freight_type integer,
    freight numeric(10,2),
    surcharge_value numeric(10,2),
    discount_value numeric(10,2),
    supplier_id bigint REFERENCES person_adapt_to_supplier(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    transporter_id bigint REFERENCES person_adapt_to_transporter(id)
);

CREATE TABLE purchase_item (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    quantity_received numeric(10,2) CONSTRAINT positive_quantity_received CHECK (quantity_received >= 0),
    base_cost numeric(10,2),
    cost numeric(10,2),
    sellable_id bigint REFERENCES asellable(id),
    order_id bigint REFERENCES purchase_order(id)
);

CREATE TABLE abstract_renegotiation_adapter (
    -- Subclasses:
    --    renegotiation_adapt_to_return_sale
    --    renegotiation_adapt_to_exchange
    --    renegotiation_adapt_to_change_installments
    id serial NOT NULL PRIMARY KEY,
    child_name character varying(255)
);

CREATE TABLE branch_station (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text UNIQUE,
    is_active boolean,
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE till (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    initial_cash_amount numeric(10,2),
    final_cash_amount numeric(10,2),
    opening_date timestamp,
    closing_date timestamp,
    station_id bigint REFERENCES branch_station(id)
);

CREATE TABLE cfop_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    code text,
    description text
);

CREATE TABLE sale (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    coupon_id integer,
    service_invoice_number integer,
    open_date timestamp,
    close_date timestamp,
    confirm_date timestamp,
    cancel_date timestamp,
    status integer,
    discount_value numeric(10,2),
    surcharge_value numeric(10,2),
    notes text,
    client_role integer,
    client_id bigint REFERENCES person_adapt_to_client(id),
    cfop_id bigint REFERENCES cfop_data(id),
    till_id bigint REFERENCES till(id),
    salesperson_id bigint REFERENCES person_adapt_to_sales_person(id),
    renegotiation_data_id bigint REFERENCES abstract_renegotiation_adapter(id)
);

CREATE TABLE sale_adapt_to_payment_group (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES sale(id)
);

CREATE TABLE asellable_item (
    -- Subclasses:
    --    product_sellable_item
    --    service_sellable_item
    --    gift_certificate_item
    id serial NOT NULL PRIMARY KEY,
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    base_price numeric(10,2),
    price numeric(10,2),
    sale_id bigint REFERENCES sale(id),
    sellable_id bigint REFERENCES asellable(id),
    child_name character varying(255)
);

CREATE TABLE abstract_stock_item (
    -- Subclasses:
    --    product_stock_item
    id serial NOT NULL PRIMARY KEY,
    stock_cost numeric(10,2),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    logic_quantity numeric(10,2) CONSTRAINT positive_logic_quantity CHECK (logic_quantity >= 0),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    child_name character varying(255)
);

CREATE TABLE product_stock_item (
    id serial NOT NULL PRIMARY KEY,
    storable_id bigint REFERENCES product_adapt_to_storable(id)
);

CREATE TABLE address (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    street text,
    number integer,
    district text,
    postal_code text,
    complement text,
    is_main_address boolean,
    person_id bigint REFERENCES person(id),
    city_location_id bigint REFERENCES city_location(id)
);

CREATE TABLE abstract_payment_group (
    -- Subclasses:
    --    sale_adapt_to_payment_group
    --    till_adapt_to_payment_group
    --    purchase_order_adapt_to_payment_group
    --    receiving_order_adapt_to_payment_group
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    open_date timestamp,
    close_date timestamp,
    cancel_date timestamp,
    default_method integer,
    installments_number integer,
    interval_type integer,
    intervals integer,
    child_name character varying(255)
);

CREATE TABLE bill_check_group_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    installments_number integer,
    first_duedate timestamp,
    interest numeric(10,2) CONSTRAINT interest_percent CHECK (interest >= 0 AND interest <= 100),
    interval_type integer,
    intervals integer,
    group_id bigint REFERENCES abstract_payment_group(id)
);

CREATE TABLE branch_synchronization (
    id serial NOT NULL PRIMARY KEY,
    sync_time timestamp  NOT NULL,
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    policy text NOT NULL
);

CREATE TABLE calls (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp,
    message text,
    person_id bigint REFERENCES person(id),
    attendant_id bigint REFERENCES person_adapt_to_user(id)
);

CREATE TABLE card_installment_settings (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    payment_day integer CHECK (payment_day <= 28),
    closing_day integer CHECK (closing_day <= 28)
);

CREATE TABLE card_installments_provider_details (
    id serial NOT NULL PRIMARY KEY,
    max_installments_number integer,
    installment_settings_id bigint REFERENCES card_installment_settings(id)
);

CREATE TABLE card_installments_store_details (
    id serial NOT NULL PRIMARY KEY,
    max_installments_number integer,
    installment_settings_id bigint REFERENCES card_installment_settings(id)
);

CREATE TABLE payment_destination (
    -- Subclasses:
    --    store_destination
    --    bank_destination
    id serial NOT NULL PRIMARY KEY,
    description text,
    account_id bigint REFERENCES bank_account(id),
    notes text,
    child_name character varying(255)
);

CREATE TABLE payment_method_details (
    -- Subclasses:
    --    debit_card_details
    --    credit_card_details
    --    card_installments_store_details
    --    card_installments_provider_details
    --    finance_details
    id serial NOT NULL PRIMARY KEY,
    is_active boolean,
    commission numeric(10,2),
    provider_id bigint REFERENCES person_adapt_to_credit_provider(id),
    destination_id bigint REFERENCES payment_destination(id),
    child_name character varying(255)
);

CREATE TABLE apayment_method (
    -- Subclasses:
    --    money_p_m
    --    gift_certificate_p_m
    --    card_p_m
    --    finance_p_m
    id serial NOT NULL PRIMARY KEY,
    is_active boolean,
    child_name character varying(255),
    daily_penalty numeric(10,2) CHECK (daily_penalty >= 0 AND daily_penalty <= 100),
    interest numeric(10,2) CONSTRAINT interest_percent CHECK (interest >= 0 AND interest <= 100),
    destination_id bigint REFERENCES payment_destination(id)
);

CREATE TABLE payment (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    open_date timestamp,
    due_date timestamp,
    paid_date timestamp,
    cancel_date timestamp,
    paid_value numeric(10,2),
    base_value numeric(10,2),
    value numeric(10,2),
    interest numeric(10,2) CONSTRAINT interest_percent CHECK (interest >= 0 AND interest <= 100),
    discount numeric(10,2),
    description text,
    payment_number text,
    method_id bigint REFERENCES apayment_method(id),
    method_details_id bigint REFERENCES payment_method_details(id),
    group_id bigint REFERENCES abstract_payment_group(id),
    till_id bigint REFERENCES till(id),
    destination_id bigint REFERENCES payment_destination(id)
);

CREATE TABLE check_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    payment_id bigint REFERENCES payment(id),
    bank_data_id bigint REFERENCES bank_account(id)
);

CREATE TABLE credit_card_details (
    id serial NOT NULL PRIMARY KEY,
    installment_settings_id bigint REFERENCES card_installment_settings(id)
);

CREATE TABLE credit_provider_group_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    installments_number integer,
    payment_type_id bigint REFERENCES payment_method_details(id),
    provider_id bigint REFERENCES person_adapt_to_credit_provider(id),
    group_id bigint REFERENCES abstract_payment_group(id)
);

CREATE TABLE debit_card_details (
    id serial NOT NULL PRIMARY KEY,
    receive_days integer
);

CREATE TABLE device_settings (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    "type" integer,
    brand text,
    model text,
    device integer,
    is_active boolean,
    station_id bigint REFERENCES branch_station(id)
);

CREATE TABLE device_constant (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    constant_type integer,
    constant_name text,
    constant_value numeric(10,2),
    constant_enum integer,
    device_value bytea,
    device_settings_id bigint REFERENCES device_settings(id)
);

CREATE TABLE employee_role_history (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    began timestamp,
    ended timestamp,
    salary numeric(10,2),
    role_id bigint REFERENCES employee_role(id),
    employee_id bigint REFERENCES person_adapt_to_employee(id),
    is_active boolean
);

CREATE TABLE finance_details (
    id serial NOT NULL PRIMARY KEY,
    receive_days integer
);

CREATE TABLE gift_certificate (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
);

CREATE TABLE gift_certificate_adapt_to_sellable (
    id serial NOT NULL PRIMARY KEY,
    group_id bigint REFERENCES abstract_payment_group(id),
    original_id bigint UNIQUE REFERENCES gift_certificate(id)
);

CREATE TABLE gift_certificate_item (
    id serial NOT NULL PRIMARY KEY
);

CREATE TABLE gift_certificate_type (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    base_sellable_info_id bigint REFERENCES base_sellable_info(id),
    on_sale_info_id bigint REFERENCES on_sale_info(id)
);

CREATE TABLE icms_ipi_book_entry (
    id serial NOT NULL PRIMARY KEY,
    icms_value numeric(10,2),
    ipi_value numeric(10,2)
);

CREATE TABLE inheritable_model (
    -- Subclasses:
    --   asellable_category
    --   asellable_item
    --   abstract_fiscal_book_entry
    --   abstract_stock_item
    --   apayment_method
    --   payment_destination
    --   payment_method_details
    id serial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_valid_model boolean
);

CREATE TABLE inheritable_model_adapter (
    -- Subclasses:
    --   asellable
    --   abstract_renegotiation_adapter
    --   abstract_payment_group
    id serial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_valid_model boolean
);

CREATE TABLE iss_book_entry (
    id serial NOT NULL PRIMARY KEY,
    iss_value numeric(10,2)
);

CREATE TABLE liaison (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    phone_number text,
    person_id bigint REFERENCES person(id)
);

CREATE TABLE parameter_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    field_name text NOT NULL UNIQUE,
    field_value text,
    is_editable boolean
);

CREATE TABLE payment_adapt_to_in_payment (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment(id)
);

CREATE TABLE payment_adapt_to_out_payment (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment(id)
);

CREATE TABLE payment_method (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
);

CREATE TABLE payment_operation (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    operation_date timestamp
);

CREATE TABLE bill_p_m (
    id serial NOT NULL PRIMARY KEY,
    max_installments_number integer,
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE card_p_m (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE check_p_m (
    id serial NOT NULL PRIMARY KEY,
    max_installments_number integer,
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE finance_p_m (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE gift_certificate_p_m (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE money_p_m (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE po_adapt_to_payment_deposit (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment_operation(id)
);

CREATE TABLE po_adapt_to_payment_devolution (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    reason text,
    original_id bigint UNIQUE REFERENCES payment_operation(id)
);

CREATE TABLE product_retention_history (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    reason text,
    product_id bigint REFERENCES product(id)
);

CREATE TABLE product_sellable_item (
    id serial NOT NULL PRIMARY KEY
);

CREATE TABLE product_stock_reference (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    logic_quantity numeric(10,2) CONSTRAINT positive_logic_quantity CHECK (logic_quantity >= 0),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    product_item_id bigint REFERENCES product_sellable_item(id)
);

CREATE TABLE profile_settings (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    app_dir_name text,
    has_permission boolean,
    user_profile_id bigint REFERENCES user_profile(id)
);

CREATE TABLE purchase_order_adapt_to_payment_group (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES purchase_order(id)
);

CREATE TABLE receiving_order (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    receival_date timestamp,
    confirm_date timestamp,
    notes text,
    freight_total numeric(10,2),
    surcharge_value numeric(10,2),
    discount_value numeric(10,2),
    icms_total numeric(10,2),
    ipi_total numeric(10,2),
    invoice_number integer CONSTRAINT valid_invoice_number CHECK (invoice_number >= 1 and invoice_number <= 999999),
    invoice_total numeric(10,2),
    cfop_id bigint REFERENCES cfop_data(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    supplier_id bigint REFERENCES person_adapt_to_supplier(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    purchase_id bigint REFERENCES purchase_order(id),
    transporter_id bigint REFERENCES person_adapt_to_transporter(id)
);

CREATE TABLE receiving_order_adapt_to_payment_group (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES receiving_order(id)
);

CREATE TABLE receiving_order_item (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    cost numeric(10,2),
    sellable_id bigint REFERENCES asellable(id),
    receiving_order_id bigint REFERENCES receiving_order(id),
    purchase_item_id bigint REFERENCES purchase_item(id)
);

CREATE TABLE renegotiation_data (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    reason text,
    paid_total numeric(10,2) CHECK (paid_total >= 0),
    invoice_number integer,
    penalty_value numeric(10,2),
    responsible_id bigint REFERENCES person(id),
    new_order_id bigint REFERENCES sale(id)
);

CREATE TABLE renegotiation_adapt_to_change_installments (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES renegotiation_data(id)
);

CREATE TABLE renegotiation_adapt_to_exchange (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES renegotiation_data(id)
);

CREATE TABLE renegotiation_adapt_to_return_sale (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES renegotiation_data(id)
);

CREATE TABLE service_sellable_item (
    id serial NOT NULL PRIMARY KEY,
    notes text,
    estimated_fix_date timestamp,
    completion_date timestamp
);

CREATE TABLE service_sellable_item_adapt_to_delivery (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    address text,
    original_id bigint UNIQUE REFERENCES service_sellable_item(id)
);

CREATE TABLE delivery_item (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    sellable_id bigint REFERENCES asellable(id),
    delivery_id bigint REFERENCES service_sellable_item_adapt_to_delivery(id)
);

CREATE TABLE store_destination (
    id serial NOT NULL PRIMARY KEY,
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE till_adapt_to_payment_group (
    id serial NOT NULL PRIMARY KEY,
    original_id bigint UNIQUE REFERENCES till(id)
);

CREATE TABLE till_entry (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp,
    description text,
    value numeric(10,2),
    is_initial_cash_amount boolean,
    till_id bigint REFERENCES till(id),
    payment_group_id bigint REFERENCES abstract_payment_group(id)
);

CREATE TABLE bank_destination (
    id serial NOT NULL PRIMARY KEY,
    branch_id bigint REFERENCES person_adapt_to_bank_branch(id)
);

CREATE TABLE abstract_fiscal_book_entry (
    -- Subclasses:
    --    icms_ipi_book_entry
    --    iss_book_entry
    id serial NOT NULL PRIMARY KEY,
    date timestamp,
    is_reversal boolean,
    invoice_number integer,
    cfop_id bigint REFERENCES cfop_data(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    drawee_id bigint REFERENCES person(id),
    payment_group_id bigint REFERENCES abstract_payment_group(id),
    child_name character varying(255)
);

--
-- Finally create the system_table which we use to verify that the schema
-- is properly created.
--
CREATE TABLE system_table (
    id serial NOT NULL PRIMARY KEY,
    update_date timestamp,
    version integer
);
