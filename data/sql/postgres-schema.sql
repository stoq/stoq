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

--
-- Sequences
--

CREATE SEQUENCE stoqlib_abstract_bookentry_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

CREATE SEQUENCE stoqlib_branch_identifier_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

CREATE SEQUENCE stoqlib_payment_identifier_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

CREATE SEQUENCE stoqlib_purchase_ordernumber_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

CREATE SEQUENCE stoqlib_purchasereceiving_number_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

CREATE SEQUENCE stoqlib_sale_ordernumber_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

CREATE SEQUENCE stoqlib_sellable_code_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

ALTER TABLE transaction_entry ALTER COLUMN id TYPE bigint;
ALTER TABLE person ALTER COLUMN id TYPE bigint;
ALTER TABLE bank ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_bank_branch ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_branch ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_client ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_company ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_credit_provider ALTER COLUMN id TYPE bigint;
ALTER TABLE city_location ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_individual ALTER COLUMN id TYPE bigint;
ALTER TABLE employee_role ALTER COLUMN id TYPE bigint;
ALTER TABLE work_permit_data ALTER COLUMN id TYPE bigint;
ALTER TABLE military_data ALTER COLUMN id TYPE bigint;
ALTER TABLE voter_data ALTER COLUMN id TYPE bigint;
ALTER TABLE bank_account ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_employee ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_sales_person ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_supplier ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_transporter ALTER COLUMN id TYPE bigint;
ALTER TABLE user_profile ALTER COLUMN id TYPE bigint;
ALTER TABLE person_adapt_to_user ALTER COLUMN id TYPE bigint;
ALTER TABLE product ALTER COLUMN id TYPE bigint;
ALTER TABLE product_adapt_to_sellable ALTER COLUMN id TYPE bigint;
ALTER TABLE product_adapt_to_storable ALTER COLUMN id TYPE bigint;
ALTER TABLE product_supplier_info ALTER COLUMN id TYPE bigint;
ALTER TABLE service ALTER COLUMN id TYPE bigint;
ALTER TABLE service_adapt_to_sellable ALTER COLUMN id TYPE bigint;
ALTER TABLE base_sellable_info ALTER COLUMN id TYPE bigint;
ALTER TABLE on_sale_info ALTER COLUMN id TYPE bigint;
ALTER TABLE asellable_category ALTER COLUMN id TYPE bigint;
ALTER TABLE base_sellable_category ALTER COLUMN id TYPE bigint;
ALTER TABLE sellable_category ALTER COLUMN id TYPE bigint;
ALTER TABLE sellable_unit ALTER COLUMN id TYPE bigint;
ALTER TABLE asellable ALTER COLUMN id TYPE bigint;
ALTER TABLE purchase_order ALTER COLUMN id TYPE bigint;
ALTER TABLE purchase_item ALTER COLUMN id TYPE bigint;
ALTER TABLE abstract_renegotiation_adapter ALTER COLUMN id TYPE bigint;
ALTER TABLE branch_station ALTER COLUMN id TYPE bigint;
ALTER TABLE till ALTER COLUMN id TYPE bigint;
ALTER TABLE cfop_data ALTER COLUMN id TYPE bigint;
ALTER TABLE sale ALTER COLUMN id TYPE bigint;
ALTER TABLE sale_adapt_to_payment_group ALTER COLUMN id TYPE bigint;
ALTER TABLE asellable_item ALTER COLUMN id TYPE bigint;
ALTER TABLE abstract_stock_item ALTER COLUMN id TYPE bigint;
ALTER TABLE product_stock_item ALTER COLUMN id TYPE bigint;
ALTER TABLE address ALTER COLUMN id TYPE bigint;
ALTER TABLE abstract_payment_group ALTER COLUMN id TYPE bigint;
ALTER TABLE bill_check_group_data ALTER COLUMN id TYPE bigint;
ALTER TABLE branch_synchronization ALTER COLUMN id TYPE bigint;
ALTER TABLE calls ALTER COLUMN id TYPE bigint;
ALTER TABLE card_installment_settings ALTER COLUMN id TYPE bigint;
ALTER TABLE card_installments_provider_details ALTER COLUMN id TYPE bigint;
ALTER TABLE card_installments_store_details ALTER COLUMN id TYPE bigint;
ALTER TABLE payment_destination ALTER COLUMN id TYPE bigint;
ALTER TABLE abstract_check_bill_adapter ALTER COLUMN id TYPE bigint;
ALTER TABLE payment_method_details ALTER COLUMN id TYPE bigint;
ALTER TABLE abstract_payment_method_adapter ALTER COLUMN id TYPE bigint;
ALTER TABLE payment ALTER COLUMN id TYPE bigint;
ALTER TABLE check_data ALTER COLUMN id TYPE bigint;
ALTER TABLE credit_card_details ALTER COLUMN id TYPE bigint;
ALTER TABLE credit_provider_group_data ALTER COLUMN id TYPE bigint;
ALTER TABLE debit_card_details ALTER COLUMN id TYPE bigint;
ALTER TABLE device_constants ALTER COLUMN id TYPE bigint;
ALTER TABLE device_settings ALTER COLUMN id TYPE bigint;
ALTER TABLE employee_role_history ALTER COLUMN id TYPE bigint;
ALTER TABLE finance_details ALTER COLUMN id TYPE bigint;
ALTER TABLE gift_certificate ALTER COLUMN id TYPE bigint;
ALTER TABLE gift_certificate_adapt_to_sellable ALTER COLUMN id TYPE bigint;
ALTER TABLE gift_certificate_item ALTER COLUMN id TYPE bigint;
ALTER TABLE gift_certificate_type ALTER COLUMN id TYPE bigint;
ALTER TABLE icms_ipi_book_entry ALTER COLUMN id TYPE bigint;
ALTER TABLE inheritable_model ALTER COLUMN id TYPE bigint;
ALTER TABLE inheritable_model_adapter ALTER COLUMN id TYPE bigint;
ALTER TABLE iss_book_entry ALTER COLUMN id TYPE bigint;
ALTER TABLE liaison ALTER COLUMN id TYPE bigint;
ALTER TABLE parameter_data ALTER COLUMN id TYPE bigint;
ALTER TABLE payment_adapt_to_in_payment ALTER COLUMN id TYPE bigint;
ALTER TABLE payment_adapt_to_out_payment ALTER COLUMN id TYPE bigint;
ALTER TABLE payment_method ALTER COLUMN id TYPE bigint;
ALTER TABLE payment_operation ALTER COLUMN id TYPE bigint;
ALTER TABLE pm_adapt_to_bill_p_m ALTER COLUMN id TYPE bigint;
ALTER TABLE pm_adapt_to_card_p_m ALTER COLUMN id TYPE bigint;
ALTER TABLE pm_adapt_to_check_p_m ALTER COLUMN id TYPE bigint;
ALTER TABLE pm_adapt_to_finance_p_m ALTER COLUMN id TYPE bigint;
ALTER TABLE pm_adapt_to_gift_certificate_p_m ALTER COLUMN id TYPE bigint;
ALTER TABLE pm_adapt_to_money_p_m ALTER COLUMN id TYPE bigint;
ALTER TABLE po_adapt_to_payment_deposit ALTER COLUMN id TYPE bigint;
ALTER TABLE po_adapt_to_payment_devolution ALTER COLUMN id TYPE bigint;
ALTER TABLE product_retention_history ALTER COLUMN id TYPE bigint;
ALTER TABLE product_sellable_item ALTER COLUMN id TYPE bigint;
ALTER TABLE product_stock_reference ALTER COLUMN id TYPE bigint;
ALTER TABLE profile_settings ALTER COLUMN id TYPE bigint;
ALTER TABLE purchase_order_adapt_to_payment_group ALTER COLUMN id TYPE bigint;
ALTER TABLE receiving_order ALTER COLUMN id TYPE bigint;
ALTER TABLE receiving_order_adapt_to_payment_group ALTER COLUMN id TYPE bigint;
ALTER TABLE receiving_order_item ALTER COLUMN id TYPE bigint;
ALTER TABLE renegotiation_data ALTER COLUMN id TYPE bigint;
ALTER TABLE renegotiation_adapt_to_change_installments ALTER COLUMN id TYPE bigint;
ALTER TABLE renegotiation_adapt_to_exchange ALTER COLUMN id TYPE bigint;
ALTER TABLE renegotiation_adapt_to_return_sale ALTER COLUMN id TYPE bigint;
ALTER TABLE service_sellable_item ALTER COLUMN id TYPE bigint;
ALTER TABLE service_sellable_item_adapt_to_delivery ALTER COLUMN id TYPE bigint;
ALTER TABLE delivery_item ALTER COLUMN id TYPE bigint;
ALTER TABLE store_destination ALTER COLUMN id TYPE bigint;
ALTER TABLE till_adapt_to_payment_group ALTER COLUMN id TYPE bigint;
ALTER TABLE till_entry ALTER COLUMN id TYPE bigint;
ALTER TABLE bank_destination ALTER COLUMN id TYPE bigint;
ALTER TABLE abstract_fiscal_book_entry ALTER COLUMN id TYPE bigint;
ALTER TABLE system_table ALTER COLUMN id TYPE bigint;
