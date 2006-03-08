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
--

-- Changes on Bug fix #2320
ALTER TABLE bank_account ADD COLUMN bank_id integer;
ALTER TABLE bank_account DROP COLUMN name;


--Converts a double_precision column to a numeric one.
--arguments are:
--          1 - the table name
--          2 - the column_name we would like to convert
CREATE OR REPLACE FUNCTION doubletonum(text, text)
RETURNS integer AS '
DECLARE
    new_column text;
BEGIN
        new_column = textcat($2, cast(''2'' as text));

        execute ''alter table '' || quote_ident($1) ||
            '' add column '' || quote_ident(new_column) ||
            '' numeric(10,2)'';

        execute ''update '' || quote_ident($1) || '' set '' ||
            quote_ident(new_column) || '' = cast('' ||
                        quote_ident($2) || '' as numeric(10,2))'';

        execute ''alter table '' || quote_ident($1) ||
            '' drop column '' || quote_ident($2);

        execute ''alter table '' || quote_ident($1) ||
            '' rename column '' || quote_ident(new_column) ||
                '' to '' || quote_ident($2);

    RETURN 1;
END;
'  LANGUAGE 'plpgsql';

SELECT doubletonum('till', 'balance_sent');
SELECT doubletonum('till', 'initial_cash_amount');
SELECT doubletonum('till', 'final_cash_amount');
SELECT doubletonum('delivery_item', 'quantity');
SELECT doubletonum('person_adapt_to_employee', 'salary');
SELECT doubletonum('person_adapt_to_sales_person', 'comission');
SELECT doubletonum('person_adapt_to_transporter', 'freight_percentage');
SELECT doubletonum('employee_role_history', 'salary');
SELECT doubletonum('person_adapt_to_employee', 'salary');
SELECT doubletonum('renegotiation_adapt_to_gift_certificate', 'overpaid_value');
SELECT doubletonum('renegotiation_adapt_to_sale_return_money', 'overpaid_value');
SELECT doubletonum('renegotiation_adapt_to_outstanding_value', 'outstanding_value');
SELECT doubletonum('purchase_item', 'quantity');
SELECT doubletonum('purchase_item', 'quantity_received');
SELECT doubletonum('purchase_item', 'base_cost');
SELECT doubletonum('purchase_item', 'cost');
SELECT doubletonum('purchase_order', 'freight');
SELECT doubletonum('purchase_order', 'charge_value');
SELECT doubletonum('purchase_order', 'discount_value');
SELECT doubletonum('receiving_order_item', 'quantity_received');
SELECT doubletonum('receiving_order_item', 'cost');
SELECT doubletonum('receiving_order', 'invoice_total');
SELECT doubletonum('receiving_order', 'freight_total');
SELECT doubletonum('receiving_order', 'charge_value');
SELECT doubletonum('receiving_order', 'discount_value');
SELECT doubletonum('receiving_order', 'icms_total');
SELECT doubletonum('receiving_order', 'ipi_total');
SELECT doubletonum('product_supplier_info', 'base_cost');
SELECT doubletonum('product_supplier_info', 'icms');
SELECT doubletonum('product_stock_reference', 'quantity');
SELECT doubletonum('product_stock_reference', 'logic_quantity');
SELECT doubletonum('abstract_sellable_item', 'quantity');
SELECT doubletonum('abstract_sellable_item', 'base_price');
SELECT doubletonum('abstract_sellable_item', 'price');
SELECT doubletonum('on_sale_info', 'on_sale_price');
SELECT doubletonum('base_sellable_info', 'price');
SELECT doubletonum('base_sellable_info', 'max_discount');
SELECT doubletonum('base_sellable_info', 'commission');
SELECT doubletonum('abstract_sellable', 'markup');
SELECT doubletonum('abstract_sellable', 'cost');
SELECT doubletonum('abstract_stock_item', 'stock_cost');
SELECT doubletonum('abstract_stock_item', 'quantity');
SELECT doubletonum('abstract_stock_item', 'logic_quantity');
SELECT doubletonum('sale', 'discount_value');
SELECT doubletonum('sale', 'charge_value');
SELECT doubletonum('payment', 'paid_value');
SELECT doubletonum('payment', 'base_value');
SELECT doubletonum('payment', 'value');
SELECT doubletonum('payment', 'interest');
SELECT doubletonum('payment', 'discount');
SELECT doubletonum('payment_method_details', 'commission');
SELECT doubletonum('abstract_check_bill_adapter', 'monthly_interest');
SELECT doubletonum('abstract_check_bill_adapter', 'daily_penalty');
DROP FUNCTION doubletonum(text, text);


---- Ups... losing data here. But unfortunately there is no other solution
---- when converting a string field to an integer field
ALTER TABLE sale DROP COLUMN order_number;
ALTER TABLE sale ADD COLUMN order_number integer;

---- useless column
ALTER TABLE abstract_payment_group DROP COLUMN daily_penalty;

ALTER TABLE bill_check_group_data RENAME COLUMN interest TO monthly_interest;

ALTER TABLE inheritable_model_adapter
            ADD COLUMN model_created timestamp without time zone;
ALTER TABLE inheritable_model_adapter
            ADD COLUMN model_modified timestamp without time zone;
ALTER TABLE inheritable_model_adapter ADD COLUMN is_valid_model boolean;
UPDATE inheritable_model_adapter SET is_valid_model = true;
UPDATE inheritable_model_adapter SET model_created = 'now';
UPDATE inheritable_model_adapter SET model_modified = 'now';

-- fixing the next value of inheritable_model_adapter sequence
CREATE OR REPLACE FUNCTION fix_sequence() RETURNS integer AS '
DECLARE
    max_id integer;
BEGIN
        perform setval(''inheritable_model_adapter_id_seq'',
                    (select max(id) from inheritable_model_adapter));

    RETURN 1;
END;
'  LANGUAGE 'plpgsql';

SELECT fix_sequence();
DROP FUNCTION fix_sequence();


--this parameter was erroneusly set in the last version, fixing it
UPDATE parameter_data SET field_value = (SELECT id FROM
person_adapt_to_company WHERE original_id = (SELECT field_value FROM
parameter_data WHERE field_name='CURRENT_WAREHOUSE')) WHERE field_name =
'CURRENT_WAREHOUSE';
