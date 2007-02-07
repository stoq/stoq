--
-- Copyright (C) 2006 Async Open Source
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
    id bigserial NOT NULL PRIMARY KEY,
    te_time timestamp without time zone NOT NULL,
    user_id integer,
    station_id integer,
    "type" integer
);

CREATE TABLE person (
    id bigserial NOT NULL PRIMARY KEY,
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
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    short_name text,
    compensation_code text
);

CREATE TABLE person_adapt_to_bank_branch (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    bank_id bigint REFERENCES bank(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_branch (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    identifier integer NOT NULL UNIQUE,
    manager_id bigint REFERENCES person(id),
    is_active boolean,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_client (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    days_late integer,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_company (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    cnpj text,
    fancy_name text,
    state_registry text,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_credit_provider (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    provider_type integer,
    short_name text,
    provider_id text,
    open_contract_date timestamp without time zone,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE city_location (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    country text,
    city text,
    state text
);

CREATE TABLE person_adapt_to_individual (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    cpf text,
    rg_number text,
    birth_date timestamp without time zone,
    occupation text,
    marital_status integer,
    father_name text,
    mother_name text,
    rg_expedition_date timestamp without time zone,
    rg_expedition_local text,
    gender integer,
    spouse_name text,
    birth_location_id bigint REFERENCES city_location(id),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE employee_role (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text NOT NULL UNIQUE
);

CREATE TABLE work_permit_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    series_number text,
    pis_number text,
    pis_bank text,
    pis_registry_date timestamp without time zone
);

CREATE TABLE military_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    series_number text,
    category text
);

CREATE TABLE voter_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    number text,
    section text,
    "zone" text
);

CREATE TABLE bank_account (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    bank_id integer,
    branch text,
    account text
);

CREATE TABLE person_adapt_to_employee (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    admission_date timestamp without time zone,
    expire_vacation timestamp without time zone,
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
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    comission numeric(10,2),
    comission_type integer,
    is_active boolean,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_supplier (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    product_desc text,
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE person_adapt_to_transporter (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    open_contract_date timestamp without time zone,
    freight_percentage numeric(10,2),
    original_id bigint UNIQUE REFERENCES person(id)
);

CREATE TABLE user_profile (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text
);

CREATE TABLE person_adapt_to_user (
    id bigserial NOT NULL PRIMARY KEY,
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
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    image bytea
);

CREATE TABLE product_adapt_to_sellable (
    id bigserial NOT NULL PRIMARY KEY,
    tax_type integer,
    tax_value numeric(10,2),
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES product(id)
);

-- FIXME: original_id should be marked as UNIQUE

CREATE TABLE product_adapt_to_storable (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint REFERENCES product(id)
);

CREATE TABLE product_supplier_info (
    id bigserial NOT NULL PRIMARY KEY,
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
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    image bytea
);

CREATE TABLE service_adapt_to_sellable (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES service(id)
);

CREATE TABLE base_sellable_info (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    price numeric(10,2),
    description text,
    max_discount numeric(10,2),
    commission numeric(10,2)
);

CREATE TABLE on_sale_info (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    on_sale_price numeric(10,2),
    on_sale_start_date timestamp without time zone,
    on_sale_end_date timestamp without time zone
);

CREATE TABLE asellable_category (
    -- Subclasses:
    --    base_sellable_category
    --    sellable_category
    id bigserial NOT NULL PRIMARY KEY,
    description text,
    suggested_markup numeric(10,2),
    salesperson_commission numeric(10,2),
    child_name character varying(255)
);

CREATE TABLE base_sellable_category (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255)
);

CREATE TABLE sellable_category (
    id bigserial NOT NULL PRIMARY KEY,
    base_category_id bigint REFERENCES base_sellable_category(id),
    child_name character varying(255)
);

CREATE TABLE sellable_unit (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    unit_index integer
);

CREATE TABLE asellable (
    -- Subclasses:
    --    product_adapt_to_sellable
    --    service_adapt_to_sellable
    --    gift_certificate_adapt_to_sellable
    id bigserial NOT NULL PRIMARY KEY,
    code integer NOT NULL UNIQUE,
    barcode text,
    status integer,
    cost numeric(10,2),
    notes text,
    unit_id bigint REFERENCES sellable_unit(id),
    base_sellable_info_id bigint REFERENCES base_sellable_info(id),
    on_sale_info_id bigint REFERENCES on_sale_info(id),
    category_id bigint REFERENCES sellable_category(id),
    child_name character varying(255)
);


CREATE TABLE purchase_order (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    order_number integer NOT NULL UNIQUE,
    open_date timestamp without time zone,
    quote_deadline timestamp without time zone,
    expected_receival_date timestamp without time zone,
    expected_pay_date timestamp without time zone,
    receival_date timestamp without time zone,
    confirm_date timestamp without time zone,
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
    id bigserial NOT NULL PRIMARY KEY,
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
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255)
);

CREATE TABLE branch_station (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text UNIQUE,
    is_active boolean,
    branch_id bigint REFERENCES person_adapt_to_branch(id)
);

CREATE TABLE till (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    initial_cash_amount numeric(10,2),
    final_cash_amount numeric(10,2),
    opening_date timestamp without time zone,
    closing_date timestamp without time zone,
    station_id bigint REFERENCES branch_station(id)
);

CREATE TABLE cfop_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    code text,
    description text
);

CREATE TABLE sale (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    order_number integer NOT NULL UNIQUE,
    coupon_id integer,
    service_invoice_number integer,
    open_date timestamp without time zone,
    close_date timestamp without time zone,
    confirm_date timestamp without time zone,
    cancel_date timestamp without time zone,
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
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES sale(id)
);

CREATE TABLE asellable_item (
    -- Subclasses:
    --    product_sellable_item
    --    service_sellable_item
    --    gift_certificate_item
    id bigserial NOT NULL PRIMARY KEY,
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
    id bigserial NOT NULL PRIMARY KEY,
    stock_cost numeric(10,2),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    logic_quantity numeric(10,2) CONSTRAINT positive_logic_quantity CHECK (logic_quantity >= 0),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    child_name character varying(255)
);

CREATE TABLE product_stock_item (
    id bigserial NOT NULL PRIMARY KEY,
    storable_id bigint REFERENCES product_adapt_to_storable(id),
    child_name character varying(255)
);

CREATE TABLE address (
    id bigserial NOT NULL PRIMARY KEY,
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
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    status integer,
    open_date timestamp without time zone,
    close_date timestamp without time zone,
    cancel_date timestamp without time zone,
    default_method integer,
    installments_number integer,
    interval_type integer,
    intervals integer,
    child_name character varying(255)
);

CREATE TABLE bill_check_group_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    installments_number integer,
    first_duedate timestamp without time zone,
    monthly_interest numeric(10,2),
    interval_type integer,
    intervals integer,
    group_id bigint REFERENCES abstract_payment_group(id)
);

CREATE TABLE branch_synchronization (
    id bigserial NOT NULL PRIMARY KEY,
    sync_time timestamp without time zone NOT NULL,
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    policy text NOT NULL
);

CREATE TABLE calls (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    date timestamp without time zone,
    message text,
    person_id bigint REFERENCES person(id),
    attendant_id bigint REFERENCES person_adapt_to_user(id)
);

CREATE TABLE card_installment_settings (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    payment_day integer CHECK (payment_day <= 28),
    closing_day integer CHECK (closing_day <= 28)
);

CREATE TABLE card_installments_provider_details (
    id bigserial NOT NULL PRIMARY KEY,
    installment_settings_id bigint REFERENCES card_installment_settings(id),
    child_name character varying(255)
);

CREATE TABLE card_installments_store_details (
    id bigserial NOT NULL PRIMARY KEY,
    max_installments_number integer,
    installment_settings_id bigint REFERENCES card_installment_settings(id),
    child_name character varying(255)
);

CREATE TABLE payment_destination (
    -- Subclasses:
    --    store_destination
    --    bank_destination
    id bigserial NOT NULL PRIMARY KEY,
    description text,
    account_id bigint REFERENCES bank_account(id),
    notes text,
    child_name character varying(255)
);

CREATE TABLE abstract_check_bill_adapter (
    -- Subclasses:
    --   pm_adapt_to_bill_p_m
    --   pm_adapt_to_check_p_m
    id bigserial NOT NULL PRIMARY KEY,
    destination_id bigint REFERENCES payment_destination(id),
    max_installments_number integer,
    monthly_interest numeric(10,2) CHECK (monthly_interest >= 0 AND monthly_interest <= 100),
    daily_penalty numeric(10,2) CHECK (daily_penalty >= 0 AND daily_penalty <= 100),
    child_name character varying(255)
);

CREATE TABLE payment_method_details (
    -- Subclasses:
    --    debit_card_details
    --    credit_card_details
    --    card_installments_store_details
    --    card_installments_provider_details
    --    finance_details
    id bigserial NOT NULL PRIMARY KEY,
    is_active boolean,
    commission numeric(10,2),
    provider_id bigint REFERENCES person_adapt_to_credit_provider(id),
    destination_id bigint REFERENCES payment_destination(id),
    child_name character varying(255)
);

CREATE TABLE abstract_payment_method_adapter (
    -- Subclasses:
    --    abstract_check_bill_adapter
    --    pm_adapt_to_money_p_m
    --    pm_adapt_to_gift_certificate_p_m
    --    pm_adapt_to_card_p_m
    --    pm_adapt_to_finance_p_m
    id bigserial NOT NULL PRIMARY KEY,
    is_active boolean,
    child_name character varying(255)
);

CREATE TABLE payment (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    identifier integer NOT NULL UNIQUE,
    status integer,
    open_date timestamp without time zone,
    due_date timestamp without time zone,
    paid_date timestamp without time zone,
    cancel_date timestamp without time zone,
    paid_value numeric(10,2),
    base_value numeric(10,2),
    value numeric(10,2),
    interest numeric(10,2),
    discount numeric(10,2),
    description text,
    payment_number text,
    method_id bigint REFERENCES abstract_payment_method_adapter(id),
    method_details_id bigint REFERENCES payment_method_details(id),
    group_id bigint REFERENCES abstract_payment_group(id),
    till_id bigint REFERENCES till(id),
    destination_id bigint REFERENCES payment_destination(id)
);

CREATE TABLE check_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    payment_id bigint REFERENCES payment(id),
    bank_data_id bigint REFERENCES bank_account(id)
);

CREATE TABLE credit_card_details (
    id bigserial NOT NULL PRIMARY KEY,
    installment_settings_id bigint REFERENCES card_installment_settings(id),
    child_name character varying(255)
);

CREATE TABLE credit_provider_group_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    installments_number integer,
    payment_type_id bigint REFERENCES payment_method_details(id),
    provider_id bigint REFERENCES person_adapt_to_credit_provider(id),
    group_id bigint REFERENCES abstract_payment_group(id)
);

