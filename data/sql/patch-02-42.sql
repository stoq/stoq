-- Alterando precisao de numeros no postgres. Com uma precisao 10, para o
-- caso de valores onde se tem 4 casas decimais, sobram apenas 6 para a
-- parte inteira, limitando bastante o valor.

-- Colocando uma precisão de 20 para termos mais seguranca quanto aos
-- valores maximos permitidos.

-- Price Columns

-- account.py
ALTER TABLE account_transaction ALTER COLUMN value TYPE numeric(20, 2);

-- commission.py
ALTER TABLE commission ALTER COLUMN value TYPE numeric(20, 2);

-- devices.py
ALTER TABLE fiscal_day_tax ALTER COLUMN value TYPE numeric(20, 2);
ALTER TABLE fiscal_day_history ALTER COLUMN period_total TYPE numeric(20, 2);
ALTER TABLE fiscal_day_history ALTER COLUMN total TYPE numeric(20, 2);

-- fiscal.py
ALTER TABLE fiscal_book_entry ALTER COLUMN iss_value TYPE numeric(20, 2);
ALTER TABLE fiscal_book_entry ALTER COLUMN icms_value TYPE numeric(20, 2);
ALTER TABLE fiscal_book_entry ALTER COLUMN ipi_value TYPE numeric(20, 2);

-- inventory.py
ALTER TABLE inventory_item ALTER COLUMN product_cost TYPE numeric(20, 8);

-- loan.py
ALTER TABLE loan_item ALTER COLUMN price TYPE numeric(20, 2);

-- payment/method.py
ALTER TABLE credit_card_data ALTER COLUMN fee_value TYPE numeric(20, 2);
ALTER TABLE credit_card_data ALTER COLUMN entrance_value TYPE numeric(20, 2);

-- payment/payment.py
ALTER TABLE payment ALTER COLUMN paid_value TYPE numeric(20, 2);
ALTER TABLE payment ALTER COLUMN base_value TYPE numeric(20, 2);
ALTER TABLE payment ALTER COLUMN value TYPE numeric(20, 2);
ALTER TABLE payment ALTER COLUMN interest TYPE numeric(20, 2);
ALTER TABLE payment ALTER COLUMN discount TYPE numeric(20, 2);
ALTER TABLE payment ALTER COLUMN penalty TYPE numeric(20, 2);

ALTER TABLE payment_flow_history ALTER COLUMN to_receive TYPE numeric(20, 2);
ALTER TABLE payment_flow_history ALTER COLUMN received TYPE numeric(20, 2);
ALTER TABLE payment_flow_history ALTER COLUMN to_pay TYPE numeric(20, 2);
ALTER TABLE payment_flow_history ALTER COLUMN paid TYPE numeric(20, 2);
ALTER TABLE payment_flow_history ALTER COLUMN balance_expected TYPE numeric(20, 2);
ALTER TABLE payment_flow_history ALTER COLUMN balance_real TYPE numeric(20, 2);

-- payment/renegotiation.py
ALTER TABLE payment_renegotiation ALTER COLUMN discount_value TYPE numeric(20, 2);
ALTER TABLE payment_renegotiation ALTER COLUMN surcharge_value TYPE numeric(20, 2);
ALTER TABLE payment_renegotiation ALTER COLUMN total TYPE numeric(20, 2);

-- person.py
ALTER TABLE person_adapt_to_client ALTER COLUMN credit_limit TYPE numeric(20, 2);
ALTER TABLE person_adapt_to_employee ALTER COLUMN salary TYPE numeric(20, 2);
ALTER TABLE person_adapt_to_credit_provider ALTER COLUMN monthly_fee TYPE numeric(20, 2);
ALTER TABLE employee_role_history ALTER COLUMN salary TYPE numeric(20, 2);

-- product.py
ALTER TABLE product_supplier_info ALTER COLUMN base_cost TYPE numeric(20, 8);
ALTER TABLE product_stock_item ALTER COLUMN stock_cost TYPE numeric(20, 8);

-- purchase.py
ALTER TABLE purchase_item ALTER COLUMN base_cost TYPE numeric(20, 8);
ALTER TABLE purchase_item ALTER COLUMN cost TYPE numeric(20, 8);
ALTER TABLE purchase_order ALTER COLUMN expected_freight TYPE numeric(20, 2);
ALTER TABLE purchase_order ALTER COLUMN surcharge_value TYPE numeric(20, 2);
ALTER TABLE purchase_order ALTER COLUMN discount_value TYPE numeric(20, 2);

-- receiving.py
ALTER TABLE receiving_order_item ALTER COLUMN cost TYPE numeric(20, 8);
ALTER TABLE receiving_order ALTER COLUMN freight_total TYPE numeric(20, 2);
ALTER TABLE receiving_order ALTER COLUMN surcharge_value TYPE numeric(20, 2);
ALTER TABLE receiving_order ALTER COLUMN discount_value TYPE numeric(20, 2);
ALTER TABLE receiving_order ALTER COLUMN secure_value TYPE numeric(20, 2);
ALTER TABLE receiving_order ALTER COLUMN expense_value TYPE numeric(20, 2);
ALTER TABLE receiving_order ALTER COLUMN icms_total TYPE numeric(20, 2);
ALTER TABLE receiving_order ALTER COLUMN ipi_total TYPE numeric(20, 2);
ALTER TABLE receiving_order ALTER COLUMN invoice_total TYPE numeric(20, 2);

-- renegotiation.py
ALTER TABLE renegotiation_data ALTER COLUMN paid_total TYPE numeric(20, 2);
ALTER TABLE renegotiation_data ALTER COLUMN penalty_value TYPE numeric(20, 2);

-- sale.py
ALTER TABLE sale_item ALTER COLUMN base_price TYPE numeric(20, 2);
ALTER TABLE sale_item ALTER COLUMN average_cost TYPE numeric(20, 8);
ALTER TABLE sale_item ALTER COLUMN price TYPE numeric(20, 2);
ALTER TABLE sale ALTER COLUMN discount_value TYPE numeric(20, 2);
ALTER TABLE sale ALTER COLUMN surcharge_value TYPE numeric(20, 2);
ALTER TABLE sale ALTER COLUMN total_amount TYPE numeric(20, 2);

-- sellable.py
ALTER TABLE on_sale_info ALTER COLUMN on_sale_price TYPE numeric(20, 2);
ALTER TABLE base_sellable_info ALTER COLUMN price TYPE numeric(20, 2);
ALTER TABLE client_category_price ALTER COLUMN price TYPE numeric(20, 2);
ALTER TABLE sellable ALTER COLUMN cost TYPE numeric(20, 8);


-- taxes.py
ALTER TABLE sale_item_icms ALTER COLUMN v_bc TYPE numeric(20, 2);
ALTER TABLE sale_item_icms ALTER COLUMN v_icms TYPE numeric(20, 2);
ALTER TABLE sale_item_icms ALTER COLUMN v_bc_st TYPE numeric(20, 2);
ALTER TABLE sale_item_icms ALTER COLUMN v_icms_st TYPE numeric(20, 2);
ALTER TABLE sale_item_icms ALTER COLUMN v_cred_icms_sn TYPE numeric(20, 2);
ALTER TABLE sale_item_icms ALTER COLUMN v_bc_st_ret TYPE numeric(20, 2);
ALTER TABLE sale_item_icms ALTER COLUMN v_icms_st_ret TYPE numeric(20, 2);

ALTER TABLE sale_item_ipi ALTER COLUMN v_ipi TYPE numeric(20, 2);
ALTER TABLE sale_item_ipi ALTER COLUMN v_bc TYPE numeric(20, 2);
ALTER TABLE sale_item_ipi ALTER COLUMN v_unid TYPE numeric(20, 2);

-- till.py
ALTER TABLE till ALTER COLUMN initial_cash_amount TYPE numeric(20, 2);
ALTER TABLE till ALTER COLUMN final_cash_amount TYPE numeric(20, 2);
ALTER TABLE till_entry ALTER COLUMN value TYPE numeric(20, 2);