CREATE TABLE debit_card_details (
    id bigserial NOT NULL PRIMARY KEY,
    receive_days integer,
    child_name character varying(255)
);

CREATE TABLE device_constants (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    constants bytea
);

CREATE TABLE device_settings (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    "type" integer,
    brand text,
    model text,
    device integer,
    station_id bigint REFERENCES branch_station(id),
    constants_id bigint REFERENCES device_constants(id),
    pm_constants_id bigint REFERENCES device_constants(id),
    is_active boolean
);

CREATE TABLE employee_role_history (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    began timestamp without time zone,
    ended timestamp without time zone,
    salary numeric(10,2),
    role_id bigint REFERENCES employee_role(id),
    employee_id bigint REFERENCES person_adapt_to_employee(id),
    is_active boolean
);

CREATE TABLE finance_details (
    id bigserial NOT NULL PRIMARY KEY,
    receive_days integer,
    child_name character varying(255)
);

CREATE TABLE gift_certificate (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
);

CREATE TABLE gift_certificate_adapt_to_sellable (
    id bigserial NOT NULL PRIMARY KEY,
    group_id bigint REFERENCES abstract_payment_group(id),
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES gift_certificate(id)
);

CREATE TABLE gift_certificate_item (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255)
);

CREATE TABLE gift_certificate_type (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_active boolean,
    base_sellable_info_id bigint REFERENCES base_sellable_info(id),
    on_sale_info_id bigint REFERENCES on_sale_info(id)
);

CREATE TABLE icms_ipi_book_entry (
    id bigserial NOT NULL PRIMARY KEY,
    icms_value numeric(10,2),
    ipi_value numeric(10,2),
    child_name character varying(255)
);

CREATE TABLE inheritable_model (
    -- Subclasses:
    --   asellable_category
    --   asellable_item
    --   abstract_fiscal_book_entry
    --   abstract_stock_item
    --   payment_destination
    --   payment_method_details
    id bigserial NOT NULL PRIMARY KEY,
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
    --   abstract_payment_method_adapter
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    is_valid_model boolean
);

CREATE TABLE iss_book_entry (
    id bigserial NOT NULL PRIMARY KEY,
    iss_value numeric(10,2),
    child_name character varying(255)
);

CREATE TABLE liaison (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text,
    phone_number text,
    person_id bigint REFERENCES person(id)
);

CREATE TABLE parameter_data (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    field_name text NOT NULL UNIQUE,
    field_value text,
    is_editable boolean
);

CREATE TABLE payment_adapt_to_in_payment (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment(id)
);

CREATE TABLE payment_adapt_to_out_payment (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment(id)
);

CREATE TABLE payment_method (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
);

CREATE TABLE payment_operation (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    operation_date timestamp without time zone
);

CREATE TABLE pm_adapt_to_bill_p_m (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE pm_adapt_to_card_p_m (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE pm_adapt_to_check_p_m (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE pm_adapt_to_finance_p_m (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE pm_adapt_to_gift_certificate_p_m (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE pm_adapt_to_money_p_m (
    id bigserial NOT NULL PRIMARY KEY,
    destination_id bigint REFERENCES payment_destination(id),
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES payment_method(id)
);

CREATE TABLE po_adapt_to_payment_deposit (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES payment_operation(id)
);

CREATE TABLE po_adapt_to_payment_devolution (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    reason text,
    original_id bigint UNIQUE REFERENCES payment_operation(id)
);

CREATE TABLE product_retention_history (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    reason text,
    product_id bigint REFERENCES product(id)
);

CREATE TABLE product_sellable_item (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255)
);

CREATE TABLE product_stock_reference (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    logic_quantity numeric(10,2) CONSTRAINT positive_logic_quantity CHECK (logic_quantity >= 0),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    product_item_id bigint REFERENCES product_sellable_item(id)
);

CREATE TABLE profile_settings (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    app_dir_name text,
    has_permission boolean,
    user_profile_id bigint REFERENCES user_profile(id)
);

CREATE TABLE purchase_order_adapt_to_payment_group (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES purchase_order(id)
);

CREATE TABLE receiving_order (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    receiving_number integer NOT NULL UNIQUE,
    status integer,
    receival_date timestamp without time zone,
    confirm_date timestamp without time zone,
    notes text,
    freight_total numeric(10,2),
    surcharge_value numeric(10,2),
    discount_value numeric(10,2),
    icms_total numeric(10,2),
    ipi_total numeric(10,2),
    invoice_number integer,
    invoice_total numeric(10,2),
    cfop_id bigint REFERENCES cfop_data(id),
    responsible_id bigint REFERENCES person_adapt_to_user(id),
    supplier_id bigint REFERENCES person_adapt_to_supplier(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    purchase_id bigint REFERENCES purchase_order(id),
    transporter_id bigint REFERENCES person_adapt_to_transporter(id)
);

CREATE TABLE receiving_order_adapt_to_payment_group (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES receiving_order(id)
);

CREATE TABLE receiving_order_item (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity_received numeric(10,2) CONSTRAINT positive_quantity_received CHECK (quantity_received >= 0),
    cost numeric(10,2),
    sellable_id bigint REFERENCES asellable(id),
    receiving_order_id bigint REFERENCES receiving_order(id)
);

CREATE TABLE renegotiation_data (
    id bigserial NOT NULL PRIMARY KEY,
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
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES renegotiation_data(id)
);

CREATE TABLE renegotiation_adapt_to_exchange (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES renegotiation_data(id)
);

CREATE TABLE renegotiation_adapt_to_return_sale (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES renegotiation_data(id)
);

CREATE TABLE service_sellable_item (
    id bigserial NOT NULL PRIMARY KEY,
    notes text,
    estimated_fix_date timestamp without time zone,
    completion_date timestamp without time zone,
    child_name character varying(255)
);

CREATE TABLE service_sellable_item_adapt_to_delivery (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    address text,
    original_id bigint UNIQUE REFERENCES service_sellable_item(id)
);

CREATE TABLE delivery_item (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    quantity numeric(10,2) CONSTRAINT positive_quantity CHECK (quantity >= 0),
    sellable_id bigint REFERENCES asellable(id),
    delivery_id bigint REFERENCES service_sellable_item_adapt_to_delivery(id)
);

CREATE TABLE store_destination (
    id bigserial NOT NULL PRIMARY KEY,
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    child_name character varying(255)
);

CREATE TABLE till_adapt_to_payment_group (
    id bigserial NOT NULL PRIMARY KEY,
    child_name character varying(255),
    original_id bigint UNIQUE REFERENCES till(id)
);

CREATE TABLE till_entry (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    identifier integer NOT NULL UNIQUE,
    date timestamp without time zone,
    description text,
    value numeric(10,2),
    is_initial_cash_amount boolean,
    till_id bigint REFERENCES till(id),
    payment_group_id bigint REFERENCES abstract_payment_group(id)
);

CREATE TABLE bank_destination (
    id bigserial NOT NULL PRIMARY KEY,
    branch_id bigint REFERENCES person_adapt_to_bank_branch(id),
    child_name character varying(255)
);

CREATE TABLE abstract_fiscal_book_entry (
    -- Subclasses:
    --    icms_ipi_book_entry
    --    iss_book_entry
    id bigserial NOT NULL PRIMARY KEY,
    identifier integer NOT NULL UNIQUE,
    date timestamp without time zone,
    is_reversal boolean,
    invoice_number integer,
    cfop_id bigint REFERENCES cfop_data(id),
    branch_id bigint REFERENCES person_adapt_to_branch(id),
    drawee_id bigint REFERENCES person(id),
    payment_group_id bigint REFERENCES abstract_payment_group(id),
    child_name character varying(255)
);

--
-- Views
--


--
-- Stores information about sellables. Note: This view must be used
-- always when searching for stock information on a certain branch
-- company. For general sellable information in all the branches go to
-- sellable_full_stock_view.
--
-- Usage: select * from sellable_view where branch_id=1;
--
-- Available fields are:
--     id                 - the id of the asellable table
--     code               - the sellable code
--     barcode            - the sellable barcode
--     status             - the sellable status
--     cost               - the sellable cost
--     price              - the sellable price
--     is_valid_model     - the sellable is_valid_model system attribute
--     description        - the sellable description
--     unit               - the unit in case the sellable is not a gift
--                          certificate
--     product_id         - the id of the product table
--     supplier_name      - the supplier name in case the sellable is a
--                          product
--     branch_id          - the id of person_adapt_to_branch table
--     stock              - the stock in case the sellable is a product
--
--
--
-- Callsites:
--
--   stoqlib/gui/search/sellablesearch.py
--   stoqlib/gui/search/productsearch.py
--   stoqlib/reporting/product.py
--
CREATE VIEW sellable_view AS

   SELECT DISTINCT
      asellable.id AS id,
      asellable.code AS code,
      asellable.barcode AS barcode,
      asellable.status AS status,
      asellable.cost AS cost,
      base_sellable_info.price AS price,
      base_sellable_info.is_valid_model AS is_valid_model,
      base_sellable_info.description AS description,
      sellable_unit.description AS unit,
      product.id as product_id,
      supplier_person.name AS supplier_name,
      abstract_stock_item.branch_id AS branch_id,
      sum(abstract_stock_item.quantity+abstract_stock_item.logic_quantity) AS stock

   FROM base_sellable_info, asellable

      -- Sellable unit

      LEFT JOIN sellable_unit
      ON (sellable_unit.id = asellable.unit_id)

      -- Product

      LEFT JOIN product_adapt_to_sellable
      ON (product_adapt_to_sellable.id = asellable.id)

      LEFT JOIN product
      ON (product.id = product_adapt_to_sellable.original_id)

      -- Product Stock Item

      LEFT JOIN product_adapt_to_storable
      ON (product_adapt_to_storable.original_id = product.id)
      
      LEFT JOIN product_stock_item
      ON (product_stock_item.storable_id = product_adapt_to_storable.id)

      LEFT JOIN abstract_stock_item
      ON (abstract_stock_item.id = product_stock_item.id)

      -- Product Supplier

      LEFT JOIN product_supplier_info
      ON (product_supplier_info.product_id = product.id AND
          product_supplier_info.is_main_supplier = 't')

      LEFT JOIN person_adapt_to_supplier
      ON (person_adapt_to_supplier.id = product_supplier_info.supplier_id)

      LEFT JOIN person AS supplier_person
      ON (supplier_person.id = person_adapt_to_supplier.original_id)

   WHERE
        asellable.base_sellable_info_id = base_sellable_info.id AND
        base_sellable_info.is_valid_model = 't'

   GROUP BY
        asellable.code, asellable.status,  asellable.barcode, asellable.id, 
        asellable.cost, base_sellable_info.price, base_sellable_info.description, 
        base_sellable_info.is_valid_model, sellable_unit.description, 
        product.id,  supplier_person.name, abstract_stock_item.branch_id;



--
-- Stores information about sellables and stock information in all
-- branch companies.
--
-- Available fields are: the same fields of sellable_view table.
--
-- Callsites:
--
--   stoqlib/gui/search/sellablesearch.py
--
CREATE VIEW sellable_full_stock_view AS

  SELECT DISTINCT
    sum(stock) AS stock,
    id,
    code,
    barcode,
    status,
    0 AS branch_id, cost,
    price,
    is_valid_model,
    description,
    unit,
    supplier_name,
    product_id

  FROM sellable_view

  GROUP BY code, barcode, status, id, cost, price, is_valid_model,
           description, unit, supplier_name, product_id;


--
-- Stores information about products and stock information in all
-- branch companies.
--
-- Available fields are: the same fields of sellable_full_stock_view
--
-- Callsites:
--
--   stoqlib/gui/search/productsearch.py
--
CREATE VIEW product_full_stock_view AS

  SELECT * 

  FROM sellable_full_stock_view 

  WHERE product_id IS NOT NULL;


--
-- Stores information about services
--
-- Available fields are:
--     id                 - the id of the asellable table
--     code               - the sellable code
--     barcode            - the sellable barcode
--     status             - the sellable status
--     cost               - the sellable cost
--     price              - the sellable price
--     description        - the sellable description
--     unit               - the unit in case the sellable is not a gift
--                          certificate
--     service_id         - the id of the service table
--
-- Callsites:
--
--   stoqlib/gui/search/servicesearch.py
--
CREATE VIEW service_view AS

  SELECT DISTINCT
    asellable.id AS id,
    asellable.code AS code,
    asellable.barcode AS barcode,
    asellable.status AS status,
    asellable.cost AS cost,
    base_sellable_info.price AS price,
    base_sellable_info.description AS description,
    sellable_unit.description AS unit,
    service.id AS service_id

  FROM base_sellable_info, service_adapt_to_sellable, service, asellable

    LEFT JOIN sellable_unit
    ON (asellable.unit_id = sellable_unit.id)

  WHERE service.is_valid_model = 't' AND
        asellable.base_sellable_info_id = base_sellable_info.id AND
        asellable.id = service_adapt_to_sellable.id AND
        service.id = service_adapt_to_sellable.original_id;


--
-- Stores information about gift certificates
--
-- Available fields are:
--     id                 - the id of the asellable table
--     code               - the sellable code
--     barcode            - the sellable barcode
--     status             - the sellable status
--     cost               - the sellable cost
--     price              - the sellable price
--     on_sale_price      - the sellable price when the item is on sale
--     description        - the sellable description
--     giftcertificate_id - the id of giftcertificate table
--
-- Callsites:
--
--   stoqlib/gui/search/giftcertificatesearch.py
--
CREATE VIEW gift_certificate_view AS

  SELECT DISTINCT
    asellable.id AS id,
    asellable.code AS code,
    asellable.barcode AS barcode,
    asellable.status AS status,
    asellable.cost AS cost,
    base_sellable_info.price AS price,
    on_sale_info.on_sale_price AS on_sale_price,
    base_sellable_info.description AS description,
    gift_certificate.id AS giftcertificate_id

  FROM asellable, base_sellable_info, on_sale_info, 
       gift_certificate_adapt_to_sellable, gift_certificate

  WHERE gift_certificate.is_valid_model = 't' AND
        asellable.base_sellable_info_id = base_sellable_info.id AND
        asellable.on_sale_info_id = on_sale_info.id AND
        asellable.id = gift_certificate_adapt_to_sellable.id AND
        gift_certificate_adapt_to_sellable.original_id = gift_certificate.id;

--
-- Stores information about sales
--
-- Available fields are:
--     id                 - the id of the sale table
--     coupon_id          - the id generated by the fiscal printer
--     order_number       - the sale order_number
--     open_date          - the date when the sale was started
--     confirm_date       - the date when the sale was confirmed
--     close_date         - the date when the sale was closed
--     cancel_date        - the date when the sale was cancelled
--     notes              - sale order general notes
--     status             - the sale status
--     salesperson_name   - the salesperson name
--     client_name        - the sale client name
--     client_id          - the if of the client table
--     subtotal           - the sum of all items in the sale
--     surcharge_value    - the sale surcharge value
--     discount_value     - the sale discount value
--     total              - the subtotal - discount + charge
--     total_quantity     - the items total quantity for the sale
--
--  Callsites:
--   
--   stoqlib/domain/person.py
--   stoqlib/gui/search/salesearch.py
--   stoqlib/gui/slaves/saleslave.py
--   stoqlib/gui/dialogs/saledetails.p
--   stoqlib/gui/wizards/salereturnwizard.py
--   stoqlib/reporting/sale.py
--   stoq/gui/receivable/receivable.py
--   stoq/gui/sales/sales.py
--   stoq/gui/till/till.py
--
CREATE VIEW sale_view AS

  SELECT DISTINCT
    sale_id AS id,
    sale.coupon_id AS coupon_id,
    sale.order_number AS order_number,
    sale.open_date AS open_date,
    sale.close_date AS close_date,
    sale.status AS status,
    sale.surcharge_value AS surcharge_value,
    sale.discount_value AS discount_value,
    sale.confirm_date AS confirm_date,
    sale.cancel_date AS cancel_date,
    sale.notes AS notes,
    sale.client_id AS client_id,
    client_person.name AS client_name,
    person.name AS salesperson_name,
    sum(quantity * price) - sale.discount_value + sale.surcharge_value AS total,
    sum(quantity * price) AS subtotal,
    sum(quantity) AS total_quantity

  FROM asellable_item, person_adapt_to_sales_person, person, sale
    
    LEFT JOIN person_adapt_to_client
    ON (sale.client_id = person_adapt_to_client.id)

    LEFT JOIN person AS client_person
    ON (person_adapt_to_client.original_id = client_person.id)

  WHERE sale.is_valid_model = 't' AND
        asellable_item.sale_id = sale_id AND
        sale.salesperson_id = person_adapt_to_sales_person.id AND
        person_adapt_to_sales_person.original_id = person.id
 
  GROUP BY asellable_item.sale_id, sale.id,
           sale.surcharge_value, sale.discount_value, 
           sale.coupon_id, sale.order_number,
           sale.open_date, sale.close_date,
           sale.status, sale.confirm_date,
           sale.cancel_date, sale.notes,
           sale.client_id,
           client_person.name,
           person.name

  HAVING sale_id = sale.id;

--
-- Stores information about clients.
-- Available fields are:
--    id                  - the id of the person table
--    name                - the client name
--    status              - the client financial status
--    cpf                 - the brazil-specific cpf attribute
--    rg_number           - the brazil-specific rg_number attribute
--    phone_number        - the client phone_number
--
-- Callsites:
--
--   stoqlib/gui/search/personsearch.py
--
CREATE VIEW client_view AS

  SELECT DISTINCT
    person.id AS id,
    person.name AS name,
    person_adapt_to_client.status AS status,
    person_adapt_to_individual.cpf AS cpf,
    person_adapt_to_individual.rg_number As rg_number,
    person.phone_number AS phone_number,
    person_adapt_to_client.id AS client_id

  FROM person_adapt_to_client, person

    LEFT JOIN person_adapt_to_individual
    ON (person.id = person_adapt_to_individual.original_id)

  WHERE person_adapt_to_client.is_valid_model = 't' AND
        person.id = person_adapt_to_client.original_id;


--
-- Stores information about purchase orders.
-- Available fields are:
--    id                      - the if of purchase_order table
--    status                  - the purchase order status
--    order_number            - the purchase order_number
--    open_date               - the date when the order was started
--    quote_deadline          - the date when the quotation expires
--    expected_receival_date  - expected date to receive products
--    expected_pay_date       - expected date to pay the products
--    receival_date           - the date when the products were received
--    confirm_date            - the date when the order was confirmed
--    salesperson_name        - the name of supplier's salesperson
--    freight                 - the freight value
--    surcharge_value         - the surcharge value for the order total
--    discount_value          - the discount_value for the order total
--    supplier_name           - the supplier name
--    transporter_name        - the transporter name
--    branch_name             - the branch company name
--    ordered_quantity        - the total quantity ordered
--    received_quantity       - the total quantity received
--    subtotal                - the order subtotal (sum of product values)
--    total                   - subtotal - discount_value + surcharge_value
--
-- Callsites:
--
--   stoqlib/gui/wizards/receivingwizard.py
--   stoqlib/reporting/purchase.py
--   stoq/gui/purchase/purchase.py
--
CREATE VIEW purchase_order_view AS

  SELECT DISTINCT
    purchase_order.id AS id,
    purchase_order.status AS status,
    purchase_order.order_number AS order_number,
    purchase_order.open_date AS open_date,
    purchase_order.quote_deadline AS quote_deadline,
    purchase_order.expected_receival_date AS expected_receival_date,
    purchase_order.expected_pay_date AS expected_pay_date,
    purchase_order.receival_date AS receival_date,
    purchase_order.confirm_date AS confirm_date,
    purchase_order.salesperson_name AS salesperson_name,
    purchase_order.freight AS freight,
    purchase_order.surcharge_value AS surcharge_value,
    purchase_order.discount_value AS discount_value,
    supplier_person.name AS supplier_name,
    transporter_person.name AS transporter_name,
    branch_person.name AS branch_name,
    sum(quantity) AS ordered_quantity,
    sum(quantity_received) AS received_quantity,
    sum(cost*quantity) AS subtotal,
    sum(cost*quantity) - purchase_order.discount_value + purchase_order.surcharge_value AS total

  FROM person_adapt_to_supplier,
       person AS supplier_person,
       person_adapt_to_branch,
       purchase_item,
       person AS branch_person,
       purchase_order
       
    LEFT JOIN person_adapt_to_transporter
    ON (purchase_order.transporter_id = person_adapt_to_transporter.id)

    LEFT JOIN person AS transporter_person
    ON (person_adapt_to_transporter.original_id = transporter_person.id)

  WHERE purchase_order.is_valid_model = 't' AND
        person_adapt_to_supplier.original_id = supplier_person.id AND
        person_adapt_to_branch.original_id = branch_person.id AND
        purchase_order.supplier_id = person_adapt_to_supplier.id AND
        purchase_order.branch_id = person_adapt_to_branch.id AND
        purchase_item.order_id = purchase_order.id

  GROUP BY purchase_item.order_id,
           purchase_order.id,
           purchase_order.status,
           purchase_order.order_number,
           purchase_order.open_date,
           purchase_order.quote_deadline,
           purchase_order.expected_receival_date,
           purchase_order.expected_pay_date,
           purchase_order.receival_date,
           purchase_order.confirm_date,
           purchase_order.salesperson_name,
           purchase_order.freight,
           purchase_order.surcharge_value,
           purchase_order.discount_value,
           supplier_person.name,
           transporter_person.name,
           branch_person.name

  HAVING order_id = purchase_order.id;

--
-- Stores information about clients.
-- Available fields are:
--    id                  - the id of the icms_ipi_book_entry table
--    identifier          - the identifier of icms_ipi_book_entry table
--    icms_value          - the total value of icms
--    ipi_value           - the total value of ipi
--    date                - the date when the entry was created
--    invoice_number      - the invoice number
--    cfop_data_id        - the if of the cfop_data table
--    cfop_code           - the code of the cfop
--    drawee_name         - the drawee name
--    drawee_id           - the if of Person table
--    branch_id           - the id of the person_adapt_to_branch table
--    payment_group_id    - the id of the abstract_payment_group table
--
-- Callsites:
--
--   stoqlib/gui/search/fiscalsearch.py
--
CREATE VIEW icms_ipi_view AS

  SELECT DISTINCT
    icms_ipi_book_entry.id AS id,
    icms_ipi_book_entry.icms_value AS icms_value,
    icms_ipi_book_entry.ipi_value AS ipi_value,
    abstract_fiscal_book_entry.identifier AS identifier,
    abstract_fiscal_book_entry.date AS date,
    abstract_fiscal_book_entry.invoice_number AS invoice_number,
    abstract_fiscal_book_entry.cfop_id AS cfop_data_id,
    abstract_fiscal_book_entry.branch_id AS branch_id,
    abstract_fiscal_book_entry.drawee_id AS drawee_id,
    abstract_fiscal_book_entry.payment_group_id AS payment_group_id,
    cfop_data.code AS cfop_code,
    person.name AS drawee_name

  FROM cfop_data, icms_ipi_book_entry, abstract_fiscal_book_entry

   LEFT JOIN person
   ON (abstract_fiscal_book_entry.drawee_id = person.id)

  WHERE icms_ipi_book_entry.id = abstract_fiscal_book_entry.id AND 
        cfop_data.id = abstract_fiscal_book_entry.cfop_id;


--
-- Stores information about clients.
-- Available fields are:
--    id                  - the id of the iss_book_entry table
--    identifier          - the identifier of iss_book_entry table
--    iss_value           - the total value of iss
--    date                - the date when the entry was created
--    invoice_number      - the invoice number
--    cfop_data_id        - the if of the cfop_data table
--    cfop_code           - the code of the cfop
--    drawee_name         - the drawee name
--    branch_id           - the id of the person_adapt_to_branch table
--    payment_group_id    - the if of the abstract_payment_group table
--
-- Callsites:
--
--   stoqlib/gui/search/fiscalsearch.py
--
CREATE VIEW iss_view AS

  SELECT DISTINCT
    iss_book_entry.id AS id,
    iss_book_entry.iss_value AS iss_value,
    abstract_fiscal_book_entry.identifier AS identifier,
    abstract_fiscal_book_entry.date AS date,
    abstract_fiscal_book_entry.invoice_number AS invoice_number,
    abstract_fiscal_book_entry.cfop_id AS cfop_data_id,
    abstract_fiscal_book_entry.branch_id AS branch_id,
    abstract_fiscal_book_entry.drawee_id AS drawee_id,
    abstract_fiscal_book_entry.payment_group_id AS payment_group_id,
    cfop_data.code AS cfop_code,
    person.name AS drawee_name

  FROM iss_book_entry, cfop_data, abstract_fiscal_book_entry

    LEFT JOIN person
    ON (abstract_fiscal_book_entry.drawee_id = person.id)

  WHERE iss_book_entry.id = abstract_fiscal_book_entry.id AND
        cfop_data.id = abstract_fiscal_book_entry.cfop_id;


--
-- Stores information about till entries and payments
-- Available fields are:
--    id                      - the identifier of till entries and payments
--    Note: this field is used only to deal with SQLObject compatibility
--    identifier              - the identifier of till entries and payments
--    Note: this is a field used to query on with search dialogs
--    date                    - the date when the entry was created
--    description             - the entry description
--    value                   - the entry value
--    is_initial_cash_amount  - is this entry the initial cash amount?
--    till_id                 - the id of the till table
--    status                  - the status of the till table
--    closing_date            - the closing_date of the till table
--    station_name            - the value of name branch_station name column
--    branch_id               - the id of the person_adapt_to_branch table
--
-- Callsites:
--
--   stoqlib/domain/till.py
--   stoqlib/gui/dialogs/tillhistory.py
--

CREATE VIEW till_entry_and_payment_view AS

  SELECT DISTINCT
    till_entry.identifier AS id,
    till_entry.identifier AS identifier,
    till_entry.date AS date,
    till_entry.description AS description,
    till_entry.value AS value,
    till_entry.is_initial_cash_amount AS is_initial_cash_amount,
    till_entry.till_id AS till_id,
    till.status AS status,
    till.closing_date AS closing_date,
    branch_station.name AS station_name,
    person_adapt_to_branch.id AS branch_id

  FROM till_entry, till, branch_station, person_adapt_to_branch
  
  WHERE till_entry.till_id = till.id AND
    	till.station_id = branch_station.id AND
    	branch_station.branch_id = person_adapt_to_branch.id

  UNION ALL

    SELECT DISTINCT
      payment.identifier AS id,
      payment.identifier AS identifier,
      payment.open_date AS date,
      payment.description AS description,
      payment.value AS value,
      FALSE AS is_initial_cash_amount,
      payment.till_id AS till_id,
      till.status AS status,
      till.closing_date AS date,
      branch_station.name AS station_name,
      person_adapt_to_branch.id AS branch_id

    FROM payment, till, branch_station, person_adapt_to_branch

    WHERE payment.till_id = till.id AND
          till.station_id = branch_station.id AND
          branch_station.branch_id = person_adapt_to_branch.id;

--
-- Stores information about payments
-- Available fields are:
--    identifier              - the identifier of till entries and payments
--    date                    - the date when the entry was created
--    description             - the entry description
--    value                   - the entry value
--    station_name            - the value of name branch_station name column
--
CREATE VIEW till_fiscal_operations_view AS

  SELECT DISTINCT
    payment.id AS id,
    payment.identifier AS identifier,
    payment.open_date AS date,
    payment.description AS description,
    payment.value AS value,
    branch_station.name AS station_name,
    person_adapt_to_branch.id AS branch_id,
    till.status AS status

  FROM payment, till, branch_station, person_adapt_to_branch

  WHERE payment.till_id = till.id AND
        till.station_id = branch_station.id AND
        branch_station.branch_id = person_adapt_to_branch.id;

--
-- Finally create the system_table which we use to verify that the schema
-- is properly created.
--
CREATE TABLE system_table (
    id bigserial NOT NULL PRIMARY KEY,
    update_date timestamp without time zone,
    version integer
);