--
-- Quantity Columns
--


-- inventory.py
ALTER TABLE inventory_item ALTER COLUMN recorded_quantity TYPE numeric(20, 3);
ALTER TABLE inventory_item ALTER COLUMN actual_quantity TYPE numeric(20, 3);

-- loan.py
ALTER TABLE loan_item ALTER COLUMN quantity TYPE numeric(20, 3);
ALTER TABLE loan_item ALTER COLUMN sale_quantity TYPE numeric(20, 3);
ALTER TABLE loan_item ALTER COLUMN return_quantity TYPE numeric(20, 3);


-- production.py
ALTER TABLE production_item ALTER COLUMN quantity TYPE numeric(20, 3);
ALTER TABLE production_item ALTER COLUMN produced TYPE numeric(20, 3);
ALTER TABLE production_item ALTER COLUMN lost TYPE numeric(20, 3);

ALTER TABLE production_material ALTER COLUMN needed TYPE numeric(20, 3);
ALTER TABLE production_material ALTER COLUMN allocated TYPE numeric(20, 3);
ALTER TABLE production_material ALTER COLUMN consumed TYPE numeric(20, 3);
ALTER TABLE production_material ALTER COLUMN lost TYPE numeric(20, 3);
ALTER TABLE production_material ALTER COLUMN to_purchase TYPE numeric(20, 3);
ALTER TABLE production_material ALTER COLUMN to_make TYPE numeric(20, 3);

ALTER TABLE production_service ALTER COLUMN quantity TYPE numeric(20, 3);-- Really?

-- product.py
ALTER TABLE product_supplier_info ALTER COLUMN minimum_purchase TYPE numeric(20, 3);

ALTER TABLE product_history ALTER COLUMN quantity_sold TYPE numeric(20,3);
ALTER TABLE product_history ALTER COLUMN quantity_received TYPE numeric(20,3);
ALTER TABLE product_history ALTER COLUMN quantity_transfered TYPE numeric(20,3);
ALTER TABLE product_history ALTER COLUMN quantity_produced TYPE numeric(20,3);
ALTER TABLE product_history ALTER COLUMN quantity_consumed TYPE numeric(20,3);
ALTER TABLE product_history ALTER COLUMN quantity_lost TYPE numeric(20,3);
ALTER TABLE product_history ALTER COLUMN quantity_decreased TYPE numeric(20,3);

ALTER TABLE product_stock_item ALTER COLUMN quantity TYPE numeric(20,3);
ALTER TABLE product_stock_item ALTER COLUMN logic_quantity TYPE numeric(20,3);

ALTER TABLE product_adapt_to_storable ALTER COLUMN minimum_quantity TYPE numeric(20,3);
ALTER TABLE product_adapt_to_storable ALTER COLUMN maximum_quantity TYPE numeric(20,3);

ALTER TABLE product_component ALTER COLUMN quantity TYPE numeric(20,3);

-- purchase.py
ALTER TABLE purchase_item ALTER COLUMN quantity TYPE numeric(20,3);
ALTER TABLE purchase_item ALTER COLUMN quantity_received TYPE numeric(20,3);
ALTER TABLE purchase_item ALTER COLUMN quantity_sold TYPE numeric(20,3);
ALTER TABLE purchase_item ALTER COLUMN quantity_returned TYPE numeric(20,3);

-- receiving.py
ALTER TABLE receiving_order_item ALTER COLUMN quantity TYPE numeric(20,3);

-- sale.py
ALTER TABLE sale_item ALTER COLUMN quantity TYPE numeric(20, 3);
ALTER TABLE delivery_item ALTER COLUMN quantity TYPE numeric(20, 3);

-- stockdecrease.py
ALTER TABLE stock_decrease_item ALTER COLUMN quantity TYPE numeric(20, 3);

-- transfer.py
ALTER TABLE transfer_order_item ALTER COLUMN quantity TYPE numeric(20, 3);

