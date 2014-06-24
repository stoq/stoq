-- Pass 0: Fix up broken tables

UPDATE fiscal_book_entry SET branch_id = field_value::bigint
  FROM parameter_data
 WHERE (branch_id IS NULL AND
        parameter_data.field_name = 'MAIN_COMPANY');

-- Pass 1: Enable extension

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Pass 2: Add a new temporary ID column

ALTER TABLE account ADD COLUMN temp_id bigint;
ALTER TABLE account_transaction ADD COLUMN temp_id bigint;
ALTER TABLE address ADD COLUMN temp_id bigint;
ALTER TABLE attachment ADD COLUMN temp_id bigint;
ALTER TABLE bank_account ADD COLUMN temp_id bigint;
ALTER TABLE bill_option ADD COLUMN temp_id bigint;
ALTER TABLE branch ADD COLUMN temp_id bigint;
ALTER TABLE branch_station ADD COLUMN temp_id bigint;
ALTER TABLE calls ADD COLUMN temp_id bigint;
ALTER TABLE card_installment_settings ADD COLUMN temp_id bigint;
ALTER TABLE card_installments_provider_details ADD COLUMN temp_id bigint;
ALTER TABLE card_installments_store_details ADD COLUMN temp_id bigint;
ALTER TABLE card_operation_cost ADD COLUMN temp_id bigint;
ALTER TABLE card_payment_device ADD COLUMN temp_id bigint;
ALTER TABLE cfop_data ADD COLUMN temp_id bigint;
ALTER TABLE check_data ADD COLUMN temp_id bigint;
ALTER TABLE client ADD COLUMN temp_id bigint;
ALTER TABLE client_category ADD COLUMN temp_id bigint;
ALTER TABLE client_category_price ADD COLUMN temp_id bigint;
ALTER TABLE client_salary_history ADD COLUMN temp_id bigint;
ALTER TABLE commission ADD COLUMN temp_id bigint;
ALTER TABLE commission_source ADD COLUMN temp_id bigint;
ALTER TABLE company ADD COLUMN temp_id bigint;
ALTER TABLE contact_info ADD COLUMN temp_id bigint;
ALTER TABLE cost_center ADD COLUMN temp_id bigint;
ALTER TABLE cost_center_entry ADD COLUMN temp_id bigint;
ALTER TABLE credit_card_data ADD COLUMN temp_id bigint;
ALTER TABLE credit_card_details ADD COLUMN temp_id bigint;
ALTER TABLE credit_check_history ADD COLUMN temp_id bigint;
ALTER TABLE credit_provider ADD COLUMN temp_id bigint;
ALTER TABLE delivery ADD COLUMN temp_id bigint;
ALTER TABLE device_constant ADD COLUMN temp_id bigint;
ALTER TABLE device_settings ADD COLUMN temp_id bigint;
ALTER TABLE employee ADD COLUMN temp_id bigint;
ALTER TABLE employee_role ADD COLUMN temp_id bigint;
ALTER TABLE employee_role_history ADD COLUMN temp_id bigint;
ALTER TABLE fiscal_book_entry ADD COLUMN temp_id bigint;
ALTER TABLE fiscal_day_history ADD COLUMN temp_id bigint;
ALTER TABLE fiscal_day_tax ADD COLUMN temp_id bigint;
ALTER TABLE fiscal_sale_history ADD COLUMN temp_id bigint;
ALTER TABLE image ADD COLUMN temp_id bigint;
ALTER TABLE individual ADD COLUMN temp_id bigint;
ALTER TABLE installed_plugin ADD COLUMN temp_id bigint;
ALTER TABLE inventory ADD COLUMN temp_id bigint;
ALTER TABLE inventory_item ADD COLUMN temp_id bigint;
ALTER TABLE invoice_field ADD COLUMN temp_id bigint;
ALTER TABLE invoice_layout ADD COLUMN temp_id bigint;
ALTER TABLE invoice_printer ADD COLUMN temp_id bigint;
ALTER TABLE loan ADD COLUMN temp_id bigint;
ALTER TABLE loan_item ADD COLUMN temp_id bigint;
ALTER TABLE login_user ADD COLUMN temp_id bigint;
ALTER TABLE military_data ADD COLUMN temp_id bigint;
ALTER TABLE parameter_data ADD COLUMN temp_id bigint;
ALTER TABLE payment ADD COLUMN temp_id bigint;
ALTER TABLE payment_category ADD COLUMN temp_id bigint;
ALTER TABLE payment_change_history ADD COLUMN temp_id bigint;
ALTER TABLE payment_comment ADD COLUMN temp_id bigint;
ALTER TABLE payment_flow_history ADD COLUMN temp_id bigint;
ALTER TABLE payment_group ADD COLUMN temp_id bigint;
ALTER TABLE payment_method ADD COLUMN temp_id bigint;
ALTER TABLE payment_renegotiation ADD COLUMN temp_id bigint;
ALTER TABLE person ADD COLUMN temp_id bigint;
ALTER TABLE product ADD COLUMN temp_id bigint;
ALTER TABLE product_component ADD COLUMN temp_id bigint;
ALTER TABLE product_history ADD COLUMN temp_id bigint;
ALTER TABLE product_icms_template ADD COLUMN temp_id bigint;
ALTER TABLE production_item ADD COLUMN temp_id bigint;
ALTER TABLE production_item_quality_result ADD COLUMN temp_id bigint;
ALTER TABLE production_material ADD COLUMN temp_id bigint;
ALTER TABLE production_order ADD COLUMN temp_id bigint;
ALTER TABLE production_produced_item ADD COLUMN temp_id bigint;
ALTER TABLE production_service ADD COLUMN temp_id bigint;
ALTER TABLE product_ipi_template ADD COLUMN temp_id bigint;
ALTER TABLE product_manufacturer ADD COLUMN temp_id bigint;
ALTER TABLE product_quality_test ADD COLUMN temp_id bigint;
ALTER TABLE product_stock_item ADD COLUMN temp_id bigint;
ALTER TABLE product_supplier_info ADD COLUMN temp_id bigint;
ALTER TABLE product_tax_template ADD COLUMN temp_id bigint;
ALTER TABLE profile_settings ADD COLUMN temp_id bigint;
ALTER TABLE purchase_item ADD COLUMN temp_id bigint;
ALTER TABLE purchase_order ADD COLUMN temp_id bigint;
ALTER TABLE quotation ADD COLUMN temp_id bigint;
ALTER TABLE quote_group ADD COLUMN temp_id bigint;
ALTER TABLE receiving_order ADD COLUMN temp_id bigint;
ALTER TABLE receiving_order_item ADD COLUMN temp_id bigint;
ALTER TABLE returned_sale ADD COLUMN temp_id bigint;
ALTER TABLE returned_sale_item ADD COLUMN temp_id bigint;
ALTER TABLE sale ADD COLUMN temp_id bigint;
ALTER TABLE sale_item ADD COLUMN temp_id bigint;
ALTER TABLE sale_item_icms ADD COLUMN temp_id bigint;
ALTER TABLE sale_item_ipi ADD COLUMN temp_id bigint;
ALTER TABLE sales_person ADD COLUMN temp_id bigint;
ALTER TABLE sellable ADD COLUMN temp_id bigint;
ALTER TABLE sellable_category ADD COLUMN temp_id bigint;
ALTER TABLE sellable_tax_constant ADD COLUMN temp_id bigint;
ALTER TABLE sellable_unit ADD COLUMN temp_id bigint;
ALTER TABLE service ADD COLUMN temp_id bigint;
ALTER TABLE stock_decrease ADD COLUMN temp_id bigint;
ALTER TABLE stock_decrease_item ADD COLUMN temp_id bigint;
ALTER TABLE stock_transaction_history ADD COLUMN temp_id bigint;
ALTER TABLE storable ADD COLUMN temp_id bigint;
ALTER TABLE storable_batch ADD COLUMN temp_id bigint;
ALTER TABLE supplier ADD COLUMN temp_id bigint;
ALTER TABLE till ADD COLUMN temp_id bigint;
ALTER TABLE till_entry ADD COLUMN temp_id bigint;
ALTER TABLE transfer_order ADD COLUMN temp_id bigint;
ALTER TABLE transfer_order_item ADD COLUMN temp_id bigint;
ALTER TABLE transporter ADD COLUMN temp_id bigint;
ALTER TABLE ui_field ADD COLUMN temp_id bigint;
ALTER TABLE ui_form ADD COLUMN temp_id bigint;
ALTER TABLE user_branch_access ADD COLUMN temp_id bigint;
ALTER TABLE user_profile ADD COLUMN temp_id bigint;
ALTER TABLE voter_data ADD COLUMN temp_id bigint;
ALTER TABLE work_order ADD COLUMN temp_id bigint;
ALTER TABLE work_order_category ADD COLUMN temp_id bigint;
ALTER TABLE work_order_item ADD COLUMN temp_id bigint;
ALTER TABLE work_order_package ADD COLUMN temp_id bigint;
ALTER TABLE work_order_package_item ADD COLUMN temp_id bigint;
ALTER TABLE work_permit_data ADD COLUMN temp_id bigint;

-- Pass 3: Copy over the ID to the temporary column

UPDATE account SET temp_id = id;
UPDATE account_transaction SET temp_id = id;
UPDATE address SET temp_id = id;
UPDATE attachment SET temp_id = id;
UPDATE bank_account SET temp_id = id;
UPDATE bill_option SET temp_id = id;
UPDATE branch SET temp_id = id;
UPDATE branch_station SET temp_id = id;
UPDATE calls SET temp_id = id;
UPDATE card_installment_settings SET temp_id = id;
UPDATE card_installments_provider_details SET temp_id = id;
UPDATE card_installments_store_details SET temp_id = id;
UPDATE card_operation_cost SET temp_id = id;
UPDATE card_payment_device SET temp_id = id;
UPDATE cfop_data SET temp_id = id;
UPDATE check_data SET temp_id = id;
UPDATE client SET temp_id = id;
UPDATE client_category SET temp_id = id;
UPDATE client_category_price SET temp_id = id;
UPDATE client_salary_history SET temp_id = id;
UPDATE commission SET temp_id = id;
UPDATE commission_source SET temp_id = id;
UPDATE company SET temp_id = id;
UPDATE contact_info SET temp_id = id;
UPDATE cost_center SET temp_id = id;
UPDATE cost_center_entry SET temp_id = id;
UPDATE credit_card_data SET temp_id = id;
UPDATE credit_card_details SET temp_id = id;
UPDATE credit_check_history SET temp_id = id;
UPDATE credit_provider SET temp_id = id;
UPDATE delivery SET temp_id = id;
UPDATE device_constant SET temp_id = id;
UPDATE device_settings SET temp_id = id;
UPDATE employee SET temp_id = id;
UPDATE employee_role SET temp_id = id;
UPDATE employee_role_history SET temp_id = id;
UPDATE fiscal_book_entry SET temp_id = id;
UPDATE fiscal_day_history SET temp_id = id;
UPDATE fiscal_day_tax SET temp_id = id;
UPDATE fiscal_sale_history SET temp_id = id;
UPDATE image SET temp_id = id;
UPDATE individual SET temp_id = id;
UPDATE installed_plugin SET temp_id = id;
UPDATE inventory SET temp_id = id;
UPDATE inventory_item SET temp_id = id;
UPDATE invoice_field SET temp_id = id;
UPDATE invoice_layout SET temp_id = id;
UPDATE invoice_printer SET temp_id = id;
UPDATE loan SET temp_id = id;
UPDATE loan_item SET temp_id = id;
UPDATE login_user SET temp_id = id;
UPDATE military_data SET temp_id = id;
UPDATE parameter_data SET temp_id = id;
UPDATE payment SET temp_id = id;
UPDATE payment_category SET temp_id = id;
UPDATE payment_change_history SET temp_id = id;
UPDATE payment_comment SET temp_id = id;
UPDATE payment_flow_history SET temp_id = id;
UPDATE payment_group SET temp_id = id;
UPDATE payment_method SET temp_id = id;
UPDATE payment_renegotiation SET temp_id = id;
UPDATE person SET temp_id = id;
UPDATE product SET temp_id = id;
UPDATE product_component SET temp_id = id;
UPDATE product_history SET temp_id = id;
UPDATE product_icms_template SET temp_id = id;
UPDATE production_item SET temp_id = id;
UPDATE production_item_quality_result SET temp_id = id;
UPDATE production_material SET temp_id = id;
UPDATE production_order SET temp_id = id;
UPDATE production_produced_item SET temp_id = id;
UPDATE production_service SET temp_id = id;
UPDATE product_ipi_template SET temp_id = id;
UPDATE product_manufacturer SET temp_id = id;
UPDATE product_quality_test SET temp_id = id;
UPDATE product_stock_item SET temp_id = id;
UPDATE product_supplier_info SET temp_id = id;
UPDATE product_tax_template SET temp_id = id;
UPDATE profile_settings SET temp_id = id;
UPDATE purchase_item SET temp_id = id;
UPDATE purchase_order SET temp_id = id;
UPDATE quotation SET temp_id = id;
UPDATE quote_group SET temp_id = id;
UPDATE receiving_order SET temp_id = id;
UPDATE receiving_order_item SET temp_id = id;
UPDATE returned_sale SET temp_id = id;
UPDATE returned_sale_item SET temp_id = id;
UPDATE sale SET temp_id = id;
UPDATE sale_item SET temp_id = id;
UPDATE sale_item_icms SET temp_id = id;
UPDATE sale_item_ipi SET temp_id = id;
UPDATE sales_person SET temp_id = id;
UPDATE sellable SET temp_id = id;
UPDATE sellable_category SET temp_id = id;
UPDATE sellable_tax_constant SET temp_id = id;
UPDATE sellable_unit SET temp_id = id;
UPDATE service SET temp_id = id;
UPDATE stock_decrease SET temp_id = id;
UPDATE stock_decrease_item SET temp_id = id;
UPDATE stock_transaction_history SET temp_id = id;
UPDATE storable SET temp_id = id;
UPDATE storable_batch SET temp_id = id;
UPDATE supplier SET temp_id = id;
UPDATE till SET temp_id = id;
UPDATE till_entry SET temp_id = id;
UPDATE transfer_order SET temp_id = id;
UPDATE transfer_order_item SET temp_id = id;
UPDATE transporter SET temp_id = id;
UPDATE ui_field SET temp_id = id;
UPDATE ui_form SET temp_id = id;
UPDATE user_branch_access SET temp_id = id;
UPDATE user_profile SET temp_id = id;
UPDATE voter_data SET temp_id = id;
UPDATE work_order SET temp_id = id;
UPDATE work_order_category SET temp_id = id;
UPDATE work_order_item SET temp_id = id;
UPDATE work_order_package SET temp_id = id;
UPDATE work_order_package_item SET temp_id = id;
UPDATE work_permit_data SET temp_id = id;

-- Pass 4: Remove the default serial value

ALTER TABLE account ALTER COLUMN id DROP DEFAULT;
ALTER TABLE account_transaction ALTER COLUMN id DROP DEFAULT;
ALTER TABLE address ALTER COLUMN id DROP DEFAULT;
ALTER TABLE attachment ALTER COLUMN id DROP DEFAULT;
ALTER TABLE bank_account ALTER COLUMN id DROP DEFAULT;
ALTER TABLE bill_option ALTER COLUMN id DROP DEFAULT;
ALTER TABLE branch ALTER COLUMN id DROP DEFAULT;
ALTER TABLE branch_station ALTER COLUMN id DROP DEFAULT;
ALTER TABLE calls ALTER COLUMN id DROP DEFAULT;
ALTER TABLE card_installment_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE card_installments_provider_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE card_installments_store_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE card_operation_cost ALTER COLUMN id DROP DEFAULT;
ALTER TABLE card_payment_device ALTER COLUMN id DROP DEFAULT;
ALTER TABLE cfop_data ALTER COLUMN id DROP DEFAULT;
ALTER TABLE check_data ALTER COLUMN id DROP DEFAULT;
ALTER TABLE client ALTER COLUMN id DROP DEFAULT;
ALTER TABLE client_category ALTER COLUMN id DROP DEFAULT;
ALTER TABLE client_category_price ALTER COLUMN id DROP DEFAULT;
ALTER TABLE client_salary_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE commission ALTER COLUMN id DROP DEFAULT;
ALTER TABLE commission_source ALTER COLUMN id DROP DEFAULT;
ALTER TABLE company ALTER COLUMN id DROP DEFAULT;
ALTER TABLE contact_info ALTER COLUMN id DROP DEFAULT;
ALTER TABLE cost_center ALTER COLUMN id DROP DEFAULT;
ALTER TABLE cost_center_entry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE credit_card_data ALTER COLUMN id DROP DEFAULT;
ALTER TABLE credit_card_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE credit_check_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE credit_provider ALTER COLUMN id DROP DEFAULT;
ALTER TABLE delivery ALTER COLUMN id DROP DEFAULT;
ALTER TABLE device_constant ALTER COLUMN id DROP DEFAULT;
ALTER TABLE device_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE employee ALTER COLUMN id DROP DEFAULT;
ALTER TABLE employee_role ALTER COLUMN id DROP DEFAULT;
ALTER TABLE employee_role_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE fiscal_book_entry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE fiscal_day_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE fiscal_day_tax ALTER COLUMN id DROP DEFAULT;
ALTER TABLE fiscal_sale_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE image ALTER COLUMN id DROP DEFAULT;
ALTER TABLE individual ALTER COLUMN id DROP DEFAULT;
ALTER TABLE installed_plugin ALTER COLUMN id DROP DEFAULT;
ALTER TABLE inventory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE inventory_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE invoice_field ALTER COLUMN id DROP DEFAULT;
ALTER TABLE invoice_layout ALTER COLUMN id DROP DEFAULT;
ALTER TABLE invoice_printer ALTER COLUMN id DROP DEFAULT;
ALTER TABLE loan ALTER COLUMN id DROP DEFAULT;
ALTER TABLE loan_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE login_user ALTER COLUMN id DROP DEFAULT;
ALTER TABLE military_data ALTER COLUMN id DROP DEFAULT;
ALTER TABLE parameter_data ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment_category ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment_change_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment_comment ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment_flow_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment_group ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment_method ALTER COLUMN id DROP DEFAULT;
ALTER TABLE payment_renegotiation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE person ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_component ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_icms_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE production_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE production_item_quality_result ALTER COLUMN id DROP DEFAULT;
ALTER TABLE production_material ALTER COLUMN id DROP DEFAULT;
ALTER TABLE production_order ALTER COLUMN id DROP DEFAULT;
ALTER TABLE production_produced_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE production_service ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_ipi_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_manufacturer ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_quality_test ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_stock_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_supplier_info ALTER COLUMN id DROP DEFAULT;
ALTER TABLE product_tax_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE profile_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE purchase_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE purchase_order ALTER COLUMN id DROP DEFAULT;
ALTER TABLE quotation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE quote_group ALTER COLUMN id DROP DEFAULT;
ALTER TABLE receiving_order ALTER COLUMN id DROP DEFAULT;
ALTER TABLE receiving_order_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE returned_sale ALTER COLUMN id DROP DEFAULT;
ALTER TABLE returned_sale_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sale ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sale_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sale_item_icms ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sale_item_ipi ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sales_person ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sellable ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sellable_category ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sellable_tax_constant ALTER COLUMN id DROP DEFAULT;
ALTER TABLE sellable_unit ALTER COLUMN id DROP DEFAULT;
ALTER TABLE service ALTER COLUMN id DROP DEFAULT;
ALTER TABLE stock_decrease ALTER COLUMN id DROP DEFAULT;
ALTER TABLE stock_decrease_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE stock_transaction_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE storable ALTER COLUMN id DROP DEFAULT;
ALTER TABLE storable_batch ALTER COLUMN id DROP DEFAULT;
ALTER TABLE supplier ALTER COLUMN id DROP DEFAULT;
ALTER TABLE till ALTER COLUMN id DROP DEFAULT;
ALTER TABLE till_entry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE transfer_order ALTER COLUMN id DROP DEFAULT;
ALTER TABLE transfer_order_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE transporter ALTER COLUMN id DROP DEFAULT;
ALTER TABLE ui_field ALTER COLUMN id DROP DEFAULT;
ALTER TABLE ui_form ALTER COLUMN id DROP DEFAULT;
ALTER TABLE user_branch_access ALTER COLUMN id DROP DEFAULT;
ALTER TABLE user_profile ALTER COLUMN id DROP DEFAULT;
ALTER TABLE voter_data ALTER COLUMN id DROP DEFAULT;
ALTER TABLE work_order ALTER COLUMN id DROP DEFAULT;
ALTER TABLE work_order_category ALTER COLUMN id DROP DEFAULT;
ALTER TABLE work_order_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE work_order_package ALTER COLUMN id DROP DEFAULT;
ALTER TABLE work_order_package_item ALTER COLUMN id DROP DEFAULT;
ALTER TABLE work_permit_data ALTER COLUMN id DROP DEFAULT;

-- Pass 5: Remove the constraints for the ID columns
--         CASCADE is needed as the references to these columns are going to be
--         temporarily invalid

ALTER TABLE account DROP CONSTRAINT account_pkey CASCADE;
ALTER TABLE account_transaction DROP CONSTRAINT account_transaction_pkey CASCADE;
ALTER TABLE address DROP CONSTRAINT address_pkey CASCADE;
ALTER TABLE attachment DROP CONSTRAINT attachment_pkey CASCADE;
ALTER TABLE bank_account DROP CONSTRAINT bank_account_pkey CASCADE;
ALTER TABLE bill_option DROP CONSTRAINT bill_option_pkey CASCADE;
ALTER TABLE branch DROP CONSTRAINT IF EXISTS branch_pkey CASCADE;
ALTER TABLE branch DROP CONSTRAINT IF EXISTS person_adapt_to_branch_pkey CASCADE;
ALTER TABLE branch_station DROP CONSTRAINT branch_station_pkey CASCADE;
ALTER TABLE calls DROP CONSTRAINT calls_pkey CASCADE;
ALTER TABLE card_installment_settings DROP CONSTRAINT card_installment_settings_pkey CASCADE;
ALTER TABLE card_installments_provider_details DROP CONSTRAINT card_installments_provider_details_pkey CASCADE;
ALTER TABLE card_installments_store_details DROP CONSTRAINT card_installments_store_details_pkey CASCADE;
ALTER TABLE card_operation_cost DROP CONSTRAINT card_operation_cost_pkey CASCADE;
ALTER TABLE card_payment_device DROP CONSTRAINT card_payment_device_pkey CASCADE;
ALTER TABLE cfop_data DROP CONSTRAINT cfop_data_pkey CASCADE;
ALTER TABLE check_data DROP CONSTRAINT check_data_pkey CASCADE;
ALTER TABLE client DROP CONSTRAINT IF EXISTS client_pkey CASCADE;
ALTER TABLE client DROP CONSTRAINT IF EXISTS person_adapt_to_client_pkey CASCADE;
ALTER TABLE client_category DROP CONSTRAINT client_category_pkey CASCADE;
ALTER TABLE client_category_price DROP CONSTRAINT client_category_price_pkey CASCADE;
ALTER TABLE client_salary_history DROP CONSTRAINT client_salary_history_pkey CASCADE;
ALTER TABLE commission DROP CONSTRAINT commission_pkey CASCADE;
ALTER TABLE commission_source DROP CONSTRAINT commission_source_pkey CASCADE;
ALTER TABLE company DROP CONSTRAINT IF EXISTS company_pkey CASCADE;
ALTER TABLE company DROP CONSTRAINT IF EXISTS person_adapt_to_company_pkey CASCADE;
ALTER TABLE contact_info DROP CONSTRAINT liaison_pkey CASCADE;
ALTER TABLE cost_center DROP CONSTRAINT cost_center_pkey CASCADE;
ALTER TABLE cost_center_entry DROP CONSTRAINT cost_center_entry_pkey CASCADE;
ALTER TABLE credit_card_data DROP CONSTRAINT credit_card_data_pkey CASCADE;
ALTER TABLE credit_card_details DROP CONSTRAINT credit_card_details_pkey CASCADE;
ALTER TABLE credit_check_history DROP CONSTRAINT credit_check_history_pkey CASCADE;
ALTER TABLE credit_provider DROP CONSTRAINT IF EXISTS credit_provider_pkey CASCADE;
ALTER TABLE credit_provider DROP CONSTRAINT IF EXISTS person_adapt_to_credit_provider_pkey CASCADE;
ALTER TABLE delivery DROP CONSTRAINT delivery_pkey CASCADE;
ALTER TABLE device_constant DROP CONSTRAINT device_constant_pkey CASCADE;
ALTER TABLE device_settings DROP CONSTRAINT device_settings_pkey CASCADE;
ALTER TABLE employee DROP CONSTRAINT IF EXISTS employee_pkey CASCADE;
ALTER TABLE employee DROP CONSTRAINT IF EXISTS person_adapt_to_employee_pkey CASCADE;
ALTER TABLE employee_role DROP CONSTRAINT employee_role_pkey CASCADE;
ALTER TABLE employee_role_history DROP CONSTRAINT employee_role_history_pkey CASCADE;
ALTER TABLE fiscal_book_entry DROP CONSTRAINT IF EXISTS fiscal_book_entry_pkey CASCADE;
ALTER TABLE fiscal_book_entry DROP CONSTRAINT IF EXISTS abstract_fiscal_book_entry_pkey CASCADE;
ALTER TABLE fiscal_day_history DROP CONSTRAINT fiscal_day_history_pkey CASCADE;
ALTER TABLE fiscal_day_tax DROP CONSTRAINT fiscal_day_tax_pkey CASCADE;
ALTER TABLE fiscal_sale_history DROP CONSTRAINT IF EXISTS fiscal_sale_history_pkey CASCADE;
ALTER TABLE fiscal_sale_history DROP CONSTRAINT IF EXISTS paulista_invoice_pkey CASCADE;
ALTER TABLE image DROP CONSTRAINT image_pkey CASCADE;
ALTER TABLE individual DROP CONSTRAINT IF EXISTS individual_pkey CASCADE;
ALTER TABLE individual DROP CONSTRAINT IF EXISTS person_adapt_to_individual_pkey CASCADE;
ALTER TABLE installed_plugin DROP CONSTRAINT installed_plugin_pkey CASCADE;
ALTER TABLE inventory DROP CONSTRAINT inventory_pkey CASCADE;
ALTER TABLE inventory_item DROP CONSTRAINT inventory_item_pkey CASCADE;
ALTER TABLE invoice_field DROP CONSTRAINT invoice_field_pkey CASCADE;
ALTER TABLE invoice_layout DROP CONSTRAINT invoice_layout_pkey CASCADE;
ALTER TABLE invoice_printer DROP CONSTRAINT invoice_printer_pkey CASCADE;
ALTER TABLE loan DROP CONSTRAINT loan_pkey CASCADE;
ALTER TABLE loan_item DROP CONSTRAINT loan_item_pkey CASCADE;
ALTER TABLE login_user DROP CONSTRAINT IF EXISTS login_user_pkey CASCADE;
ALTER TABLE login_user DROP CONSTRAINT IF EXISTS person_adapt_to_user_pkey CASCADE;
ALTER TABLE military_data DROP CONSTRAINT military_data_pkey CASCADE;
ALTER TABLE parameter_data DROP CONSTRAINT parameter_data_pkey CASCADE;
ALTER TABLE payment DROP CONSTRAINT payment_pkey CASCADE;
ALTER TABLE payment_category DROP CONSTRAINT payment_category_pkey CASCADE;
ALTER TABLE payment_change_history DROP CONSTRAINT IF EXISTS payment_change_history_pkey CASCADE;
ALTER TABLE payment_change_history DROP CONSTRAINT IF EXISTS payment_due_date_info_pkey CASCADE;
ALTER TABLE payment_comment DROP CONSTRAINT payment_comment_pkey CASCADE;
ALTER TABLE payment_flow_history DROP CONSTRAINT payment_flow_history_pkey CASCADE;
ALTER TABLE payment_group DROP CONSTRAINT IF EXISTS payment_group_pkey CASCADE;
ALTER TABLE payment_group DROP CONSTRAINT IF EXISTS abstract_payment_group_pkey CASCADE;
ALTER TABLE payment_method DROP CONSTRAINT IF EXISTS apayment_method_pkey CASCADE;
ALTER TABLE payment_method DROP CONSTRAINT IF EXISTS payment_method_pkey CASCADE;
ALTER TABLE payment_renegotiation DROP CONSTRAINT payment_renegotiation_pkey CASCADE;
ALTER TABLE person DROP CONSTRAINT person_pkey CASCADE;
ALTER TABLE product DROP CONSTRAINT product_pkey CASCADE;
ALTER TABLE product_component DROP CONSTRAINT product_component_pkey CASCADE;
ALTER TABLE product_history DROP CONSTRAINT product_history_pkey CASCADE;
ALTER TABLE product_icms_template DROP CONSTRAINT product_icms_template_pkey CASCADE;
ALTER TABLE production_item DROP CONSTRAINT production_item_pkey CASCADE;
ALTER TABLE production_item_quality_result DROP CONSTRAINT production_item_quality_result_pkey CASCADE;
ALTER TABLE production_material DROP CONSTRAINT production_material_pkey CASCADE;
ALTER TABLE production_order DROP CONSTRAINT production_order_pkey CASCADE;
ALTER TABLE production_produced_item DROP CONSTRAINT production_produced_item_pkey CASCADE;
ALTER TABLE production_service DROP CONSTRAINT production_service_pkey CASCADE;
ALTER TABLE product_ipi_template DROP CONSTRAINT product_ipi_template_pkey CASCADE;
ALTER TABLE product_manufacturer DROP CONSTRAINT product_manufacturer_pkey CASCADE;
ALTER TABLE product_quality_test DROP CONSTRAINT product_quality_test_pkey CASCADE;
ALTER TABLE product_stock_item DROP CONSTRAINT IF EXISTS product_stock_item_pkey CASCADE;
ALTER TABLE product_stock_item DROP CONSTRAINT IF EXISTS abstract_stock_item_pkey CASCADE;
ALTER TABLE product_supplier_info DROP CONSTRAINT product_supplier_info_pkey CASCADE;
ALTER TABLE product_tax_template DROP CONSTRAINT product_tax_template_pkey CASCADE;
ALTER TABLE profile_settings DROP CONSTRAINT profile_settings_pkey CASCADE;
ALTER TABLE purchase_item DROP CONSTRAINT purchase_item_pkey CASCADE;
ALTER TABLE purchase_order DROP CONSTRAINT purchase_order_pkey CASCADE;
ALTER TABLE quotation DROP CONSTRAINT IF EXISTS quotation_pkey CASCADE;
ALTER TABLE quotation DROP CONSTRAINT IF EXISTS purchase_order_adapt_to_quote_pkey CASCADE;
ALTER TABLE quote_group DROP CONSTRAINT quote_group_pkey CASCADE;
ALTER TABLE receiving_order DROP CONSTRAINT receiving_order_pkey CASCADE;
ALTER TABLE receiving_order_item DROP CONSTRAINT receiving_order_item_pkey CASCADE;
ALTER TABLE returned_sale DROP CONSTRAINT returned_sale_pkey CASCADE;
ALTER TABLE returned_sale_item DROP CONSTRAINT returned_sale_item_pkey CASCADE;
ALTER TABLE sale DROP CONSTRAINT sale_pkey CASCADE;
ALTER TABLE sale_item DROP CONSTRAINT IF EXISTS sale_item_pkey CASCADE;
ALTER TABLE sale_item DROP CONSTRAINT IF EXISTS asellable_item_pkey CASCADE;
ALTER TABLE sale_item_icms DROP CONSTRAINT sale_item_icms_pkey CASCADE;
ALTER TABLE sale_item_ipi DROP CONSTRAINT sale_item_ipi_pkey CASCADE;
ALTER TABLE sales_person DROP CONSTRAINT IF EXISTS sales_person_pkey CASCADE;
ALTER TABLE sales_person DROP CONSTRAINT IF EXISTS person_adapt_to_sales_person_pkey CASCADE;
ALTER TABLE sellable DROP CONSTRAINT IF EXISTS sellable_pkey CASCADE;
ALTER TABLE sellable DROP CONSTRAINT IF EXISTS asellable_pkey CASCADE;
ALTER TABLE sellable_category DROP CONSTRAINT IF EXISTS asellable_category_pkey CASCADE;
ALTER TABLE sellable_category DROP CONSTRAINT IF EXISTS sellable_category_pkey CASCADE;
ALTER TABLE sellable_tax_constant DROP CONSTRAINT sellable_tax_constant_pkey CASCADE;
ALTER TABLE sellable_unit DROP CONSTRAINT sellable_unit_pkey CASCADE;
ALTER TABLE service DROP CONSTRAINT service_pkey CASCADE;
ALTER TABLE stock_decrease DROP CONSTRAINT stock_decrease_pkey CASCADE;
ALTER TABLE stock_decrease_item DROP CONSTRAINT stock_decrease_item_pkey CASCADE;
ALTER TABLE stock_transaction_history DROP CONSTRAINT stock_transaction_history_pkey CASCADE;
ALTER TABLE storable DROP CONSTRAINT IF EXISTS storable_pkey CASCADE;
ALTER TABLE storable DROP CONSTRAINT IF EXISTS product_adapt_to_storable_pkey CASCADE;
ALTER TABLE storable_batch DROP CONSTRAINT storable_batch_pkey CASCADE;
ALTER TABLE supplier DROP CONSTRAINT IF EXISTS supplier_pkey CASCADE;
ALTER TABLE supplier DROP CONSTRAINT IF EXISTS person_adapt_to_supplier_pkey CASCADE;
ALTER TABLE till DROP CONSTRAINT till_pkey CASCADE;
ALTER TABLE till_entry DROP CONSTRAINT till_entry_pkey CASCADE;
ALTER TABLE transfer_order DROP CONSTRAINT transfer_order_pkey CASCADE;
ALTER TABLE transfer_order_item DROP CONSTRAINT transfer_order_item_pkey CASCADE;
ALTER TABLE transporter DROP CONSTRAINT IF EXISTS transporter_pkey CASCADE;
ALTER TABLE transporter DROP CONSTRAINT IF EXISTS person_adapt_to_transporter_pkey CASCADE;
ALTER TABLE ui_field DROP CONSTRAINT ui_field_pkey CASCADE;
ALTER TABLE ui_form DROP CONSTRAINT ui_form_pkey CASCADE;
ALTER TABLE user_branch_access DROP CONSTRAINT user_branch_access_pkey CASCADE;
ALTER TABLE user_profile DROP CONSTRAINT user_profile_pkey CASCADE;
ALTER TABLE voter_data DROP CONSTRAINT voter_data_pkey CASCADE;
ALTER TABLE work_order DROP CONSTRAINT work_order_pkey CASCADE;
ALTER TABLE work_order_category DROP CONSTRAINT work_order_category_pkey CASCADE;
ALTER TABLE work_order_item DROP CONSTRAINT work_order_item_pkey CASCADE;
ALTER TABLE work_order_package DROP CONSTRAINT work_order_package_pkey CASCADE;
ALTER TABLE work_order_package_item DROP CONSTRAINT work_order_package_item_pkey CASCADE;
ALTER TABLE work_permit_data DROP CONSTRAINT work_permit_data_pkey CASCADE;

-- Pass 6: Remove NOT NULL for the ID columns

ALTER TABLE account ALTER COLUMN id DROP NOT NULL;
ALTER TABLE account_transaction ALTER COLUMN id DROP NOT NULL;
ALTER TABLE address ALTER COLUMN id DROP NOT NULL;
ALTER TABLE attachment ALTER COLUMN id DROP NOT NULL;
ALTER TABLE bank_account ALTER COLUMN id DROP NOT NULL;
ALTER TABLE bill_option ALTER COLUMN id DROP NOT NULL;
ALTER TABLE branch ALTER COLUMN id DROP NOT NULL;
ALTER TABLE branch_station ALTER COLUMN id DROP NOT NULL;
ALTER TABLE calls ALTER COLUMN id DROP NOT NULL;
ALTER TABLE card_installment_settings ALTER COLUMN id DROP NOT NULL;
ALTER TABLE card_installments_provider_details ALTER COLUMN id DROP NOT NULL;
ALTER TABLE card_installments_store_details ALTER COLUMN id DROP NOT NULL;
ALTER TABLE card_operation_cost ALTER COLUMN id DROP NOT NULL;
ALTER TABLE card_payment_device ALTER COLUMN id DROP NOT NULL;
ALTER TABLE cfop_data ALTER COLUMN id DROP NOT NULL;
ALTER TABLE check_data ALTER COLUMN id DROP NOT NULL;
ALTER TABLE client ALTER COLUMN id DROP NOT NULL;
ALTER TABLE client_category ALTER COLUMN id DROP NOT NULL;
ALTER TABLE client_category_price ALTER COLUMN id DROP NOT NULL;
ALTER TABLE client_salary_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE commission ALTER COLUMN id DROP NOT NULL;
ALTER TABLE commission_source ALTER COLUMN id DROP NOT NULL;
ALTER TABLE company ALTER COLUMN id DROP NOT NULL;
ALTER TABLE contact_info ALTER COLUMN id DROP NOT NULL;
ALTER TABLE cost_center ALTER COLUMN id DROP NOT NULL;
ALTER TABLE cost_center_entry ALTER COLUMN id DROP NOT NULL;
ALTER TABLE credit_card_data ALTER COLUMN id DROP NOT NULL;
ALTER TABLE credit_card_details ALTER COLUMN id DROP NOT NULL;
ALTER TABLE credit_check_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE credit_provider ALTER COLUMN id DROP NOT NULL;
ALTER TABLE delivery ALTER COLUMN id DROP NOT NULL;
ALTER TABLE device_constant ALTER COLUMN id DROP NOT NULL;
ALTER TABLE device_settings ALTER COLUMN id DROP NOT NULL;
ALTER TABLE employee ALTER COLUMN id DROP NOT NULL;
ALTER TABLE employee_role ALTER COLUMN id DROP NOT NULL;
ALTER TABLE employee_role_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE fiscal_book_entry ALTER COLUMN id DROP NOT NULL;
ALTER TABLE fiscal_day_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE fiscal_day_tax ALTER COLUMN id DROP NOT NULL;
ALTER TABLE fiscal_sale_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE image ALTER COLUMN id DROP NOT NULL;
ALTER TABLE individual ALTER COLUMN id DROP NOT NULL;
ALTER TABLE installed_plugin ALTER COLUMN id DROP NOT NULL;
ALTER TABLE inventory ALTER COLUMN id DROP NOT NULL;
ALTER TABLE inventory_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE invoice_field ALTER COLUMN id DROP NOT NULL;
ALTER TABLE invoice_layout ALTER COLUMN id DROP NOT NULL;
ALTER TABLE invoice_printer ALTER COLUMN id DROP NOT NULL;
ALTER TABLE loan ALTER COLUMN id DROP NOT NULL;
ALTER TABLE loan_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE login_user ALTER COLUMN id DROP NOT NULL;
ALTER TABLE military_data ALTER COLUMN id DROP NOT NULL;
ALTER TABLE parameter_data ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment_category ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment_change_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment_comment ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment_flow_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment_group ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment_method ALTER COLUMN id DROP NOT NULL;
ALTER TABLE payment_renegotiation ALTER COLUMN id DROP NOT NULL;
ALTER TABLE person ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_component ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_icms_template ALTER COLUMN id DROP NOT NULL;
ALTER TABLE production_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE production_item_quality_result ALTER COLUMN id DROP NOT NULL;
ALTER TABLE production_material ALTER COLUMN id DROP NOT NULL;
ALTER TABLE production_order ALTER COLUMN id DROP NOT NULL;
ALTER TABLE production_produced_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE production_service ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_ipi_template ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_manufacturer ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_quality_test ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_stock_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_supplier_info ALTER COLUMN id DROP NOT NULL;
ALTER TABLE product_tax_template ALTER COLUMN id DROP NOT NULL;
ALTER TABLE profile_settings ALTER COLUMN id DROP NOT NULL;
ALTER TABLE purchase_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE purchase_order ALTER COLUMN id DROP NOT NULL;
ALTER TABLE quotation ALTER COLUMN id DROP NOT NULL;
ALTER TABLE quote_group ALTER COLUMN id DROP NOT NULL;
ALTER TABLE receiving_order ALTER COLUMN id DROP NOT NULL;
ALTER TABLE receiving_order_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE returned_sale ALTER COLUMN id DROP NOT NULL;
ALTER TABLE returned_sale_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sale ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sale_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sale_item_icms ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sale_item_ipi ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sales_person ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sellable ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sellable_category ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sellable_tax_constant ALTER COLUMN id DROP NOT NULL;
ALTER TABLE sellable_unit ALTER COLUMN id DROP NOT NULL;
ALTER TABLE service ALTER COLUMN id DROP NOT NULL;
ALTER TABLE stock_decrease ALTER COLUMN id DROP NOT NULL;
ALTER TABLE stock_decrease_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE stock_transaction_history ALTER COLUMN id DROP NOT NULL;
ALTER TABLE storable ALTER COLUMN id DROP NOT NULL;
ALTER TABLE storable_batch ALTER COLUMN id DROP NOT NULL;
ALTER TABLE supplier ALTER COLUMN id DROP NOT NULL;
ALTER TABLE till ALTER COLUMN id DROP NOT NULL;
ALTER TABLE till_entry ALTER COLUMN id DROP NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN id DROP NOT NULL;
ALTER TABLE transfer_order_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE transporter ALTER COLUMN id DROP NOT NULL;
ALTER TABLE ui_field ALTER COLUMN id DROP NOT NULL;
ALTER TABLE ui_form ALTER COLUMN id DROP NOT NULL;
ALTER TABLE user_branch_access ALTER COLUMN id DROP NOT NULL;
ALTER TABLE user_profile ALTER COLUMN id DROP NOT NULL;
ALTER TABLE voter_data ALTER COLUMN id DROP NOT NULL;
ALTER TABLE work_order ALTER COLUMN id DROP NOT NULL;
ALTER TABLE work_order_category ALTER COLUMN id DROP NOT NULL;
ALTER TABLE work_order_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE work_order_package ALTER COLUMN id DROP NOT NULL;
ALTER TABLE work_order_package_item ALTER COLUMN id DROP NOT NULL;
ALTER TABLE work_permit_data ALTER COLUMN id DROP NOT NULL;

-- Pass 7: Reset the old ID columns

UPDATE account SET id = NULL;
UPDATE account_transaction SET id = NULL;
UPDATE address SET id = NULL;
UPDATE attachment SET id = NULL;
UPDATE bank_account SET id = NULL;
UPDATE bill_option SET id = NULL;
UPDATE branch SET id = NULL;
UPDATE branch_station SET id = NULL;
UPDATE calls SET id = NULL;
UPDATE card_installment_settings SET id = NULL;
UPDATE card_installments_provider_details SET id = NULL;
UPDATE card_installments_store_details SET id = NULL;
UPDATE card_operation_cost SET id = NULL;
UPDATE card_payment_device SET id = NULL;
UPDATE cfop_data SET id = NULL;
UPDATE check_data SET id = NULL;
UPDATE client SET id = NULL;
UPDATE client_category SET id = NULL;
UPDATE client_category_price SET id = NULL;
UPDATE client_salary_history SET id = NULL;
UPDATE commission SET id = NULL;
UPDATE commission_source SET id = NULL;
UPDATE company SET id = NULL;
UPDATE contact_info SET id = NULL;
UPDATE cost_center SET id = NULL;
UPDATE cost_center_entry SET id = NULL;
UPDATE credit_card_data SET id = NULL;
UPDATE credit_card_details SET id = NULL;
UPDATE credit_check_history SET id = NULL;
UPDATE credit_provider SET id = NULL;
UPDATE delivery SET id = NULL;
UPDATE device_constant SET id = NULL;
UPDATE device_settings SET id = NULL;
UPDATE employee SET id = NULL;
UPDATE employee_role SET id = NULL;
UPDATE employee_role_history SET id = NULL;
UPDATE fiscal_book_entry SET id = NULL;
UPDATE fiscal_day_history SET id = NULL;
UPDATE fiscal_day_tax SET id = NULL;
UPDATE fiscal_sale_history SET id = NULL;
UPDATE image SET id = NULL;
UPDATE individual SET id = NULL;
UPDATE installed_plugin SET id = NULL;
UPDATE inventory SET id = NULL;
UPDATE inventory_item SET id = NULL;
UPDATE invoice_field SET id = NULL;
UPDATE invoice_layout SET id = NULL;
UPDATE invoice_printer SET id = NULL;
UPDATE loan SET id = NULL;
UPDATE loan_item SET id = NULL;
UPDATE login_user SET id = NULL;
UPDATE military_data SET id = NULL;
UPDATE parameter_data SET id = NULL;
UPDATE payment SET id = NULL;
UPDATE payment_category SET id = NULL;
UPDATE payment_change_history SET id = NULL;
UPDATE payment_comment SET id = NULL;
UPDATE payment_flow_history SET id = NULL;
UPDATE payment_group SET id = NULL;
UPDATE payment_method SET id = NULL;
UPDATE payment_renegotiation SET id = NULL;
UPDATE person SET id = NULL;
UPDATE product SET id = NULL;
UPDATE product_component SET id = NULL;
UPDATE product_history SET id = NULL;
UPDATE product_icms_template SET id = NULL;
UPDATE production_item SET id = NULL;
UPDATE production_item_quality_result SET id = NULL;
UPDATE production_material SET id = NULL;
UPDATE production_order SET id = NULL;
UPDATE production_produced_item SET id = NULL;
UPDATE production_service SET id = NULL;
UPDATE product_ipi_template SET id = NULL;
UPDATE product_manufacturer SET id = NULL;
UPDATE product_quality_test SET id = NULL;
UPDATE product_stock_item SET id = NULL;
UPDATE product_supplier_info SET id = NULL;
UPDATE product_tax_template SET id = NULL;
UPDATE profile_settings SET id = NULL;
UPDATE purchase_item SET id = NULL;
UPDATE purchase_order SET id = NULL;
UPDATE quotation SET id = NULL;
UPDATE quote_group SET id = NULL;
UPDATE receiving_order SET id = NULL;
UPDATE receiving_order_item SET id = NULL;
UPDATE returned_sale SET id = NULL;
UPDATE returned_sale_item SET id = NULL;
UPDATE sale SET id = NULL;
UPDATE sale_item SET id = NULL;
UPDATE sale_item_icms SET id = NULL;
UPDATE sale_item_ipi SET id = NULL;
UPDATE sales_person SET id = NULL;
UPDATE sellable SET id = NULL;
UPDATE sellable_category SET id = NULL;
UPDATE sellable_tax_constant SET id = NULL;
UPDATE sellable_unit SET id = NULL;
UPDATE service SET id = NULL;
UPDATE stock_decrease SET id = NULL;
UPDATE stock_decrease_item SET id = NULL;
UPDATE stock_transaction_history SET id = NULL;
UPDATE storable SET id = NULL;
UPDATE storable_batch SET id = NULL;
UPDATE supplier SET id = NULL;
UPDATE till SET id = NULL;
UPDATE till_entry SET id = NULL;
UPDATE transfer_order SET id = NULL;
UPDATE transfer_order_item SET id = NULL;
UPDATE transporter SET id = NULL;
UPDATE ui_field SET id = NULL;
UPDATE ui_form SET id = NULL;
UPDATE user_branch_access SET id = NULL;
UPDATE user_profile SET id = NULL;
UPDATE voter_data SET id = NULL;
UPDATE work_order SET id = NULL;
UPDATE work_order_category SET id = NULL;
UPDATE work_order_item SET id = NULL;
UPDATE work_order_package SET id = NULL;
UPDATE work_order_package_item SET id = NULL;
UPDATE work_permit_data SET id = NULL;

-- Pass 8: Change the column type to uuid

ALTER TABLE account ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE account_transaction ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE address ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE attachment ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE bank_account ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE bill_option ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE branch ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE branch_station ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE calls ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE card_installment_settings ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE card_installments_provider_details ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE card_installments_store_details ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE card_operation_cost ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE card_payment_device ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE cfop_data ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE check_data ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE client ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE client_category ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE client_category_price ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE client_salary_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE commission ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE commission_source ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE company ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE contact_info ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE cost_center ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE cost_center_entry ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE credit_card_data ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE credit_card_details ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE credit_check_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE credit_provider ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE delivery ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE device_constant ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE device_settings ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE employee ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE employee_role ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE employee_role_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE fiscal_book_entry ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE fiscal_day_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE fiscal_day_tax ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE fiscal_sale_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE image ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE individual ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE installed_plugin ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE inventory ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE inventory_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE invoice_field ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE invoice_layout ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE invoice_printer ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE loan ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE loan_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE login_user ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE military_data ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE parameter_data ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment_category ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment_change_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment_comment ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment_flow_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment_group ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment_method ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE payment_renegotiation ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE person ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_component ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_icms_template ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE production_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE production_item_quality_result ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE production_material ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE production_order ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE production_produced_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE production_service ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_ipi_template ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_manufacturer ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_quality_test ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_stock_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_supplier_info ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE product_tax_template ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE profile_settings ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE purchase_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE purchase_order ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE quotation ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE quote_group ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE receiving_order ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE receiving_order_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE returned_sale ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE returned_sale_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sale ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sale_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sale_item_icms ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sale_item_ipi ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sales_person ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sellable ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sellable_category ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sellable_tax_constant ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE sellable_unit ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE service ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE stock_decrease ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE stock_decrease_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE stock_transaction_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE storable ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE storable_batch ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE supplier ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE till ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE till_entry ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE transfer_order ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE transfer_order_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE transporter ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE ui_field ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE ui_form ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE user_branch_access ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE user_profile ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE voter_data ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE work_order ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE work_order_category ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE work_order_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE work_order_package ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE work_order_package_item ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
ALTER TABLE work_permit_data ALTER COLUMN id TYPE uuid USING uuid_generate_v1();

-- Pass 9: Add back a default

ALTER TABLE account ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE account_transaction ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE address ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE attachment ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE bank_account ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE bill_option ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE branch ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE branch_station ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE calls ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE card_installment_settings ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE card_installments_provider_details ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE card_installments_store_details ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE card_operation_cost ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE card_payment_device ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE cfop_data ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE check_data ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE client ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE client_category ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE client_category_price ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE client_salary_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE commission ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE commission_source ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE company ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE contact_info ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE cost_center ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE cost_center_entry ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE credit_card_data ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE credit_card_details ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE credit_check_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE credit_provider ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE delivery ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE device_constant ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE device_settings ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE employee ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE employee_role ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE employee_role_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE fiscal_book_entry ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE fiscal_day_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE fiscal_day_tax ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE fiscal_sale_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE image ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE individual ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE installed_plugin ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE inventory ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE inventory_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE invoice_field ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE invoice_layout ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE invoice_printer ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE loan ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE loan_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE login_user ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE military_data ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE parameter_data ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment_category ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment_change_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment_comment ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment_flow_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment_group ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment_method ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE payment_renegotiation ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE person ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_component ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_icms_template ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE production_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE production_item_quality_result ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE production_material ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE production_order ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE production_produced_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE production_service ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_ipi_template ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_manufacturer ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_quality_test ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_stock_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_supplier_info ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE product_tax_template ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE profile_settings ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE purchase_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE purchase_order ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE quotation ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE quote_group ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE receiving_order ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE receiving_order_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE returned_sale ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE returned_sale_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sale ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sale_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sale_item_icms ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sale_item_ipi ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sales_person ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sellable ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sellable_category ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sellable_tax_constant ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE sellable_unit ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE service ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE stock_decrease ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE stock_decrease_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE stock_transaction_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE storable ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE storable_batch ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE supplier ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE till ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE till_entry ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE transfer_order ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE transfer_order_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE transporter ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE ui_field ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE ui_form ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE user_branch_access ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE user_profile ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE voter_data ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE work_order ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE work_order_category ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE work_order_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE work_order_package ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE work_order_package_item ALTER COLUMN id SET DEFAULT uuid_generate_v1();
ALTER TABLE work_permit_data ALTER COLUMN id SET DEFAULT uuid_generate_v1();

-- Pass 10: Add back the primary keys

ALTER TABLE account ADD CONSTRAINT account_pkey PRIMARY KEY(id);
ALTER TABLE account_transaction ADD CONSTRAINT account_transaction_pkey PRIMARY KEY(id);
ALTER TABLE address ADD CONSTRAINT address_pkey PRIMARY KEY(id);
ALTER TABLE attachment ADD CONSTRAINT attachment_pkey PRIMARY KEY(id);
ALTER TABLE bank_account ADD CONSTRAINT bank_account_pkey PRIMARY KEY(id);
ALTER TABLE bill_option ADD CONSTRAINT bill_option_pkey PRIMARY KEY(id);
ALTER TABLE branch ADD CONSTRAINT branch_pkey PRIMARY KEY(id);
ALTER TABLE branch_station ADD CONSTRAINT branch_station_pkey PRIMARY KEY(id);
ALTER TABLE calls ADD CONSTRAINT calls_pkey PRIMARY KEY(id);
ALTER TABLE card_installment_settings ADD CONSTRAINT card_installment_settings_pkey PRIMARY KEY(id);
ALTER TABLE card_installments_provider_details ADD CONSTRAINT card_installments_provider_details_pkey PRIMARY KEY(id);
ALTER TABLE card_installments_store_details ADD CONSTRAINT card_installments_store_details_pkey PRIMARY KEY(id);
ALTER TABLE card_operation_cost ADD CONSTRAINT card_operation_cost_pkey PRIMARY KEY(id);
ALTER TABLE card_payment_device ADD CONSTRAINT card_payment_device_pkey PRIMARY KEY(id);
ALTER TABLE cfop_data ADD CONSTRAINT cfop_data_pkey PRIMARY KEY(id);
ALTER TABLE check_data ADD CONSTRAINT check_data_pkey PRIMARY KEY(id);
ALTER TABLE client ADD CONSTRAINT client_pkey PRIMARY KEY(id);
ALTER TABLE client_category ADD CONSTRAINT client_category_pkey PRIMARY KEY(id);
ALTER TABLE client_category_price ADD CONSTRAINT client_category_price_pkey PRIMARY KEY(id);
ALTER TABLE client_salary_history ADD CONSTRAINT client_salary_history_pkey PRIMARY KEY(id);
ALTER TABLE commission ADD CONSTRAINT commission_pkey PRIMARY KEY(id);
ALTER TABLE commission_source ADD CONSTRAINT commission_source_pkey PRIMARY KEY(id);
ALTER TABLE company ADD CONSTRAINT company_pkey PRIMARY KEY(id);
ALTER TABLE contact_info ADD CONSTRAINT contact_info_pkey PRIMARY KEY(id);
ALTER TABLE cost_center ADD CONSTRAINT cost_center_pkey PRIMARY KEY(id);
ALTER TABLE cost_center_entry ADD CONSTRAINT cost_center_entry_pkey PRIMARY KEY(id);
ALTER TABLE credit_card_data ADD CONSTRAINT credit_card_data_pkey PRIMARY KEY(id);
ALTER TABLE credit_card_details ADD CONSTRAINT credit_card_details_pkey PRIMARY KEY(id);
ALTER TABLE credit_check_history ADD CONSTRAINT credit_check_history_pkey PRIMARY KEY(id);
ALTER TABLE credit_provider ADD CONSTRAINT credit_provider_pkey PRIMARY KEY(id);
ALTER TABLE delivery ADD CONSTRAINT delivery_pkey PRIMARY KEY(id);
ALTER TABLE device_constant ADD CONSTRAINT device_constant_pkey PRIMARY KEY(id);
ALTER TABLE device_settings ADD CONSTRAINT device_settings_pkey PRIMARY KEY(id);
ALTER TABLE employee ADD CONSTRAINT employee_pkey PRIMARY KEY(id);
ALTER TABLE employee_role ADD CONSTRAINT employee_role_pkey PRIMARY KEY(id);
ALTER TABLE employee_role_history ADD CONSTRAINT employee_role_history_pkey PRIMARY KEY(id);
ALTER TABLE fiscal_book_entry ADD CONSTRAINT fiscal_book_entry_pkey PRIMARY KEY(id);
ALTER TABLE fiscal_day_history ADD CONSTRAINT fiscal_day_history_pkey PRIMARY KEY(id);
ALTER TABLE fiscal_day_tax ADD CONSTRAINT fiscal_day_tax_pkey PRIMARY KEY(id);
ALTER TABLE fiscal_sale_history ADD CONSTRAINT fiscal_sale_history_pkey PRIMARY KEY(id);
ALTER TABLE image ADD CONSTRAINT image_pkey PRIMARY KEY(id);
ALTER TABLE individual ADD CONSTRAINT individual_pkey PRIMARY KEY(id);
ALTER TABLE installed_plugin ADD CONSTRAINT installed_plugin_pkey PRIMARY KEY(id);
ALTER TABLE inventory ADD CONSTRAINT inventory_pkey PRIMARY KEY(id);
ALTER TABLE inventory_item ADD CONSTRAINT inventory_item_pkey PRIMARY KEY(id);
ALTER TABLE invoice_field ADD CONSTRAINT invoice_field_pkey PRIMARY KEY(id);
ALTER TABLE invoice_layout ADD CONSTRAINT invoice_layout_pkey PRIMARY KEY(id);
ALTER TABLE invoice_printer ADD CONSTRAINT invoice_printer_pkey PRIMARY KEY(id);
ALTER TABLE loan ADD CONSTRAINT loan_pkey PRIMARY KEY(id);
ALTER TABLE loan_item ADD CONSTRAINT loan_item_pkey PRIMARY KEY(id);
ALTER TABLE login_user ADD CONSTRAINT login_user_pkey PRIMARY KEY(id);
ALTER TABLE military_data ADD CONSTRAINT military_data_pkey PRIMARY KEY(id);
ALTER TABLE parameter_data ADD CONSTRAINT parameter_data_pkey PRIMARY KEY(id);
ALTER TABLE payment ADD CONSTRAINT payment_pkey PRIMARY KEY(id);
ALTER TABLE payment_category ADD CONSTRAINT payment_category_pkey PRIMARY KEY(id);
ALTER TABLE payment_change_history ADD CONSTRAINT payment_change_history_pkey PRIMARY KEY(id);
ALTER TABLE payment_comment ADD CONSTRAINT payment_comment_pkey PRIMARY KEY(id);
ALTER TABLE payment_flow_history ADD CONSTRAINT payment_flow_history_pkey PRIMARY KEY(id);
ALTER TABLE payment_group ADD CONSTRAINT payment_group_pkey PRIMARY KEY(id);
ALTER TABLE payment_method ADD CONSTRAINT payment_method_pkey PRIMARY KEY(id);
ALTER TABLE payment_renegotiation ADD CONSTRAINT payment_renegotiation_pkey PRIMARY KEY(id);
ALTER TABLE person ADD CONSTRAINT person_pkey PRIMARY KEY(id);
ALTER TABLE product ADD CONSTRAINT product_pkey PRIMARY KEY(id);
ALTER TABLE product_component ADD CONSTRAINT product_component_pkey PRIMARY KEY(id);
ALTER TABLE product_history ADD CONSTRAINT product_history_pkey PRIMARY KEY(id);
ALTER TABLE product_icms_template ADD CONSTRAINT product_icms_template_pkey PRIMARY KEY(id);
ALTER TABLE production_item ADD CONSTRAINT production_item_pkey PRIMARY KEY(id);
ALTER TABLE production_item_quality_result ADD CONSTRAINT production_item_quality_result_pkey PRIMARY KEY(id);
ALTER TABLE production_material ADD CONSTRAINT production_material_pkey PRIMARY KEY(id);
ALTER TABLE production_order ADD CONSTRAINT production_order_pkey PRIMARY KEY(id);
ALTER TABLE production_produced_item ADD CONSTRAINT production_produced_item_pkey PRIMARY KEY(id);
ALTER TABLE production_service ADD CONSTRAINT production_service_pkey PRIMARY KEY(id);
ALTER TABLE product_ipi_template ADD CONSTRAINT product_ipi_template_pkey PRIMARY KEY(id);
ALTER TABLE product_manufacturer ADD CONSTRAINT product_manufacturer_pkey PRIMARY KEY(id);
ALTER TABLE product_quality_test ADD CONSTRAINT product_quality_test_pkey PRIMARY KEY(id);
ALTER TABLE product_stock_item ADD CONSTRAINT product_stock_item_pkey PRIMARY KEY(id);
ALTER TABLE product_supplier_info ADD CONSTRAINT product_supplier_info_pkey PRIMARY KEY(id);
ALTER TABLE product_tax_template ADD CONSTRAINT product_tax_template_pkey PRIMARY KEY(id);
ALTER TABLE profile_settings ADD CONSTRAINT profile_settings_pkey PRIMARY KEY(id);
ALTER TABLE purchase_item ADD CONSTRAINT purchase_item_pkey PRIMARY KEY(id);
ALTER TABLE purchase_order ADD CONSTRAINT purchase_order_pkey PRIMARY KEY(id);
ALTER TABLE quotation ADD CONSTRAINT quotation_pkey PRIMARY KEY(id);
ALTER TABLE quote_group ADD CONSTRAINT quote_group_pkey PRIMARY KEY(id);
ALTER TABLE receiving_order ADD CONSTRAINT receiving_order_pkey PRIMARY KEY(id);
ALTER TABLE receiving_order_item ADD CONSTRAINT receiving_order_item_pkey PRIMARY KEY(id);
ALTER TABLE returned_sale ADD CONSTRAINT returned_sale_pkey PRIMARY KEY(id);
ALTER TABLE returned_sale_item ADD CONSTRAINT returned_sale_item_pkey PRIMARY KEY(id);
ALTER TABLE sale ADD CONSTRAINT sale_pkey PRIMARY KEY(id);
ALTER TABLE sale_item ADD CONSTRAINT sale_item_pkey PRIMARY KEY(id);
ALTER TABLE sale_item_icms ADD CONSTRAINT sale_item_icms_pkey PRIMARY KEY(id);
ALTER TABLE sale_item_ipi ADD CONSTRAINT sale_item_ipi_pkey PRIMARY KEY(id);
ALTER TABLE sales_person ADD CONSTRAINT sales_person_pkey PRIMARY KEY(id);
ALTER TABLE sellable ADD CONSTRAINT sellable_pkey PRIMARY KEY(id);
ALTER TABLE sellable_category ADD CONSTRAINT sellable_category_pkey PRIMARY KEY(id);
ALTER TABLE sellable_tax_constant ADD CONSTRAINT sellable_tax_constant_pkey PRIMARY KEY(id);
ALTER TABLE sellable_unit ADD CONSTRAINT sellable_unit_pkey PRIMARY KEY(id);
ALTER TABLE service ADD CONSTRAINT service_pkey PRIMARY KEY(id);
ALTER TABLE stock_decrease ADD CONSTRAINT stock_decrease_pkey PRIMARY KEY(id);
ALTER TABLE stock_decrease_item ADD CONSTRAINT stock_decrease_item_pkey PRIMARY KEY(id);
ALTER TABLE stock_transaction_history ADD CONSTRAINT stock_transaction_history_pkey PRIMARY KEY(id);
ALTER TABLE storable ADD CONSTRAINT storable_pkey PRIMARY KEY(id);
ALTER TABLE storable_batch ADD CONSTRAINT storable_batch_pkey PRIMARY KEY(id);
ALTER TABLE supplier ADD CONSTRAINT supplier_pkey PRIMARY KEY(id);
ALTER TABLE till ADD CONSTRAINT till_pkey PRIMARY KEY(id);
ALTER TABLE till_entry ADD CONSTRAINT till_entry_pkey PRIMARY KEY(id);
ALTER TABLE transfer_order ADD CONSTRAINT transfer_order_pkey PRIMARY KEY(id);
ALTER TABLE transfer_order_item ADD CONSTRAINT transfer_order_item_pkey PRIMARY KEY(id);
ALTER TABLE transporter ADD CONSTRAINT transporter_pkey PRIMARY KEY(id);
ALTER TABLE ui_field ADD CONSTRAINT ui_field_pkey PRIMARY KEY(id);
ALTER TABLE ui_form ADD CONSTRAINT ui_form_pkey PRIMARY KEY(id);
ALTER TABLE user_branch_access ADD CONSTRAINT user_branch_access_pkey PRIMARY KEY(id);
ALTER TABLE user_profile ADD CONSTRAINT user_profile_pkey PRIMARY KEY(id);
ALTER TABLE voter_data ADD CONSTRAINT voter_data_pkey PRIMARY KEY(id);
ALTER TABLE work_order ADD CONSTRAINT work_order_pkey PRIMARY KEY(id);
ALTER TABLE work_order_category ADD CONSTRAINT work_order_category_pkey PRIMARY KEY(id);
ALTER TABLE work_order_item ADD CONSTRAINT work_order_item_pkey PRIMARY KEY(id);
ALTER TABLE work_order_package ADD CONSTRAINT work_order_package_pkey PRIMARY KEY(id);
ALTER TABLE work_order_package_item ADD CONSTRAINT work_order_package_item_pkey PRIMARY KEY(id);
ALTER TABLE work_permit_data ADD CONSTRAINT work_permit_data_pkey PRIMARY KEY(id);

-- Pass 11: Add back NOT NULL for the id column

ALTER TABLE account ALTER COLUMN id SET NOT NULL;
ALTER TABLE account_transaction ALTER COLUMN id SET NOT NULL;
ALTER TABLE address ALTER COLUMN id SET NOT NULL;
ALTER TABLE attachment ALTER COLUMN id SET NOT NULL;
ALTER TABLE bank_account ALTER COLUMN id SET NOT NULL;
ALTER TABLE bill_option ALTER COLUMN id SET NOT NULL;
ALTER TABLE branch ALTER COLUMN id SET NOT NULL;
ALTER TABLE branch_station ALTER COLUMN id SET NOT NULL;
ALTER TABLE calls ALTER COLUMN id SET NOT NULL;
ALTER TABLE card_installment_settings ALTER COLUMN id SET NOT NULL;
ALTER TABLE card_installments_provider_details ALTER COLUMN id SET NOT NULL;
ALTER TABLE card_installments_store_details ALTER COLUMN id SET NOT NULL;
ALTER TABLE card_operation_cost ALTER COLUMN id SET NOT NULL;
ALTER TABLE card_payment_device ALTER COLUMN id SET NOT NULL;
ALTER TABLE cfop_data ALTER COLUMN id SET NOT NULL;
ALTER TABLE check_data ALTER COLUMN id SET NOT NULL;
ALTER TABLE client ALTER COLUMN id SET NOT NULL;
ALTER TABLE client_category ALTER COLUMN id SET NOT NULL;
ALTER TABLE client_category_price ALTER COLUMN id SET NOT NULL;
ALTER TABLE client_salary_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE commission ALTER COLUMN id SET NOT NULL;
ALTER TABLE commission_source ALTER COLUMN id SET NOT NULL;
ALTER TABLE company ALTER COLUMN id SET NOT NULL;
ALTER TABLE contact_info ALTER COLUMN id SET NOT NULL;
ALTER TABLE cost_center ALTER COLUMN id SET NOT NULL;
ALTER TABLE cost_center_entry ALTER COLUMN id SET NOT NULL;
ALTER TABLE credit_card_data ALTER COLUMN id SET NOT NULL;
ALTER TABLE credit_card_details ALTER COLUMN id SET NOT NULL;
ALTER TABLE credit_check_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE credit_provider ALTER COLUMN id SET NOT NULL;
ALTER TABLE delivery ALTER COLUMN id SET NOT NULL;
ALTER TABLE device_constant ALTER COLUMN id SET NOT NULL;
ALTER TABLE device_settings ALTER COLUMN id SET NOT NULL;
ALTER TABLE employee ALTER COLUMN id SET NOT NULL;
ALTER TABLE employee_role ALTER COLUMN id SET NOT NULL;
ALTER TABLE employee_role_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE fiscal_book_entry ALTER COLUMN id SET NOT NULL;
ALTER TABLE fiscal_day_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE fiscal_day_tax ALTER COLUMN id SET NOT NULL;
ALTER TABLE fiscal_sale_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE image ALTER COLUMN id SET NOT NULL;
ALTER TABLE individual ALTER COLUMN id SET NOT NULL;
ALTER TABLE installed_plugin ALTER COLUMN id SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN id SET NOT NULL;
ALTER TABLE inventory_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE invoice_field ALTER COLUMN id SET NOT NULL;
ALTER TABLE invoice_layout ALTER COLUMN id SET NOT NULL;
ALTER TABLE invoice_printer ALTER COLUMN id SET NOT NULL;
ALTER TABLE loan ALTER COLUMN id SET NOT NULL;
ALTER TABLE loan_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE login_user ALTER COLUMN id SET NOT NULL;
ALTER TABLE military_data ALTER COLUMN id SET NOT NULL;
ALTER TABLE parameter_data ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment_category ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment_change_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment_comment ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment_flow_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment_group ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment_method ALTER COLUMN id SET NOT NULL;
ALTER TABLE payment_renegotiation ALTER COLUMN id SET NOT NULL;
ALTER TABLE person ALTER COLUMN id SET NOT NULL;
ALTER TABLE product ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_component ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_icms_template ALTER COLUMN id SET NOT NULL;
ALTER TABLE production_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE production_item_quality_result ALTER COLUMN id SET NOT NULL;
ALTER TABLE production_material ALTER COLUMN id SET NOT NULL;
ALTER TABLE production_order ALTER COLUMN id SET NOT NULL;
ALTER TABLE production_produced_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE production_service ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_ipi_template ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_manufacturer ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_quality_test ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_stock_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_supplier_info ALTER COLUMN id SET NOT NULL;
ALTER TABLE product_tax_template ALTER COLUMN id SET NOT NULL;
ALTER TABLE profile_settings ALTER COLUMN id SET NOT NULL;
ALTER TABLE purchase_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE purchase_order ALTER COLUMN id SET NOT NULL;
ALTER TABLE quotation ALTER COLUMN id SET NOT NULL;
ALTER TABLE quote_group ALTER COLUMN id SET NOT NULL;
ALTER TABLE receiving_order ALTER COLUMN id SET NOT NULL;
ALTER TABLE receiving_order_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE returned_sale ALTER COLUMN id SET NOT NULL;
ALTER TABLE returned_sale_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE sale ALTER COLUMN id SET NOT NULL;
ALTER TABLE sale_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE sale_item_icms ALTER COLUMN id SET NOT NULL;
ALTER TABLE sale_item_ipi ALTER COLUMN id SET NOT NULL;
ALTER TABLE sales_person ALTER COLUMN id SET NOT NULL;
ALTER TABLE sellable ALTER COLUMN id SET NOT NULL;
ALTER TABLE sellable_category ALTER COLUMN id SET NOT NULL;
ALTER TABLE sellable_tax_constant ALTER COLUMN id SET NOT NULL;
ALTER TABLE sellable_unit ALTER COLUMN id SET NOT NULL;
ALTER TABLE service ALTER COLUMN id SET NOT NULL;
ALTER TABLE stock_decrease ALTER COLUMN id SET NOT NULL;
ALTER TABLE stock_decrease_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE stock_transaction_history ALTER COLUMN id SET NOT NULL;
ALTER TABLE storable ALTER COLUMN id SET NOT NULL;
ALTER TABLE storable_batch ALTER COLUMN id SET NOT NULL;
ALTER TABLE supplier ALTER COLUMN id SET NOT NULL;
ALTER TABLE till ALTER COLUMN id SET NOT NULL;
ALTER TABLE till_entry ALTER COLUMN id SET NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN id SET NOT NULL;
ALTER TABLE transfer_order_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE transporter ALTER COLUMN id SET NOT NULL;
ALTER TABLE ui_field ALTER COLUMN id SET NOT NULL;
ALTER TABLE ui_form ALTER COLUMN id SET NOT NULL;
ALTER TABLE user_branch_access ALTER COLUMN id SET NOT NULL;
ALTER TABLE user_profile ALTER COLUMN id SET NOT NULL;
ALTER TABLE voter_data ALTER COLUMN id SET NOT NULL;
ALTER TABLE work_order ALTER COLUMN id SET NOT NULL;
ALTER TABLE work_order_category ALTER COLUMN id SET NOT NULL;
ALTER TABLE work_order_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE work_order_package ALTER COLUMN id SET NOT NULL;
ALTER TABLE work_order_package_item ALTER COLUMN id SET NOT NULL;
ALTER TABLE work_permit_data ALTER COLUMN id SET NOT NULL;

-- Pass 12: Temporarily disable some constraints/not null

ALTER TABLE commission_source DROP CONSTRAINT check_exist_one_fkey;
ALTER TABLE cost_center_entry DROP CONSTRAINT stock_transaction_or_payment;
ALTER TABLE product_component DROP CONSTRAINT different_products;
ALTER TABLE work_order_package DROP CONSTRAINT different_branches;

ALTER TABLE account_transaction ALTER COLUMN account_id DROP NOT NULL;
ALTER TABLE account_transaction ALTER COLUMN source_account_id DROP NOT NULL;
ALTER TABLE branch_synchronization ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE commission ALTER COLUMN payment_id DROP NOT NULL;
ALTER TABLE commission ALTER COLUMN sale_id DROP NOT NULL;
ALTER TABLE commission ALTER COLUMN salesperson_id DROP NOT NULL;
ALTER TABLE cost_center_entry ALTER COLUMN cost_center_id DROP NOT NULL;
ALTER TABLE fiscal_book_entry ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE inventory ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE inventory_item ALTER COLUMN inventory_id DROP NOT NULL;
ALTER TABLE inventory_item ALTER COLUMN product_id DROP NOT NULL;
ALTER TABLE loan ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE payment ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE payment_method ALTER COLUMN destination_account_id DROP NOT NULL;
ALTER TABLE payment_renegotiation ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE product_history ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE product_stock_item ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE product_supplier_info ALTER COLUMN product_id DROP NOT NULL;
ALTER TABLE product_supplier_info ALTER COLUMN supplier_id DROP NOT NULL;
ALTER TABLE production_order ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE purchase_order ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE quotation ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE quote_group ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE receiving_order ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE receiving_order ALTER COLUMN purchase_id DROP NOT NULL;
ALTER TABLE returned_sale ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE sale ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE stock_decrease ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE stock_transaction_history ALTER COLUMN product_stock_item_id DROP NOT NULL;
ALTER TABLE stock_transaction_history ALTER COLUMN responsible_id DROP NOT NULL;
ALTER TABLE storable_batch ALTER COLUMN storable_id DROP NOT NULL;
ALTER TABLE till_entry ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE till_entry ALTER COLUMN till_id DROP NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN destination_branch_id DROP NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN destination_responsible_id DROP NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN source_branch_id DROP NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN source_responsible_id DROP NOT NULL;
ALTER TABLE transfer_order_item ALTER COLUMN sellable_id DROP NOT NULL;
ALTER TABLE transfer_order_item ALTER COLUMN transfer_order_id DROP NOT NULL;
ALTER TABLE user_branch_access ALTER COLUMN branch_id DROP NOT NULL;
ALTER TABLE user_branch_access ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE work_order_package ALTER COLUMN source_branch_id DROP NOT NULL;
ALTER TABLE work_order_package_item ALTER COLUMN order_id DROP NOT NULL;
ALTER TABLE work_order_package_item ALTER COLUMN package_id DROP NOT NULL;

-- Pass 13: Update foreign keys

ALTER TABLE client ADD COLUMN temp_person_id bigint;
UPDATE client SET temp_person_id = person_id;

ALTER TABLE client ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE client ADD CONSTRAINT client_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE client SET person_id = person.id
    FROM person
    WHERE client.temp_person_id = person.temp_id;

ALTER TABLE client DROP COLUMN temp_person_id;




ALTER TABLE client ADD COLUMN temp_category_id bigint;
UPDATE client SET temp_category_id = category_id;

ALTER TABLE client ALTER COLUMN category_id TYPE uuid USING NULL;

ALTER TABLE client ADD CONSTRAINT client_category_id_fkey FOREIGN KEY (category_id) REFERENCES client_category (id) ON UPDATE CASCADE;

UPDATE client SET category_id = client_category.id
    FROM client_category
    WHERE client.temp_category_id = client_category.temp_id;

ALTER TABLE client DROP COLUMN temp_category_id;




ALTER TABLE company ADD COLUMN temp_person_id bigint;
UPDATE company SET temp_person_id = person_id;

ALTER TABLE company ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE company ADD CONSTRAINT company_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE company SET person_id = person.id
    FROM person
    WHERE company.temp_person_id = person.temp_id;

ALTER TABLE company DROP COLUMN temp_person_id;




ALTER TABLE individual ADD COLUMN temp_person_id bigint;
UPDATE individual SET temp_person_id = person_id;

ALTER TABLE individual ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE individual ADD CONSTRAINT individual_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE individual SET person_id = person.id
    FROM person
    WHERE individual.temp_person_id = person.temp_id;

ALTER TABLE individual DROP COLUMN temp_person_id;




ALTER TABLE bill_option ADD COLUMN temp_bank_account_id bigint;
UPDATE bill_option SET temp_bank_account_id = bank_account_id;

ALTER TABLE bill_option ALTER COLUMN bank_account_id TYPE uuid USING NULL;

ALTER TABLE bill_option ADD CONSTRAINT bill_option_bank_account_id_fkey FOREIGN KEY (bank_account_id) REFERENCES bank_account (id) ON UPDATE CASCADE;

UPDATE bill_option SET bank_account_id = bank_account.id
    FROM bank_account
    WHERE bill_option.temp_bank_account_id = bank_account.temp_id;

ALTER TABLE bill_option DROP COLUMN temp_bank_account_id;




ALTER TABLE employee ADD COLUMN temp_role_id bigint;
UPDATE employee SET temp_role_id = role_id;

ALTER TABLE employee ALTER COLUMN role_id TYPE uuid USING NULL;

ALTER TABLE employee ADD CONSTRAINT employee_role_id_fkey FOREIGN KEY (role_id) REFERENCES employee_role (id) ON UPDATE CASCADE;

UPDATE employee SET role_id = employee_role.id
    FROM employee_role
    WHERE employee.temp_role_id = employee_role.temp_id;

ALTER TABLE employee DROP COLUMN temp_role_id;




ALTER TABLE employee ADD COLUMN temp_workpermit_data_id bigint;
UPDATE employee SET temp_workpermit_data_id = workpermit_data_id;

ALTER TABLE employee ALTER COLUMN workpermit_data_id TYPE uuid USING NULL;

ALTER TABLE employee ADD CONSTRAINT employee_workpermit_data_id_fkey FOREIGN KEY (workpermit_data_id) REFERENCES work_permit_data (id) ON UPDATE CASCADE;

UPDATE employee SET workpermit_data_id = work_permit_data.id
    FROM work_permit_data
    WHERE employee.temp_workpermit_data_id = work_permit_data.temp_id;

ALTER TABLE employee DROP COLUMN temp_workpermit_data_id;




ALTER TABLE employee ADD COLUMN temp_military_data_id bigint;
UPDATE employee SET temp_military_data_id = military_data_id;

ALTER TABLE employee ALTER COLUMN military_data_id TYPE uuid USING NULL;

ALTER TABLE employee ADD CONSTRAINT employee_military_data_id_fkey FOREIGN KEY (military_data_id) REFERENCES military_data (id) ON UPDATE CASCADE;

UPDATE employee SET military_data_id = military_data.id
    FROM military_data
    WHERE employee.temp_military_data_id = military_data.temp_id;

ALTER TABLE employee DROP COLUMN temp_military_data_id;




ALTER TABLE employee ADD COLUMN temp_voter_data_id bigint;
UPDATE employee SET temp_voter_data_id = voter_data_id;

ALTER TABLE employee ALTER COLUMN voter_data_id TYPE uuid USING NULL;

ALTER TABLE employee ADD CONSTRAINT employee_voter_data_id_fkey FOREIGN KEY (voter_data_id) REFERENCES voter_data (id) ON UPDATE CASCADE;

UPDATE employee SET voter_data_id = voter_data.id
    FROM voter_data
    WHERE employee.temp_voter_data_id = voter_data.temp_id;

ALTER TABLE employee DROP COLUMN temp_voter_data_id;




ALTER TABLE employee ADD COLUMN temp_bank_account_id bigint;
UPDATE employee SET temp_bank_account_id = bank_account_id;

ALTER TABLE employee ALTER COLUMN bank_account_id TYPE uuid USING NULL;

ALTER TABLE employee ADD CONSTRAINT employee_bank_account_id_fkey FOREIGN KEY (bank_account_id) REFERENCES bank_account (id) ON UPDATE CASCADE;

UPDATE employee SET bank_account_id = bank_account.id
    FROM bank_account
    WHERE employee.temp_bank_account_id = bank_account.temp_id;

ALTER TABLE employee DROP COLUMN temp_bank_account_id;




ALTER TABLE employee ADD COLUMN temp_person_id bigint;
UPDATE employee SET temp_person_id = person_id;

ALTER TABLE employee ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE employee ADD CONSTRAINT employee_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE employee SET person_id = person.id
    FROM person
    WHERE employee.temp_person_id = person.temp_id;

ALTER TABLE employee DROP COLUMN temp_person_id;




ALTER TABLE branch ADD COLUMN temp_manager_id bigint;
UPDATE branch SET temp_manager_id = manager_id;

ALTER TABLE branch ALTER COLUMN manager_id TYPE uuid USING NULL;

ALTER TABLE branch ADD CONSTRAINT branch_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES employee (id) ON UPDATE CASCADE;

UPDATE branch SET manager_id = employee.id
    FROM employee
    WHERE branch.temp_manager_id = employee.temp_id;

ALTER TABLE branch DROP COLUMN temp_manager_id;




ALTER TABLE branch ADD COLUMN temp_person_id bigint;
UPDATE branch SET temp_person_id = person_id;

ALTER TABLE branch ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE branch ADD CONSTRAINT branch_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE branch SET person_id = person.id
    FROM person
    WHERE branch.temp_person_id = person.temp_id;

ALTER TABLE branch DROP COLUMN temp_person_id;




ALTER TABLE employee ADD COLUMN temp_branch_id bigint;
UPDATE employee SET temp_branch_id = branch_id;

ALTER TABLE employee ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE employee ADD CONSTRAINT employee_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE employee SET branch_id = branch.id
    FROM branch
    WHERE employee.temp_branch_id = branch.temp_id;

ALTER TABLE employee DROP COLUMN temp_branch_id;




ALTER TABLE sales_person ADD COLUMN temp_person_id bigint;
UPDATE sales_person SET temp_person_id = person_id;

ALTER TABLE sales_person ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE sales_person ADD CONSTRAINT sales_person_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE sales_person SET person_id = person.id
    FROM person
    WHERE sales_person.temp_person_id = person.temp_id;

ALTER TABLE sales_person DROP COLUMN temp_person_id;




ALTER TABLE supplier ADD COLUMN temp_person_id bigint;
UPDATE supplier SET temp_person_id = person_id;

ALTER TABLE supplier ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE supplier ADD CONSTRAINT supplier_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE supplier SET person_id = person.id
    FROM person
    WHERE supplier.temp_person_id = person.temp_id;

ALTER TABLE supplier DROP COLUMN temp_person_id;




ALTER TABLE transporter ADD COLUMN temp_person_id bigint;
UPDATE transporter SET temp_person_id = person_id;

ALTER TABLE transporter ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE transporter ADD CONSTRAINT transporter_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE transporter SET person_id = person.id
    FROM person
    WHERE transporter.temp_person_id = person.temp_id;

ALTER TABLE transporter DROP COLUMN temp_person_id;




ALTER TABLE login_user ADD COLUMN temp_profile_id bigint;
UPDATE login_user SET temp_profile_id = profile_id;

ALTER TABLE login_user ALTER COLUMN profile_id TYPE uuid USING NULL;

ALTER TABLE login_user ADD CONSTRAINT login_user_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES user_profile (id) ON UPDATE CASCADE;

UPDATE login_user SET profile_id = user_profile.id
    FROM user_profile
    WHERE login_user.temp_profile_id = user_profile.temp_id;

ALTER TABLE login_user DROP COLUMN temp_profile_id;




ALTER TABLE login_user ADD COLUMN temp_person_id bigint;
UPDATE login_user SET temp_person_id = person_id;

ALTER TABLE login_user ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE login_user ADD CONSTRAINT login_user_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE login_user SET person_id = person.id
    FROM person
    WHERE login_user.temp_person_id = person.temp_id;

ALTER TABLE login_user DROP COLUMN temp_person_id;




ALTER TABLE user_branch_access ADD COLUMN temp_user_id bigint;
UPDATE user_branch_access SET temp_user_id = user_id;

ALTER TABLE user_branch_access ALTER COLUMN user_id TYPE uuid USING NULL;

ALTER TABLE user_branch_access ADD CONSTRAINT user_branch_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE user_branch_access SET user_id = login_user.id
    FROM login_user
    WHERE user_branch_access.temp_user_id = login_user.temp_id;

ALTER TABLE user_branch_access DROP COLUMN temp_user_id;




ALTER TABLE user_branch_access ADD COLUMN temp_branch_id bigint;
UPDATE user_branch_access SET temp_branch_id = branch_id;

ALTER TABLE user_branch_access ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE user_branch_access ADD CONSTRAINT user_branch_access_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE user_branch_access SET branch_id = branch.id
    FROM branch
    WHERE user_branch_access.temp_branch_id = branch.temp_id;

ALTER TABLE user_branch_access DROP COLUMN temp_branch_id;




ALTER TABLE client_salary_history ADD COLUMN temp_user_id bigint;
UPDATE client_salary_history SET temp_user_id = user_id;

ALTER TABLE client_salary_history ALTER COLUMN user_id TYPE uuid USING NULL;

ALTER TABLE client_salary_history ADD CONSTRAINT client_salary_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE client_salary_history SET user_id = login_user.id
    FROM login_user
    WHERE client_salary_history.temp_user_id = login_user.temp_id;

ALTER TABLE client_salary_history DROP COLUMN temp_user_id;




ALTER TABLE client_salary_history ADD COLUMN temp_client_id bigint;
UPDATE client_salary_history SET temp_client_id = client_id;

ALTER TABLE client_salary_history ALTER COLUMN client_id TYPE uuid USING NULL;

ALTER TABLE client_salary_history ADD CONSTRAINT client_salary_history_client_id_fkey FOREIGN KEY (client_id) REFERENCES client (id) ON UPDATE CASCADE;

UPDATE client_salary_history SET client_id = client.id
    FROM client
    WHERE client_salary_history.temp_client_id = client.temp_id;

ALTER TABLE client_salary_history DROP COLUMN temp_client_id;




ALTER TABLE sellable_category ADD COLUMN temp_category_id bigint;
UPDATE sellable_category SET temp_category_id = category_id;

ALTER TABLE sellable_category ALTER COLUMN category_id TYPE uuid USING NULL;

ALTER TABLE sellable_category ADD CONSTRAINT sellable_category_category_id_fkey FOREIGN KEY (category_id) REFERENCES sellable_category (id) ON UPDATE CASCADE;

UPDATE sellable_category SET category_id = sellable_category.id
    WHERE sellable_category.temp_category_id = sellable_category.temp_id;

ALTER TABLE sellable_category DROP COLUMN temp_category_id;




ALTER TABLE sellable_category ADD COLUMN temp_tax_constant_id bigint;
UPDATE sellable_category SET temp_tax_constant_id = tax_constant_id;

ALTER TABLE sellable_category ALTER COLUMN tax_constant_id TYPE uuid USING NULL;

ALTER TABLE sellable_category ADD CONSTRAINT sellable_category_tax_constant_id_fkey FOREIGN KEY (tax_constant_id) REFERENCES sellable_tax_constant (id) ON UPDATE CASCADE;

UPDATE sellable_category SET tax_constant_id = sellable_tax_constant.id
    FROM sellable_tax_constant
    WHERE sellable_category.temp_tax_constant_id = sellable_tax_constant.temp_id;

ALTER TABLE sellable_category DROP COLUMN temp_tax_constant_id;




ALTER TABLE product_ipi_template ADD COLUMN temp_product_tax_template_id bigint;
UPDATE product_ipi_template SET temp_product_tax_template_id = product_tax_template_id;

ALTER TABLE product_ipi_template ALTER COLUMN product_tax_template_id TYPE uuid USING NULL;

ALTER TABLE product_ipi_template ADD CONSTRAINT product_ipi_template_product_tax_template_id_fkey FOREIGN KEY (product_tax_template_id) REFERENCES product_tax_template (id) ON UPDATE CASCADE;

UPDATE product_ipi_template SET product_tax_template_id = product_tax_template.id
    FROM product_tax_template
    WHERE product_ipi_template.temp_product_tax_template_id = product_tax_template.temp_id;

ALTER TABLE product_ipi_template DROP COLUMN temp_product_tax_template_id;




ALTER TABLE sellable ADD COLUMN temp_image_id bigint;
UPDATE sellable SET temp_image_id = image_id;

ALTER TABLE sellable ALTER COLUMN image_id TYPE uuid USING NULL;

ALTER TABLE sellable ADD CONSTRAINT sellable_image_id_fkey FOREIGN KEY (image_id) REFERENCES image (id) ON UPDATE CASCADE;

UPDATE sellable SET image_id = image.id
    FROM image
    WHERE sellable.temp_image_id = image.temp_id;

ALTER TABLE sellable DROP COLUMN temp_image_id;




ALTER TABLE sellable ADD COLUMN temp_unit_id bigint;
UPDATE sellable SET temp_unit_id = unit_id;

ALTER TABLE sellable ALTER COLUMN unit_id TYPE uuid USING NULL;

ALTER TABLE sellable ADD CONSTRAINT sellable_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES sellable_unit (id) ON UPDATE CASCADE;

UPDATE sellable SET unit_id = sellable_unit.id
    FROM sellable_unit
    WHERE sellable.temp_unit_id = sellable_unit.temp_id;

ALTER TABLE sellable DROP COLUMN temp_unit_id;




ALTER TABLE sellable ADD COLUMN temp_category_id bigint;
UPDATE sellable SET temp_category_id = category_id;

ALTER TABLE sellable ALTER COLUMN category_id TYPE uuid USING NULL;

ALTER TABLE sellable ADD CONSTRAINT sellable_category_id_fkey FOREIGN KEY (category_id) REFERENCES sellable_category (id) ON UPDATE CASCADE;

UPDATE sellable SET category_id = sellable_category.id
    FROM sellable_category
    WHERE sellable.temp_category_id = sellable_category.temp_id;

ALTER TABLE sellable DROP COLUMN temp_category_id;




ALTER TABLE sellable ADD COLUMN temp_tax_constant_id bigint;
UPDATE sellable SET temp_tax_constant_id = tax_constant_id;

ALTER TABLE sellable ALTER COLUMN tax_constant_id TYPE uuid USING NULL;

ALTER TABLE sellable ADD CONSTRAINT sellable_tax_constant_id_fkey FOREIGN KEY (tax_constant_id) REFERENCES sellable_tax_constant (id) ON UPDATE CASCADE;

UPDATE sellable SET tax_constant_id = sellable_tax_constant.id
    FROM sellable_tax_constant
    WHERE sellable.temp_tax_constant_id = sellable_tax_constant.temp_id;

ALTER TABLE sellable DROP COLUMN temp_tax_constant_id;




ALTER TABLE sellable ADD COLUMN temp_default_sale_cfop_id bigint;
UPDATE sellable SET temp_default_sale_cfop_id = default_sale_cfop_id;

ALTER TABLE sellable ALTER COLUMN default_sale_cfop_id TYPE uuid USING NULL;

ALTER TABLE sellable ADD CONSTRAINT sellable_default_sale_cfop_id_fkey FOREIGN KEY (default_sale_cfop_id) REFERENCES cfop_data (id) ON UPDATE CASCADE;

UPDATE sellable SET default_sale_cfop_id = cfop_data.id
    FROM cfop_data
    WHERE sellable.temp_default_sale_cfop_id = cfop_data.temp_id;

ALTER TABLE sellable DROP COLUMN temp_default_sale_cfop_id;




ALTER TABLE product_icms_template ADD COLUMN temp_product_tax_template_id bigint;
UPDATE product_icms_template SET temp_product_tax_template_id = product_tax_template_id;

ALTER TABLE product_icms_template ALTER COLUMN product_tax_template_id TYPE uuid USING NULL;

ALTER TABLE product_icms_template ADD CONSTRAINT product_icms_template_product_tax_template_id_fkey FOREIGN KEY (product_tax_template_id) REFERENCES product_tax_template (id) ON UPDATE CASCADE;

UPDATE product_icms_template SET product_tax_template_id = product_tax_template.id
    FROM product_tax_template
    WHERE product_icms_template.temp_product_tax_template_id = product_tax_template.temp_id;

ALTER TABLE product_icms_template DROP COLUMN temp_product_tax_template_id;




ALTER TABLE product ADD COLUMN temp_icms_template_id bigint;
UPDATE product SET temp_icms_template_id = icms_template_id;

ALTER TABLE product ALTER COLUMN icms_template_id TYPE uuid USING NULL;

ALTER TABLE product ADD CONSTRAINT product_icms_template_id_fkey FOREIGN KEY (icms_template_id) REFERENCES product_icms_template (id) ON UPDATE CASCADE;

UPDATE product SET icms_template_id = product_icms_template.id
    FROM product_icms_template
    WHERE product.temp_icms_template_id = product_icms_template.temp_id;

ALTER TABLE product DROP COLUMN temp_icms_template_id;




ALTER TABLE product ADD COLUMN temp_ipi_template_id bigint;
UPDATE product SET temp_ipi_template_id = ipi_template_id;

ALTER TABLE product ALTER COLUMN ipi_template_id TYPE uuid USING NULL;

ALTER TABLE product ADD CONSTRAINT product_ipi_template_id_fkey FOREIGN KEY (ipi_template_id) REFERENCES product_ipi_template (id) ON UPDATE CASCADE;

UPDATE product SET ipi_template_id = product_ipi_template.id
    FROM product_ipi_template
    WHERE product.temp_ipi_template_id = product_ipi_template.temp_id;

ALTER TABLE product DROP COLUMN temp_ipi_template_id;




ALTER TABLE product ADD COLUMN temp_manufacturer_id bigint;
UPDATE product SET temp_manufacturer_id = manufacturer_id;

ALTER TABLE product ALTER COLUMN manufacturer_id TYPE uuid USING NULL;

ALTER TABLE product ADD CONSTRAINT product_manufacturer_id_fkey FOREIGN KEY (manufacturer_id) REFERENCES product_manufacturer (id) ON UPDATE CASCADE;

UPDATE product SET manufacturer_id = product_manufacturer.id
    FROM product_manufacturer
    WHERE product.temp_manufacturer_id = product_manufacturer.temp_id;

ALTER TABLE product DROP COLUMN temp_manufacturer_id;




ALTER TABLE product ADD COLUMN temp_sellable_id bigint;
UPDATE product SET temp_sellable_id = sellable_id;

ALTER TABLE product ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE product ADD CONSTRAINT product_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE product SET sellable_id = sellable.id
    FROM sellable
    WHERE product.temp_sellable_id = sellable.temp_id;

ALTER TABLE product DROP COLUMN temp_sellable_id;




ALTER TABLE product_component ADD COLUMN temp_product_id bigint;
UPDATE product_component SET temp_product_id = product_id;

ALTER TABLE product_component ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE product_component ADD CONSTRAINT product_component_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE product_component SET product_id = product.id
    FROM product
    WHERE product_component.temp_product_id = product.temp_id;

ALTER TABLE product_component DROP COLUMN temp_product_id;




ALTER TABLE product_component ADD COLUMN temp_component_id bigint;
UPDATE product_component SET temp_component_id = component_id;

ALTER TABLE product_component ALTER COLUMN component_id TYPE uuid USING NULL;

ALTER TABLE product_component ADD CONSTRAINT product_component_component_id_fkey FOREIGN KEY (component_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE product_component SET component_id = product.id
    FROM product
    WHERE product_component.temp_component_id = product.temp_id;

ALTER TABLE product_component DROP COLUMN temp_component_id;




ALTER TABLE storable ADD COLUMN temp_product_id bigint;
UPDATE storable SET temp_product_id = product_id;

ALTER TABLE storable ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE storable ADD CONSTRAINT storable_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE storable SET product_id = product.id
    FROM product
    WHERE storable.temp_product_id = product.temp_id;

ALTER TABLE storable DROP COLUMN temp_product_id;




ALTER TABLE product_supplier_info ADD COLUMN temp_supplier_id bigint;
UPDATE product_supplier_info SET temp_supplier_id = supplier_id;

ALTER TABLE product_supplier_info ALTER COLUMN supplier_id TYPE uuid USING NULL;

ALTER TABLE product_supplier_info ADD CONSTRAINT product_supplier_info_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES supplier (id) ON UPDATE CASCADE;

UPDATE product_supplier_info SET supplier_id = supplier.id
    FROM supplier
    WHERE product_supplier_info.temp_supplier_id = supplier.temp_id;

ALTER TABLE product_supplier_info DROP COLUMN temp_supplier_id;




ALTER TABLE product_supplier_info ADD COLUMN temp_product_id bigint;
UPDATE product_supplier_info SET temp_product_id = product_id;

ALTER TABLE product_supplier_info ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE product_supplier_info ADD CONSTRAINT product_supplier_info_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE product_supplier_info SET product_id = product.id
    FROM product
    WHERE product_supplier_info.temp_product_id = product.temp_id;

ALTER TABLE product_supplier_info DROP COLUMN temp_product_id;




ALTER TABLE quotation ADD COLUMN temp_purchase_id bigint;
UPDATE quotation SET temp_purchase_id = purchase_id;

ALTER TABLE quotation ALTER COLUMN purchase_id TYPE uuid USING NULL;

ALTER TABLE quotation ADD CONSTRAINT quotation_purchase_id_fkey FOREIGN KEY (purchase_id) REFERENCES purchase_order (id) ON UPDATE CASCADE;

UPDATE quotation SET purchase_id = purchase_order.id
    FROM purchase_order
    WHERE quotation.temp_purchase_id = purchase_order.temp_id;

ALTER TABLE quotation DROP COLUMN temp_purchase_id;




ALTER TABLE product_history ADD COLUMN temp_branch_id bigint;
UPDATE product_history SET temp_branch_id = branch_id;

ALTER TABLE product_history ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE product_history ADD CONSTRAINT product_history_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE product_history SET branch_id = branch.id
    FROM branch
    WHERE product_history.temp_branch_id = branch.temp_id;

ALTER TABLE product_history DROP COLUMN temp_branch_id;




ALTER TABLE product_history ADD COLUMN temp_sellable_id bigint;
UPDATE product_history SET temp_sellable_id = sellable_id;

ALTER TABLE product_history ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE product_history ADD CONSTRAINT product_history_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE product_history SET sellable_id = sellable.id
    FROM sellable
    WHERE product_history.temp_sellable_id = sellable.temp_id;

ALTER TABLE product_history DROP COLUMN temp_sellable_id;




ALTER TABLE service ADD COLUMN temp_sellable_id bigint;
UPDATE service SET temp_sellable_id = sellable_id;

ALTER TABLE service ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE service ADD CONSTRAINT service_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE service SET sellable_id = sellable.id
    FROM sellable
    WHERE service.temp_sellable_id = sellable.temp_id;

ALTER TABLE service DROP COLUMN temp_sellable_id;




ALTER TABLE payment_renegotiation ADD COLUMN temp_client_id bigint;
UPDATE payment_renegotiation SET temp_client_id = client_id;

ALTER TABLE payment_renegotiation ALTER COLUMN client_id TYPE uuid USING NULL;

ALTER TABLE payment_renegotiation ADD CONSTRAINT payment_renegotiation_client_id_fkey FOREIGN KEY (client_id) REFERENCES client (id) ON UPDATE CASCADE;

UPDATE payment_renegotiation SET client_id = client.id
    FROM client
    WHERE payment_renegotiation.temp_client_id = client.temp_id;

ALTER TABLE payment_renegotiation DROP COLUMN temp_client_id;




ALTER TABLE payment_renegotiation ADD COLUMN temp_responsible_id bigint;
UPDATE payment_renegotiation SET temp_responsible_id = responsible_id;

ALTER TABLE payment_renegotiation ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE payment_renegotiation ADD CONSTRAINT payment_renegotiation_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE payment_renegotiation SET responsible_id = login_user.id
    FROM login_user
    WHERE payment_renegotiation.temp_responsible_id = login_user.temp_id;

ALTER TABLE payment_renegotiation DROP COLUMN temp_responsible_id;




ALTER TABLE payment_renegotiation ADD COLUMN temp_branch_id bigint;
UPDATE payment_renegotiation SET temp_branch_id = branch_id;

ALTER TABLE payment_renegotiation ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE payment_renegotiation ADD CONSTRAINT payment_renegotiation_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE payment_renegotiation SET branch_id = branch.id
    FROM branch
    WHERE payment_renegotiation.temp_branch_id = branch.temp_id;

ALTER TABLE payment_renegotiation DROP COLUMN temp_branch_id;




ALTER TABLE payment_group ADD COLUMN temp_payer_id bigint;
UPDATE payment_group SET temp_payer_id = payer_id;

ALTER TABLE payment_group ALTER COLUMN payer_id TYPE uuid USING NULL;

ALTER TABLE payment_group ADD CONSTRAINT payment_group_payer_id_fkey FOREIGN KEY (payer_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE payment_group SET payer_id = person.id
    FROM person
    WHERE payment_group.temp_payer_id = person.temp_id;

ALTER TABLE payment_group DROP COLUMN temp_payer_id;




ALTER TABLE payment_group ADD COLUMN temp_renegotiation_id bigint;
UPDATE payment_group SET temp_renegotiation_id = renegotiation_id;

ALTER TABLE payment_group ALTER COLUMN renegotiation_id TYPE uuid USING NULL;

ALTER TABLE payment_group ADD CONSTRAINT payment_group_renegotiation_id_fkey FOREIGN KEY (renegotiation_id) REFERENCES payment_renegotiation (id) ON UPDATE CASCADE;

UPDATE payment_group SET renegotiation_id = payment_renegotiation.id
    FROM payment_renegotiation
    WHERE payment_group.temp_renegotiation_id = payment_renegotiation.temp_id;

ALTER TABLE payment_group DROP COLUMN temp_renegotiation_id;




ALTER TABLE payment_group ADD COLUMN temp_recipient_id bigint;
UPDATE payment_group SET temp_recipient_id = recipient_id;

ALTER TABLE payment_group ALTER COLUMN recipient_id TYPE uuid USING NULL;

ALTER TABLE payment_group ADD CONSTRAINT payment_group_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE payment_group SET recipient_id = person.id
    FROM person
    WHERE payment_group.temp_recipient_id = person.temp_id;

ALTER TABLE payment_group DROP COLUMN temp_recipient_id;




ALTER TABLE payment_renegotiation ADD COLUMN temp_group_id bigint;
UPDATE payment_renegotiation SET temp_group_id = group_id;

ALTER TABLE payment_renegotiation ALTER COLUMN group_id TYPE uuid USING NULL;

ALTER TABLE payment_renegotiation ADD CONSTRAINT payment_renegotiation_group_id_fkey FOREIGN KEY (group_id) REFERENCES payment_group (id) ON UPDATE CASCADE;

UPDATE payment_renegotiation SET group_id = payment_group.id
    FROM payment_group
    WHERE payment_renegotiation.temp_group_id = payment_group.temp_id;

ALTER TABLE payment_renegotiation DROP COLUMN temp_group_id;




ALTER TABLE quotation ADD COLUMN temp_branch_id bigint;
UPDATE quotation SET temp_branch_id = branch_id;

ALTER TABLE quotation ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE quotation ADD CONSTRAINT quotation_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE quotation SET branch_id = branch.id
    FROM branch
    WHERE quotation.temp_branch_id = branch.temp_id;

ALTER TABLE quotation DROP COLUMN temp_branch_id;




ALTER TABLE purchase_order ADD COLUMN temp_supplier_id bigint;
UPDATE purchase_order SET temp_supplier_id = supplier_id;

ALTER TABLE purchase_order ALTER COLUMN supplier_id TYPE uuid USING NULL;

ALTER TABLE purchase_order ADD CONSTRAINT purchase_order_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES supplier (id) ON UPDATE CASCADE;

UPDATE purchase_order SET supplier_id = supplier.id
    FROM supplier
    WHERE purchase_order.temp_supplier_id = supplier.temp_id;

ALTER TABLE purchase_order DROP COLUMN temp_supplier_id;




ALTER TABLE purchase_order ADD COLUMN temp_branch_id bigint;
UPDATE purchase_order SET temp_branch_id = branch_id;

ALTER TABLE purchase_order ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE purchase_order ADD CONSTRAINT purchase_order_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE purchase_order SET branch_id = branch.id
    FROM branch
    WHERE purchase_order.temp_branch_id = branch.temp_id;

ALTER TABLE purchase_order DROP COLUMN temp_branch_id;




ALTER TABLE purchase_order ADD COLUMN temp_transporter_id bigint;
UPDATE purchase_order SET temp_transporter_id = transporter_id;

ALTER TABLE purchase_order ALTER COLUMN transporter_id TYPE uuid USING NULL;

ALTER TABLE purchase_order ADD CONSTRAINT purchase_order_transporter_id_fkey FOREIGN KEY (transporter_id) REFERENCES transporter (id) ON UPDATE CASCADE;

UPDATE purchase_order SET transporter_id = transporter.id
    FROM transporter
    WHERE purchase_order.temp_transporter_id = transporter.temp_id;

ALTER TABLE purchase_order DROP COLUMN temp_transporter_id;




ALTER TABLE purchase_order ADD COLUMN temp_responsible_id bigint;
UPDATE purchase_order SET temp_responsible_id = responsible_id;

ALTER TABLE purchase_order ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE purchase_order ADD CONSTRAINT purchase_order_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE purchase_order SET responsible_id = login_user.id
    FROM login_user
    WHERE purchase_order.temp_responsible_id = login_user.temp_id;

ALTER TABLE purchase_order DROP COLUMN temp_responsible_id;




ALTER TABLE purchase_order ADD COLUMN temp_group_id bigint;
UPDATE purchase_order SET temp_group_id = group_id;

ALTER TABLE purchase_order ALTER COLUMN group_id TYPE uuid USING NULL;

ALTER TABLE purchase_order ADD CONSTRAINT purchase_order_group_id_fkey FOREIGN KEY (group_id) REFERENCES payment_group (id) ON UPDATE CASCADE;

UPDATE purchase_order SET group_id = payment_group.id
    FROM payment_group
    WHERE purchase_order.temp_group_id = payment_group.temp_id;

ALTER TABLE purchase_order DROP COLUMN temp_group_id;




ALTER TABLE purchase_item ADD COLUMN temp_sellable_id bigint;
UPDATE purchase_item SET temp_sellable_id = sellable_id;

ALTER TABLE purchase_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE purchase_item ADD CONSTRAINT purchase_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE purchase_item SET sellable_id = sellable.id
    FROM sellable
    WHERE purchase_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE purchase_item DROP COLUMN temp_sellable_id;




ALTER TABLE purchase_item ADD COLUMN temp_order_id bigint;
UPDATE purchase_item SET temp_order_id = order_id;

ALTER TABLE purchase_item ALTER COLUMN order_id TYPE uuid USING NULL;

ALTER TABLE purchase_item ADD CONSTRAINT purchase_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES purchase_order (id) ON UPDATE CASCADE;

UPDATE purchase_item SET order_id = purchase_order.id
    FROM purchase_order
    WHERE purchase_item.temp_order_id = purchase_order.temp_id;

ALTER TABLE purchase_item DROP COLUMN temp_order_id;




ALTER TABLE quote_group ADD COLUMN temp_branch_id bigint;
UPDATE quote_group SET temp_branch_id = branch_id;

ALTER TABLE quote_group ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE quote_group ADD CONSTRAINT quote_group_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE quote_group SET branch_id = branch.id
    FROM branch
    WHERE quote_group.temp_branch_id = branch.temp_id;

ALTER TABLE quote_group DROP COLUMN temp_branch_id;




ALTER TABLE quotation ADD COLUMN temp_group_id bigint;
UPDATE quotation SET temp_group_id = group_id;

ALTER TABLE quotation ALTER COLUMN group_id TYPE uuid USING NULL;

ALTER TABLE quotation ADD CONSTRAINT quotation_group_id_fkey FOREIGN KEY (group_id) REFERENCES quote_group (id) ON UPDATE CASCADE;

UPDATE quotation SET group_id = quote_group.id
    FROM quote_group
    WHERE quotation.temp_group_id = quote_group.temp_id;

ALTER TABLE quotation DROP COLUMN temp_group_id;




ALTER TABLE branch_station ADD COLUMN temp_branch_id bigint;
UPDATE branch_station SET temp_branch_id = branch_id;

ALTER TABLE branch_station ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE branch_station ADD CONSTRAINT branch_station_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE branch_station SET branch_id = branch.id
    FROM branch
    WHERE branch_station.temp_branch_id = branch.temp_id;

ALTER TABLE branch_station DROP COLUMN temp_branch_id;




ALTER TABLE till ADD COLUMN temp_station_id bigint;
UPDATE till SET temp_station_id = station_id;

ALTER TABLE till ALTER COLUMN station_id TYPE uuid USING NULL;

ALTER TABLE till ADD CONSTRAINT till_station_id_fkey FOREIGN KEY (station_id) REFERENCES branch_station (id) ON UPDATE CASCADE;

UPDATE till SET station_id = branch_station.id
    FROM branch_station
    WHERE till.temp_station_id = branch_station.temp_id;

ALTER TABLE till DROP COLUMN temp_station_id;




ALTER TABLE client_category_price ADD COLUMN temp_sellable_id bigint;
UPDATE client_category_price SET temp_sellable_id = sellable_id;

ALTER TABLE client_category_price ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE client_category_price ADD CONSTRAINT client_category_price_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE client_category_price SET sellable_id = sellable.id
    FROM sellable
    WHERE client_category_price.temp_sellable_id = sellable.temp_id;

ALTER TABLE client_category_price DROP COLUMN temp_sellable_id;




ALTER TABLE client_category_price ADD COLUMN temp_category_id bigint;
UPDATE client_category_price SET temp_category_id = category_id;

ALTER TABLE client_category_price ALTER COLUMN category_id TYPE uuid USING NULL;

ALTER TABLE client_category_price ADD CONSTRAINT client_category_price_category_id_fkey FOREIGN KEY (category_id) REFERENCES client_category (id) ON UPDATE CASCADE;

UPDATE client_category_price SET category_id = client_category.id
    FROM client_category
    WHERE client_category_price.temp_category_id = client_category.temp_id;

ALTER TABLE client_category_price DROP COLUMN temp_category_id;




ALTER TABLE sale ADD COLUMN temp_client_id bigint;
UPDATE sale SET temp_client_id = client_id;

ALTER TABLE sale ALTER COLUMN client_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_client_id_fkey FOREIGN KEY (client_id) REFERENCES client (id) ON UPDATE CASCADE;

UPDATE sale SET client_id = client.id
    FROM client
    WHERE sale.temp_client_id = client.temp_id;

ALTER TABLE sale DROP COLUMN temp_client_id;




ALTER TABLE sale ADD COLUMN temp_client_category_id bigint;
UPDATE sale SET temp_client_category_id = client_category_id;

ALTER TABLE sale ALTER COLUMN client_category_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_client_category_id_fkey FOREIGN KEY (client_category_id) REFERENCES client_category (id) ON UPDATE CASCADE;

UPDATE sale SET client_category_id = client_category.id
    FROM client_category
    WHERE sale.temp_client_category_id = client_category.temp_id;

ALTER TABLE sale DROP COLUMN temp_client_category_id;




ALTER TABLE sale ADD COLUMN temp_cfop_id bigint;
UPDATE sale SET temp_cfop_id = cfop_id;

ALTER TABLE sale ALTER COLUMN cfop_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_cfop_id_fkey FOREIGN KEY (cfop_id) REFERENCES cfop_data (id) ON UPDATE CASCADE;

UPDATE sale SET cfop_id = cfop_data.id
    FROM cfop_data
    WHERE sale.temp_cfop_id = cfop_data.temp_id;

ALTER TABLE sale DROP COLUMN temp_cfop_id;




ALTER TABLE sale ADD COLUMN temp_salesperson_id bigint;
UPDATE sale SET temp_salesperson_id = salesperson_id;

ALTER TABLE sale ALTER COLUMN salesperson_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_salesperson_id_fkey FOREIGN KEY (salesperson_id) REFERENCES sales_person (id) ON UPDATE CASCADE;

UPDATE sale SET salesperson_id = sales_person.id
    FROM sales_person
    WHERE sale.temp_salesperson_id = sales_person.temp_id;

ALTER TABLE sale DROP COLUMN temp_salesperson_id;




ALTER TABLE sale ADD COLUMN temp_branch_id bigint;
UPDATE sale SET temp_branch_id = branch_id;

ALTER TABLE sale ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE sale SET branch_id = branch.id
    FROM branch
    WHERE sale.temp_branch_id = branch.temp_id;

ALTER TABLE sale DROP COLUMN temp_branch_id;




ALTER TABLE sale ADD COLUMN temp_group_id bigint;
UPDATE sale SET temp_group_id = group_id;

ALTER TABLE sale ALTER COLUMN group_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_group_id_fkey FOREIGN KEY (group_id) REFERENCES payment_group (id) ON UPDATE CASCADE;

UPDATE sale SET group_id = payment_group.id
    FROM payment_group
    WHERE sale.temp_group_id = payment_group.temp_id;

ALTER TABLE sale DROP COLUMN temp_group_id;




ALTER TABLE sale ADD COLUMN temp_transporter_id bigint;
UPDATE sale SET temp_transporter_id = transporter_id;

ALTER TABLE sale ALTER COLUMN transporter_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_transporter_id_fkey FOREIGN KEY (transporter_id) REFERENCES transporter (id) ON UPDATE CASCADE;

UPDATE sale SET transporter_id = transporter.id
    FROM transporter
    WHERE sale.temp_transporter_id = transporter.temp_id;

ALTER TABLE sale DROP COLUMN temp_transporter_id;




ALTER TABLE sale_item ADD COLUMN temp_sale_id bigint;
UPDATE sale_item SET temp_sale_id = sale_id;

ALTER TABLE sale_item ALTER COLUMN sale_id TYPE uuid USING NULL;

ALTER TABLE sale_item ADD CONSTRAINT sale_item_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sale (id) ON UPDATE CASCADE;

UPDATE sale_item SET sale_id = sale.id
    FROM sale
    WHERE sale_item.temp_sale_id = sale.temp_id;

ALTER TABLE sale_item DROP COLUMN temp_sale_id;




ALTER TABLE sale_item ADD COLUMN temp_sellable_id bigint;
UPDATE sale_item SET temp_sellable_id = sellable_id;

ALTER TABLE sale_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE sale_item ADD CONSTRAINT sale_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE sale_item SET sellable_id = sellable.id
    FROM sellable
    WHERE sale_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE sale_item DROP COLUMN temp_sellable_id;




ALTER TABLE sale_item ADD COLUMN temp_icms_info_id bigint;
UPDATE sale_item SET temp_icms_info_id = icms_info_id;

ALTER TABLE sale_item ALTER COLUMN icms_info_id TYPE uuid USING NULL;

ALTER TABLE sale_item ADD CONSTRAINT sale_item_icms_info_id_fkey FOREIGN KEY (icms_info_id) REFERENCES sale_item_icms (id) ON UPDATE CASCADE;

UPDATE sale_item SET icms_info_id = sale_item_icms.id
    FROM sale_item_icms
    WHERE sale_item.temp_icms_info_id = sale_item_icms.temp_id;

ALTER TABLE sale_item DROP COLUMN temp_icms_info_id;




ALTER TABLE sale_item ADD COLUMN temp_ipi_info_id bigint;
UPDATE sale_item SET temp_ipi_info_id = ipi_info_id;

ALTER TABLE sale_item ALTER COLUMN ipi_info_id TYPE uuid USING NULL;

ALTER TABLE sale_item ADD CONSTRAINT sale_item_ipi_info_id_fkey FOREIGN KEY (ipi_info_id) REFERENCES sale_item_ipi (id) ON UPDATE CASCADE;

UPDATE sale_item SET ipi_info_id = sale_item_ipi.id
    FROM sale_item_ipi
    WHERE sale_item.temp_ipi_info_id = sale_item_ipi.temp_id;

ALTER TABLE sale_item DROP COLUMN temp_ipi_info_id;




ALTER TABLE sale_item ADD COLUMN temp_cfop_id bigint;
UPDATE sale_item SET temp_cfop_id = cfop_id;

ALTER TABLE sale_item ALTER COLUMN cfop_id TYPE uuid USING NULL;

ALTER TABLE sale_item ADD CONSTRAINT sale_item_cfop_id_fkey FOREIGN KEY (cfop_id) REFERENCES cfop_data (id) ON UPDATE CASCADE;

UPDATE sale_item SET cfop_id = cfop_data.id
    FROM cfop_data
    WHERE sale_item.temp_cfop_id = cfop_data.temp_id;

ALTER TABLE sale_item DROP COLUMN temp_cfop_id;




ALTER TABLE returned_sale ADD COLUMN temp_responsible_id bigint;
UPDATE returned_sale SET temp_responsible_id = responsible_id;

ALTER TABLE returned_sale ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE returned_sale ADD CONSTRAINT returned_sale_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE returned_sale SET responsible_id = login_user.id
    FROM login_user
    WHERE returned_sale.temp_responsible_id = login_user.temp_id;

ALTER TABLE returned_sale DROP COLUMN temp_responsible_id;




ALTER TABLE returned_sale ADD COLUMN temp_branch_id bigint;
UPDATE returned_sale SET temp_branch_id = branch_id;

ALTER TABLE returned_sale ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE returned_sale ADD CONSTRAINT returned_sale_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE returned_sale SET branch_id = branch.id
    FROM branch
    WHERE returned_sale.temp_branch_id = branch.temp_id;

ALTER TABLE returned_sale DROP COLUMN temp_branch_id;




ALTER TABLE returned_sale ADD COLUMN temp_sale_id bigint;
UPDATE returned_sale SET temp_sale_id = sale_id;

ALTER TABLE returned_sale ALTER COLUMN sale_id TYPE uuid USING NULL;

ALTER TABLE returned_sale ADD CONSTRAINT returned_sale_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sale (id) ON UPDATE CASCADE;

UPDATE returned_sale SET sale_id = sale.id
    FROM sale
    WHERE returned_sale.temp_sale_id = sale.temp_id;

ALTER TABLE returned_sale DROP COLUMN temp_sale_id;




ALTER TABLE returned_sale ADD COLUMN temp_new_sale_id bigint;
UPDATE returned_sale SET temp_new_sale_id = new_sale_id;

ALTER TABLE returned_sale ALTER COLUMN new_sale_id TYPE uuid USING NULL;

ALTER TABLE returned_sale ADD CONSTRAINT returned_sale_new_sale_id_fkey FOREIGN KEY (new_sale_id) REFERENCES sale (id) ON UPDATE CASCADE;

UPDATE returned_sale SET new_sale_id = sale.id
    FROM sale
    WHERE returned_sale.temp_new_sale_id = sale.temp_id;

ALTER TABLE returned_sale DROP COLUMN temp_new_sale_id;




ALTER TABLE returned_sale_item ADD COLUMN temp_sellable_id bigint;
UPDATE returned_sale_item SET temp_sellable_id = sellable_id;

ALTER TABLE returned_sale_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE returned_sale_item ADD CONSTRAINT returned_sale_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE returned_sale_item SET sellable_id = sellable.id
    FROM sellable
    WHERE returned_sale_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE returned_sale_item DROP COLUMN temp_sellable_id;




ALTER TABLE returned_sale_item ADD COLUMN temp_sale_item_id bigint;
UPDATE returned_sale_item SET temp_sale_item_id = sale_item_id;

ALTER TABLE returned_sale_item ALTER COLUMN sale_item_id TYPE uuid USING NULL;

ALTER TABLE returned_sale_item ADD CONSTRAINT returned_sale_item_sale_item_id_fkey FOREIGN KEY (sale_item_id) REFERENCES sale_item (id) ON UPDATE CASCADE;

UPDATE returned_sale_item SET sale_item_id = sale_item.id
    FROM sale_item
    WHERE returned_sale_item.temp_sale_item_id = sale_item.temp_id;

ALTER TABLE returned_sale_item DROP COLUMN temp_sale_item_id;




ALTER TABLE returned_sale_item ADD COLUMN temp_returned_sale_id bigint;
UPDATE returned_sale_item SET temp_returned_sale_id = returned_sale_id;

ALTER TABLE returned_sale_item ALTER COLUMN returned_sale_id TYPE uuid USING NULL;

ALTER TABLE returned_sale_item ADD CONSTRAINT returned_sale_item_returned_sale_id_fkey FOREIGN KEY (returned_sale_id) REFERENCES returned_sale (id) ON UPDATE CASCADE;

UPDATE returned_sale_item SET returned_sale_id = returned_sale.id
    FROM returned_sale
    WHERE returned_sale_item.temp_returned_sale_id = returned_sale.temp_id;

ALTER TABLE returned_sale_item DROP COLUMN temp_returned_sale_id;




ALTER TABLE product_stock_item ADD COLUMN temp_storable_id bigint;
UPDATE product_stock_item SET temp_storable_id = storable_id;

ALTER TABLE product_stock_item ALTER COLUMN storable_id TYPE uuid USING NULL;

ALTER TABLE product_stock_item ADD CONSTRAINT product_stock_item_storable_id_fkey FOREIGN KEY (storable_id) REFERENCES storable (id) ON UPDATE CASCADE;

UPDATE product_stock_item SET storable_id = storable.id
    FROM storable
    WHERE product_stock_item.temp_storable_id = storable.temp_id;

ALTER TABLE product_stock_item DROP COLUMN temp_storable_id;




ALTER TABLE product_stock_item ADD COLUMN temp_branch_id bigint;
UPDATE product_stock_item SET temp_branch_id = branch_id;

ALTER TABLE product_stock_item ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE product_stock_item ADD CONSTRAINT product_stock_item_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE product_stock_item SET branch_id = branch.id
    FROM branch
    WHERE product_stock_item.temp_branch_id = branch.temp_id;

ALTER TABLE product_stock_item DROP COLUMN temp_branch_id;




ALTER TABLE address ADD COLUMN temp_person_id bigint;
UPDATE address SET temp_person_id = person_id;

ALTER TABLE address ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE address ADD CONSTRAINT address_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE address SET person_id = person.id
    FROM person
    WHERE address.temp_person_id = person.temp_id;

ALTER TABLE address DROP COLUMN temp_person_id;




ALTER TABLE delivery ADD COLUMN temp_address_id bigint;
UPDATE delivery SET temp_address_id = address_id;

ALTER TABLE delivery ALTER COLUMN address_id TYPE uuid USING NULL;

ALTER TABLE delivery ADD CONSTRAINT delivery_address_id_fkey FOREIGN KEY (address_id) REFERENCES address (id) ON UPDATE CASCADE;

UPDATE delivery SET address_id = address.id
    FROM address
    WHERE delivery.temp_address_id = address.temp_id;

ALTER TABLE delivery DROP COLUMN temp_address_id;




ALTER TABLE delivery ADD COLUMN temp_transporter_id bigint;
UPDATE delivery SET temp_transporter_id = transporter_id;

ALTER TABLE delivery ALTER COLUMN transporter_id TYPE uuid USING NULL;

ALTER TABLE delivery ADD CONSTRAINT delivery_transporter_id_fkey FOREIGN KEY (transporter_id) REFERENCES transporter (id) ON UPDATE CASCADE;

UPDATE delivery SET transporter_id = transporter.id
    FROM transporter
    WHERE delivery.temp_transporter_id = transporter.temp_id;

ALTER TABLE delivery DROP COLUMN temp_transporter_id;




ALTER TABLE delivery ADD COLUMN temp_service_item_id bigint;
UPDATE delivery SET temp_service_item_id = service_item_id;

ALTER TABLE delivery ALTER COLUMN service_item_id TYPE uuid USING NULL;

ALTER TABLE delivery ADD CONSTRAINT delivery_service_item_id_fkey FOREIGN KEY (service_item_id) REFERENCES sale_item (id) ON UPDATE CASCADE;

UPDATE delivery SET service_item_id = sale_item.id
    FROM sale_item
    WHERE delivery.temp_service_item_id = sale_item.temp_id;

ALTER TABLE delivery DROP COLUMN temp_service_item_id;




ALTER TABLE sale_item ADD COLUMN temp_delivery_id bigint;
UPDATE sale_item SET temp_delivery_id = delivery_id;

ALTER TABLE sale_item ALTER COLUMN delivery_id TYPE uuid USING NULL;

ALTER TABLE sale_item ADD CONSTRAINT sale_item_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES delivery (id) ON UPDATE CASCADE;

UPDATE sale_item SET delivery_id = delivery.id
    FROM delivery
    WHERE sale_item.temp_delivery_id = delivery.temp_id;

ALTER TABLE sale_item DROP COLUMN temp_delivery_id;




ALTER TABLE branch_synchronization ADD COLUMN temp_branch_id bigint;
UPDATE branch_synchronization SET temp_branch_id = branch_id;

ALTER TABLE branch_synchronization ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE branch_synchronization ADD CONSTRAINT branch_synchronization_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE branch_synchronization SET branch_id = branch.id
    FROM branch
    WHERE branch_synchronization.temp_branch_id = branch.temp_id;

ALTER TABLE branch_synchronization DROP COLUMN temp_branch_id;




ALTER TABLE calls ADD COLUMN temp_person_id bigint;
UPDATE calls SET temp_person_id = person_id;

ALTER TABLE calls ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE calls ADD CONSTRAINT calls_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE calls SET person_id = person.id
    FROM person
    WHERE calls.temp_person_id = person.temp_id;

ALTER TABLE calls DROP COLUMN temp_person_id;




ALTER TABLE calls ADD COLUMN temp_attendant_id bigint;
UPDATE calls SET temp_attendant_id = attendant_id;

ALTER TABLE calls ALTER COLUMN attendant_id TYPE uuid USING NULL;

ALTER TABLE calls ADD CONSTRAINT calls_attendant_id_fkey FOREIGN KEY (attendant_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE calls SET attendant_id = login_user.id
    FROM login_user
    WHERE calls.temp_attendant_id = login_user.temp_id;

ALTER TABLE calls DROP COLUMN temp_attendant_id;




ALTER TABLE card_installments_provider_details ADD COLUMN temp_installment_settings_id bigint;
UPDATE card_installments_provider_details SET temp_installment_settings_id = installment_settings_id;

ALTER TABLE card_installments_provider_details ALTER COLUMN installment_settings_id TYPE uuid USING NULL;

ALTER TABLE card_installments_provider_details ADD CONSTRAINT card_installments_provider_details_installment_settings_id_fkey FOREIGN KEY (installment_settings_id) REFERENCES card_installment_settings (id) ON UPDATE CASCADE;

UPDATE card_installments_provider_details SET installment_settings_id = card_installment_settings.id
    FROM card_installment_settings
    WHERE card_installments_provider_details.temp_installment_settings_id = card_installment_settings.temp_id;

ALTER TABLE card_installments_provider_details DROP COLUMN temp_installment_settings_id;




ALTER TABLE card_installments_store_details ADD COLUMN temp_installment_settings_id bigint;
UPDATE card_installments_store_details SET temp_installment_settings_id = installment_settings_id;

ALTER TABLE card_installments_store_details ALTER COLUMN installment_settings_id TYPE uuid USING NULL;

ALTER TABLE card_installments_store_details ADD CONSTRAINT card_installments_store_details_installment_settings_id_fkey FOREIGN KEY (installment_settings_id) REFERENCES card_installment_settings (id) ON UPDATE CASCADE;

UPDATE card_installments_store_details SET installment_settings_id = card_installment_settings.id
    FROM card_installment_settings
    WHERE card_installments_store_details.temp_installment_settings_id = card_installment_settings.temp_id;

ALTER TABLE card_installments_store_details DROP COLUMN temp_installment_settings_id;




ALTER TABLE account ADD COLUMN temp_parent_id bigint;
UPDATE account SET temp_parent_id = parent_id;

ALTER TABLE account ALTER COLUMN parent_id TYPE uuid USING NULL;

ALTER TABLE account ADD CONSTRAINT account_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES account (id) ON UPDATE CASCADE;

UPDATE account SET parent_id = account.id
    WHERE account.temp_parent_id = account.temp_id;

ALTER TABLE account DROP COLUMN temp_parent_id;




ALTER TABLE account ADD COLUMN temp_station_id bigint;
UPDATE account SET temp_station_id = station_id;

ALTER TABLE account ALTER COLUMN station_id TYPE uuid USING NULL;

ALTER TABLE account ADD CONSTRAINT account_station_id_fkey FOREIGN KEY (station_id) REFERENCES branch_station (id) ON UPDATE CASCADE;

UPDATE account SET station_id = branch_station.id
    FROM branch_station
    WHERE account.temp_station_id = branch_station.temp_id;

ALTER TABLE account DROP COLUMN temp_station_id;




ALTER TABLE bank_account ADD COLUMN temp_account_id bigint;
UPDATE bank_account SET temp_account_id = account_id;

ALTER TABLE bank_account ALTER COLUMN account_id TYPE uuid USING NULL;

ALTER TABLE bank_account ADD CONSTRAINT bank_account_account_id_fkey FOREIGN KEY (account_id) REFERENCES account (id) ON UPDATE CASCADE;

UPDATE bank_account SET account_id = account.id
    FROM account
    WHERE bank_account.temp_account_id = account.temp_id;

ALTER TABLE bank_account DROP COLUMN temp_account_id;




ALTER TABLE payment_method ADD COLUMN temp_destination_account_id bigint;
UPDATE payment_method SET temp_destination_account_id = destination_account_id;

ALTER TABLE payment_method ALTER COLUMN destination_account_id TYPE uuid USING NULL;

ALTER TABLE payment_method ADD CONSTRAINT payment_method_destination_account_id_fkey FOREIGN KEY (destination_account_id) REFERENCES account (id) ON UPDATE CASCADE;

UPDATE payment_method SET destination_account_id = account.id
    FROM account
    WHERE payment_method.temp_destination_account_id = account.temp_id;

ALTER TABLE payment_method DROP COLUMN temp_destination_account_id;




ALTER TABLE device_settings ADD COLUMN temp_station_id bigint;
UPDATE device_settings SET temp_station_id = station_id;

ALTER TABLE device_settings ALTER COLUMN station_id TYPE uuid USING NULL;

ALTER TABLE device_settings ADD CONSTRAINT device_settings_station_id_fkey FOREIGN KEY (station_id) REFERENCES branch_station (id) ON UPDATE CASCADE;

UPDATE device_settings SET station_id = branch_station.id
    FROM branch_station
    WHERE device_settings.temp_station_id = branch_station.temp_id;

ALTER TABLE device_settings DROP COLUMN temp_station_id;




ALTER TABLE payment ADD COLUMN temp_method_id bigint;
UPDATE payment SET temp_method_id = method_id;

ALTER TABLE payment ALTER COLUMN method_id TYPE uuid USING NULL;

ALTER TABLE payment ADD CONSTRAINT payment_method_id_fkey FOREIGN KEY (method_id) REFERENCES payment_method (id) ON UPDATE CASCADE;

UPDATE payment SET method_id = payment_method.id
    FROM payment_method
    WHERE payment.temp_method_id = payment_method.temp_id;

ALTER TABLE payment DROP COLUMN temp_method_id;




ALTER TABLE payment ADD COLUMN temp_group_id bigint;
UPDATE payment SET temp_group_id = group_id;

ALTER TABLE payment ALTER COLUMN group_id TYPE uuid USING NULL;

ALTER TABLE payment ADD CONSTRAINT payment_group_id_fkey FOREIGN KEY (group_id) REFERENCES payment_group (id) ON UPDATE CASCADE;

UPDATE payment SET group_id = payment_group.id
    FROM payment_group
    WHERE payment.temp_group_id = payment_group.temp_id;

ALTER TABLE payment DROP COLUMN temp_group_id;




ALTER TABLE payment ADD COLUMN temp_till_id bigint;
UPDATE payment SET temp_till_id = till_id;

ALTER TABLE payment ALTER COLUMN till_id TYPE uuid USING NULL;

ALTER TABLE payment ADD CONSTRAINT payment_till_id_fkey FOREIGN KEY (till_id) REFERENCES till (id) ON UPDATE CASCADE;

UPDATE payment SET till_id = till.id
    FROM till
    WHERE payment.temp_till_id = till.temp_id;

ALTER TABLE payment DROP COLUMN temp_till_id;




ALTER TABLE payment ADD COLUMN temp_branch_id bigint;
UPDATE payment SET temp_branch_id = branch_id;

ALTER TABLE payment ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE payment ADD CONSTRAINT payment_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE payment SET branch_id = branch.id
    FROM branch
    WHERE payment.temp_branch_id = branch.temp_id;

ALTER TABLE payment DROP COLUMN temp_branch_id;




ALTER TABLE payment ADD COLUMN temp_category_id bigint;
UPDATE payment SET temp_category_id = category_id;

ALTER TABLE payment ALTER COLUMN category_id TYPE uuid USING NULL;

ALTER TABLE payment ADD CONSTRAINT payment_category_id_fkey FOREIGN KEY (category_id) REFERENCES payment_category (id) ON UPDATE CASCADE;

UPDATE payment SET category_id = payment_category.id
    FROM payment_category
    WHERE payment.temp_category_id = payment_category.temp_id;

ALTER TABLE payment DROP COLUMN temp_category_id;




ALTER TABLE payment_comment ADD COLUMN temp_payment_id bigint;
UPDATE payment_comment SET temp_payment_id = payment_id;

ALTER TABLE payment_comment ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE payment_comment ADD CONSTRAINT payment_comment_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE payment_comment SET payment_id = payment.id
    FROM payment
    WHERE payment_comment.temp_payment_id = payment.temp_id;

ALTER TABLE payment_comment DROP COLUMN temp_payment_id;




ALTER TABLE payment_comment ADD COLUMN temp_author_id bigint;
UPDATE payment_comment SET temp_author_id = author_id;

ALTER TABLE payment_comment ALTER COLUMN author_id TYPE uuid USING NULL;

ALTER TABLE payment_comment ADD CONSTRAINT payment_comment_author_id_fkey FOREIGN KEY (author_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE payment_comment SET author_id = login_user.id
    FROM login_user
    WHERE payment_comment.temp_author_id = login_user.temp_id;

ALTER TABLE payment_comment DROP COLUMN temp_author_id;




ALTER TABLE check_data ADD COLUMN temp_payment_id bigint;
UPDATE check_data SET temp_payment_id = payment_id;

ALTER TABLE check_data ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE check_data ADD CONSTRAINT check_data_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE check_data SET payment_id = payment.id
    FROM payment
    WHERE check_data.temp_payment_id = payment.temp_id;

ALTER TABLE check_data DROP COLUMN temp_payment_id;




ALTER TABLE check_data ADD COLUMN temp_bank_account_id bigint;
UPDATE check_data SET temp_bank_account_id = bank_account_id;

ALTER TABLE check_data ALTER COLUMN bank_account_id TYPE uuid USING NULL;

ALTER TABLE check_data ADD CONSTRAINT check_data_bank_account_id_fkey FOREIGN KEY (bank_account_id) REFERENCES bank_account (id) ON UPDATE CASCADE;

UPDATE check_data SET bank_account_id = bank_account.id
    FROM bank_account
    WHERE check_data.temp_bank_account_id = bank_account.temp_id;

ALTER TABLE check_data DROP COLUMN temp_bank_account_id;




ALTER TABLE credit_card_details ADD COLUMN temp_installment_settings_id bigint;
UPDATE credit_card_details SET temp_installment_settings_id = installment_settings_id;

ALTER TABLE credit_card_details ALTER COLUMN installment_settings_id TYPE uuid USING NULL;

ALTER TABLE credit_card_details ADD CONSTRAINT credit_card_details_installment_settings_id_fkey FOREIGN KEY (installment_settings_id) REFERENCES card_installment_settings (id) ON UPDATE CASCADE;

UPDATE credit_card_details SET installment_settings_id = card_installment_settings.id
    FROM card_installment_settings
    WHERE credit_card_details.temp_installment_settings_id = card_installment_settings.temp_id;

ALTER TABLE credit_card_details DROP COLUMN temp_installment_settings_id;




ALTER TABLE credit_card_data ADD COLUMN temp_payment_id bigint;
UPDATE credit_card_data SET temp_payment_id = payment_id;

ALTER TABLE credit_card_data ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE credit_card_data ADD CONSTRAINT credit_card_data_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE credit_card_data SET payment_id = payment.id
    FROM payment
    WHERE credit_card_data.temp_payment_id = payment.temp_id;

ALTER TABLE credit_card_data DROP COLUMN temp_payment_id;




ALTER TABLE credit_card_data ADD COLUMN temp_provider_id bigint;
UPDATE credit_card_data SET temp_provider_id = provider_id;

ALTER TABLE credit_card_data ALTER COLUMN provider_id TYPE uuid USING NULL;

ALTER TABLE credit_card_data ADD CONSTRAINT credit_card_data_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES credit_provider (id) ON UPDATE CASCADE;

UPDATE credit_card_data SET provider_id = credit_provider.id
    FROM credit_provider
    WHERE credit_card_data.temp_provider_id = credit_provider.temp_id;

ALTER TABLE credit_card_data DROP COLUMN temp_provider_id;




ALTER TABLE payment_change_history ADD COLUMN temp_payment_id bigint;
UPDATE payment_change_history SET temp_payment_id = payment_id;

ALTER TABLE payment_change_history ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE payment_change_history ADD CONSTRAINT payment_change_history_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE payment_change_history SET payment_id = payment.id
    FROM payment
    WHERE payment_change_history.temp_payment_id = payment.temp_id;

ALTER TABLE payment_change_history DROP COLUMN temp_payment_id;




ALTER TABLE fiscal_sale_history ADD COLUMN temp_sale_id bigint;
UPDATE fiscal_sale_history SET temp_sale_id = sale_id;

ALTER TABLE fiscal_sale_history ALTER COLUMN sale_id TYPE uuid USING NULL;

ALTER TABLE fiscal_sale_history ADD CONSTRAINT fiscal_sale_history_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sale (id) ON UPDATE CASCADE;

UPDATE fiscal_sale_history SET sale_id = sale.id
    FROM sale
    WHERE fiscal_sale_history.temp_sale_id = sale.temp_id;

ALTER TABLE fiscal_sale_history DROP COLUMN temp_sale_id;




ALTER TABLE employee_role_history ADD COLUMN temp_role_id bigint;
UPDATE employee_role_history SET temp_role_id = role_id;

ALTER TABLE employee_role_history ALTER COLUMN role_id TYPE uuid USING NULL;

ALTER TABLE employee_role_history ADD CONSTRAINT employee_role_history_role_id_fkey FOREIGN KEY (role_id) REFERENCES employee_role (id) ON UPDATE CASCADE;

UPDATE employee_role_history SET role_id = employee_role.id
    FROM employee_role
    WHERE employee_role_history.temp_role_id = employee_role.temp_id;

ALTER TABLE employee_role_history DROP COLUMN temp_role_id;




ALTER TABLE employee_role_history ADD COLUMN temp_employee_id bigint;
UPDATE employee_role_history SET temp_employee_id = employee_id;

ALTER TABLE employee_role_history ALTER COLUMN employee_id TYPE uuid USING NULL;

ALTER TABLE employee_role_history ADD CONSTRAINT employee_role_history_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES employee (id) ON UPDATE CASCADE;

UPDATE employee_role_history SET employee_id = employee.id
    FROM employee
    WHERE employee_role_history.temp_employee_id = employee.temp_id;

ALTER TABLE employee_role_history DROP COLUMN temp_employee_id;




ALTER TABLE contact_info ADD COLUMN temp_person_id bigint;
UPDATE contact_info SET temp_person_id = person_id;

ALTER TABLE contact_info ALTER COLUMN person_id TYPE uuid USING NULL;

ALTER TABLE contact_info ADD CONSTRAINT liaison_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE contact_info SET person_id = person.id
    FROM person
    WHERE contact_info.temp_person_id = person.temp_id;

ALTER TABLE contact_info DROP COLUMN temp_person_id;




ALTER TABLE profile_settings ADD COLUMN temp_user_profile_id bigint;
UPDATE profile_settings SET temp_user_profile_id = user_profile_id;

ALTER TABLE profile_settings ALTER COLUMN user_profile_id TYPE uuid USING NULL;

ALTER TABLE profile_settings ADD CONSTRAINT profile_settings_user_profile_id_fkey FOREIGN KEY (user_profile_id) REFERENCES user_profile (id) ON UPDATE CASCADE;

UPDATE profile_settings SET user_profile_id = user_profile.id
    FROM user_profile
    WHERE profile_settings.temp_user_profile_id = user_profile.temp_id;

ALTER TABLE profile_settings DROP COLUMN temp_user_profile_id;




ALTER TABLE receiving_order ADD COLUMN temp_cfop_id bigint;
UPDATE receiving_order SET temp_cfop_id = cfop_id;

ALTER TABLE receiving_order ALTER COLUMN cfop_id TYPE uuid USING NULL;

ALTER TABLE receiving_order ADD CONSTRAINT receiving_order_cfop_id_fkey FOREIGN KEY (cfop_id) REFERENCES cfop_data (id) ON UPDATE CASCADE;

UPDATE receiving_order SET cfop_id = cfop_data.id
    FROM cfop_data
    WHERE receiving_order.temp_cfop_id = cfop_data.temp_id;

ALTER TABLE receiving_order DROP COLUMN temp_cfop_id;




ALTER TABLE receiving_order ADD COLUMN temp_responsible_id bigint;
UPDATE receiving_order SET temp_responsible_id = responsible_id;

ALTER TABLE receiving_order ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE receiving_order ADD CONSTRAINT receiving_order_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE receiving_order SET responsible_id = login_user.id
    FROM login_user
    WHERE receiving_order.temp_responsible_id = login_user.temp_id;

ALTER TABLE receiving_order DROP COLUMN temp_responsible_id;




ALTER TABLE receiving_order ADD COLUMN temp_supplier_id bigint;
UPDATE receiving_order SET temp_supplier_id = supplier_id;

ALTER TABLE receiving_order ALTER COLUMN supplier_id TYPE uuid USING NULL;

ALTER TABLE receiving_order ADD CONSTRAINT receiving_order_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES supplier (id) ON UPDATE CASCADE;

UPDATE receiving_order SET supplier_id = supplier.id
    FROM supplier
    WHERE receiving_order.temp_supplier_id = supplier.temp_id;

ALTER TABLE receiving_order DROP COLUMN temp_supplier_id;




ALTER TABLE receiving_order ADD COLUMN temp_branch_id bigint;
UPDATE receiving_order SET temp_branch_id = branch_id;

ALTER TABLE receiving_order ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE receiving_order ADD CONSTRAINT receiving_order_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE receiving_order SET branch_id = branch.id
    FROM branch
    WHERE receiving_order.temp_branch_id = branch.temp_id;

ALTER TABLE receiving_order DROP COLUMN temp_branch_id;




ALTER TABLE receiving_order ADD COLUMN temp_purchase_id bigint;
UPDATE receiving_order SET temp_purchase_id = purchase_id;

ALTER TABLE receiving_order ALTER COLUMN purchase_id TYPE uuid USING NULL;

ALTER TABLE receiving_order ADD CONSTRAINT receiving_order_purchase_id_fkey FOREIGN KEY (purchase_id) REFERENCES purchase_order (id) ON UPDATE CASCADE;

UPDATE receiving_order SET purchase_id = purchase_order.id
    FROM purchase_order
    WHERE receiving_order.temp_purchase_id = purchase_order.temp_id;

ALTER TABLE receiving_order DROP COLUMN temp_purchase_id;




ALTER TABLE receiving_order ADD COLUMN temp_transporter_id bigint;
UPDATE receiving_order SET temp_transporter_id = transporter_id;

ALTER TABLE receiving_order ALTER COLUMN transporter_id TYPE uuid USING NULL;

ALTER TABLE receiving_order ADD CONSTRAINT receiving_order_transporter_id_fkey FOREIGN KEY (transporter_id) REFERENCES transporter (id) ON UPDATE CASCADE;

UPDATE receiving_order SET transporter_id = transporter.id
    FROM transporter
    WHERE receiving_order.temp_transporter_id = transporter.temp_id;

ALTER TABLE receiving_order DROP COLUMN temp_transporter_id;




ALTER TABLE receiving_order_item ADD COLUMN temp_sellable_id bigint;
UPDATE receiving_order_item SET temp_sellable_id = sellable_id;

ALTER TABLE receiving_order_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE receiving_order_item ADD CONSTRAINT receiving_order_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE receiving_order_item SET sellable_id = sellable.id
    FROM sellable
    WHERE receiving_order_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE receiving_order_item DROP COLUMN temp_sellable_id;




ALTER TABLE receiving_order_item ADD COLUMN temp_receiving_order_id bigint;
UPDATE receiving_order_item SET temp_receiving_order_id = receiving_order_id;

ALTER TABLE receiving_order_item ALTER COLUMN receiving_order_id TYPE uuid USING NULL;

ALTER TABLE receiving_order_item ADD CONSTRAINT receiving_order_item_receiving_order_id_fkey FOREIGN KEY (receiving_order_id) REFERENCES receiving_order (id) ON UPDATE CASCADE;

UPDATE receiving_order_item SET receiving_order_id = receiving_order.id
    FROM receiving_order
    WHERE receiving_order_item.temp_receiving_order_id = receiving_order.temp_id;

ALTER TABLE receiving_order_item DROP COLUMN temp_receiving_order_id;




ALTER TABLE receiving_order_item ADD COLUMN temp_purchase_item_id bigint;
UPDATE receiving_order_item SET temp_purchase_item_id = purchase_item_id;

ALTER TABLE receiving_order_item ALTER COLUMN purchase_item_id TYPE uuid USING NULL;

ALTER TABLE receiving_order_item ADD CONSTRAINT receiving_order_item_purchase_item_id_fkey FOREIGN KEY (purchase_item_id) REFERENCES purchase_item (id) ON UPDATE CASCADE;

UPDATE receiving_order_item SET purchase_item_id = purchase_item.id
    FROM purchase_item
    WHERE receiving_order_item.temp_purchase_item_id = purchase_item.temp_id;

ALTER TABLE receiving_order_item DROP COLUMN temp_purchase_item_id;




ALTER TABLE till_entry ADD COLUMN temp_till_id bigint;
UPDATE till_entry SET temp_till_id = till_id;

ALTER TABLE till_entry ALTER COLUMN till_id TYPE uuid USING NULL;

ALTER TABLE till_entry ADD CONSTRAINT till_entry_till_id_fkey FOREIGN KEY (till_id) REFERENCES till (id) ON UPDATE CASCADE;

UPDATE till_entry SET till_id = till.id
    FROM till
    WHERE till_entry.temp_till_id = till.temp_id;

ALTER TABLE till_entry DROP COLUMN temp_till_id;




ALTER TABLE till_entry ADD COLUMN temp_branch_id bigint;
UPDATE till_entry SET temp_branch_id = branch_id;

ALTER TABLE till_entry ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE till_entry ADD CONSTRAINT till_entry_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE till_entry SET branch_id = branch.id
    FROM branch
    WHERE till_entry.temp_branch_id = branch.temp_id;

ALTER TABLE till_entry DROP COLUMN temp_branch_id;




ALTER TABLE till_entry ADD COLUMN temp_payment_id bigint;
UPDATE till_entry SET temp_payment_id = payment_id;

ALTER TABLE till_entry ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE till_entry ADD CONSTRAINT till_entry_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE till_entry SET payment_id = payment.id
    FROM payment
    WHERE till_entry.temp_payment_id = payment.temp_id;

ALTER TABLE till_entry DROP COLUMN temp_payment_id;




ALTER TABLE fiscal_book_entry ADD COLUMN temp_cfop_id bigint;
UPDATE fiscal_book_entry SET temp_cfop_id = cfop_id;

ALTER TABLE fiscal_book_entry ALTER COLUMN cfop_id TYPE uuid USING NULL;

ALTER TABLE fiscal_book_entry ADD CONSTRAINT fiscal_book_entry_cfop_id_fkey FOREIGN KEY (cfop_id) REFERENCES cfop_data (id) ON UPDATE CASCADE;

UPDATE fiscal_book_entry SET cfop_id = cfop_data.id
    FROM cfop_data
    WHERE fiscal_book_entry.temp_cfop_id = cfop_data.temp_id;

ALTER TABLE fiscal_book_entry DROP COLUMN temp_cfop_id;




ALTER TABLE fiscal_book_entry ADD COLUMN temp_branch_id bigint;
UPDATE fiscal_book_entry SET temp_branch_id = branch_id;

ALTER TABLE fiscal_book_entry ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE fiscal_book_entry ADD CONSTRAINT fiscal_book_entry_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE fiscal_book_entry SET branch_id = branch.id
    FROM branch
    WHERE fiscal_book_entry.temp_branch_id = branch.temp_id;

ALTER TABLE fiscal_book_entry DROP COLUMN temp_branch_id;




ALTER TABLE fiscal_book_entry ADD COLUMN temp_drawee_id bigint;
UPDATE fiscal_book_entry SET temp_drawee_id = drawee_id;

ALTER TABLE fiscal_book_entry ALTER COLUMN drawee_id TYPE uuid USING NULL;

ALTER TABLE fiscal_book_entry ADD CONSTRAINT fiscal_book_entry_drawee_id_fkey FOREIGN KEY (drawee_id) REFERENCES person (id) ON UPDATE CASCADE;

UPDATE fiscal_book_entry SET drawee_id = person.id
    FROM person
    WHERE fiscal_book_entry.temp_drawee_id = person.temp_id;

ALTER TABLE fiscal_book_entry DROP COLUMN temp_drawee_id;




ALTER TABLE fiscal_book_entry ADD COLUMN temp_payment_group_id bigint;
UPDATE fiscal_book_entry SET temp_payment_group_id = payment_group_id;

ALTER TABLE fiscal_book_entry ALTER COLUMN payment_group_id TYPE uuid USING NULL;

ALTER TABLE fiscal_book_entry ADD CONSTRAINT fiscal_book_entry_payment_group_id_fkey FOREIGN KEY (payment_group_id) REFERENCES payment_group (id) ON UPDATE CASCADE;

UPDATE fiscal_book_entry SET payment_group_id = payment_group.id
    FROM payment_group
    WHERE fiscal_book_entry.temp_payment_group_id = payment_group.temp_id;

ALTER TABLE fiscal_book_entry DROP COLUMN temp_payment_group_id;




ALTER TABLE fiscal_day_history ADD COLUMN temp_station_id bigint;
UPDATE fiscal_day_history SET temp_station_id = station_id;

ALTER TABLE fiscal_day_history ALTER COLUMN station_id TYPE uuid USING NULL;

ALTER TABLE fiscal_day_history ADD CONSTRAINT fiscal_day_history_station_id_fkey FOREIGN KEY (station_id) REFERENCES branch_station (id) ON UPDATE CASCADE;

UPDATE fiscal_day_history SET station_id = branch_station.id
    FROM branch_station
    WHERE fiscal_day_history.temp_station_id = branch_station.temp_id;

ALTER TABLE fiscal_day_history DROP COLUMN temp_station_id;




ALTER TABLE fiscal_day_tax ADD COLUMN temp_fiscal_day_history_id bigint;
UPDATE fiscal_day_tax SET temp_fiscal_day_history_id = fiscal_day_history_id;

ALTER TABLE fiscal_day_tax ALTER COLUMN fiscal_day_history_id TYPE uuid USING NULL;

ALTER TABLE fiscal_day_tax ADD CONSTRAINT fiscal_day_tax_fiscal_day_history_id_fkey FOREIGN KEY (fiscal_day_history_id) REFERENCES fiscal_day_history (id) ON UPDATE CASCADE;

UPDATE fiscal_day_tax SET fiscal_day_history_id = fiscal_day_history.id
    FROM fiscal_day_history
    WHERE fiscal_day_tax.temp_fiscal_day_history_id = fiscal_day_history.temp_id;

ALTER TABLE fiscal_day_tax DROP COLUMN temp_fiscal_day_history_id;




ALTER TABLE commission_source ADD COLUMN temp_category_id bigint;
UPDATE commission_source SET temp_category_id = category_id;

ALTER TABLE commission_source ALTER COLUMN category_id TYPE uuid USING NULL;

ALTER TABLE commission_source ADD CONSTRAINT commission_source_category_id_fkey FOREIGN KEY (category_id) REFERENCES sellable_category (id) ON UPDATE CASCADE;

UPDATE commission_source SET category_id = sellable_category.id
    FROM sellable_category
    WHERE commission_source.temp_category_id = sellable_category.temp_id;

ALTER TABLE commission_source DROP COLUMN temp_category_id;




ALTER TABLE commission_source ADD COLUMN temp_sellable_id bigint;
UPDATE commission_source SET temp_sellable_id = sellable_id;

ALTER TABLE commission_source ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE commission_source ADD CONSTRAINT commission_source_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE commission_source SET sellable_id = sellable.id
    FROM sellable
    WHERE commission_source.temp_sellable_id = sellable.temp_id;

ALTER TABLE commission_source DROP COLUMN temp_sellable_id;




ALTER TABLE commission ADD COLUMN temp_salesperson_id bigint;
UPDATE commission SET temp_salesperson_id = salesperson_id;

ALTER TABLE commission ALTER COLUMN salesperson_id TYPE uuid USING NULL;

ALTER TABLE commission ADD CONSTRAINT commission_salesperson_id_fkey FOREIGN KEY (salesperson_id) REFERENCES sales_person (id) ON UPDATE CASCADE;

UPDATE commission SET salesperson_id = sales_person.id
    FROM sales_person
    WHERE commission.temp_salesperson_id = sales_person.temp_id;

ALTER TABLE commission DROP COLUMN temp_salesperson_id;




ALTER TABLE commission ADD COLUMN temp_sale_id bigint;
UPDATE commission SET temp_sale_id = sale_id;

ALTER TABLE commission ALTER COLUMN sale_id TYPE uuid USING NULL;

ALTER TABLE commission ADD CONSTRAINT commission_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sale (id) ON UPDATE CASCADE;

UPDATE commission SET sale_id = sale.id
    FROM sale
    WHERE commission.temp_sale_id = sale.temp_id;

ALTER TABLE commission DROP COLUMN temp_sale_id;




ALTER TABLE commission ADD COLUMN temp_payment_id bigint;
UPDATE commission SET temp_payment_id = payment_id;

ALTER TABLE commission ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE commission ADD CONSTRAINT commission_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE commission SET payment_id = payment.id
    FROM payment
    WHERE commission.temp_payment_id = payment.temp_id;

ALTER TABLE commission DROP COLUMN temp_payment_id;




ALTER TABLE transfer_order ADD COLUMN temp_source_branch_id bigint;
UPDATE transfer_order SET temp_source_branch_id = source_branch_id;

ALTER TABLE transfer_order ALTER COLUMN source_branch_id TYPE uuid USING NULL;

ALTER TABLE transfer_order ADD CONSTRAINT transfer_order_source_branch_id_fkey FOREIGN KEY (source_branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE transfer_order SET source_branch_id = branch.id
    FROM branch
    WHERE transfer_order.temp_source_branch_id = branch.temp_id;

ALTER TABLE transfer_order DROP COLUMN temp_source_branch_id;




ALTER TABLE transfer_order ADD COLUMN temp_destination_branch_id bigint;
UPDATE transfer_order SET temp_destination_branch_id = destination_branch_id;

ALTER TABLE transfer_order ALTER COLUMN destination_branch_id TYPE uuid USING NULL;

ALTER TABLE transfer_order ADD CONSTRAINT transfer_order_destination_branch_id_fkey FOREIGN KEY (destination_branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE transfer_order SET destination_branch_id = branch.id
    FROM branch
    WHERE transfer_order.temp_destination_branch_id = branch.temp_id;

ALTER TABLE transfer_order DROP COLUMN temp_destination_branch_id;




ALTER TABLE transfer_order ADD COLUMN temp_source_responsible_id bigint;
UPDATE transfer_order SET temp_source_responsible_id = source_responsible_id;

ALTER TABLE transfer_order ALTER COLUMN source_responsible_id TYPE uuid USING NULL;

ALTER TABLE transfer_order ADD CONSTRAINT transfer_order_source_responsible_id_fkey FOREIGN KEY (source_responsible_id) REFERENCES employee (id) ON UPDATE CASCADE;

UPDATE transfer_order SET source_responsible_id = employee.id
    FROM employee
    WHERE transfer_order.temp_source_responsible_id = employee.temp_id;

ALTER TABLE transfer_order DROP COLUMN temp_source_responsible_id;




ALTER TABLE transfer_order ADD COLUMN temp_destination_responsible_id bigint;
UPDATE transfer_order SET temp_destination_responsible_id = destination_responsible_id;

ALTER TABLE transfer_order ALTER COLUMN destination_responsible_id TYPE uuid USING NULL;

ALTER TABLE transfer_order ADD CONSTRAINT transfer_order_destination_responsible_id_fkey FOREIGN KEY (destination_responsible_id) REFERENCES employee (id) ON UPDATE CASCADE;

UPDATE transfer_order SET destination_responsible_id = employee.id
    FROM employee
    WHERE transfer_order.temp_destination_responsible_id = employee.temp_id;

ALTER TABLE transfer_order DROP COLUMN temp_destination_responsible_id;




ALTER TABLE transfer_order_item ADD COLUMN temp_sellable_id bigint;
UPDATE transfer_order_item SET temp_sellable_id = sellable_id;

ALTER TABLE transfer_order_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE transfer_order_item ADD CONSTRAINT transfer_order_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE transfer_order_item SET sellable_id = sellable.id
    FROM sellable
    WHERE transfer_order_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE transfer_order_item DROP COLUMN temp_sellable_id;




ALTER TABLE transfer_order_item ADD COLUMN temp_transfer_order_id bigint;
UPDATE transfer_order_item SET temp_transfer_order_id = transfer_order_id;

ALTER TABLE transfer_order_item ALTER COLUMN transfer_order_id TYPE uuid USING NULL;

ALTER TABLE transfer_order_item ADD CONSTRAINT transfer_order_item_transfer_order_id_fkey FOREIGN KEY (transfer_order_id) REFERENCES transfer_order (id) ON UPDATE CASCADE;

UPDATE transfer_order_item SET transfer_order_id = transfer_order.id
    FROM transfer_order
    WHERE transfer_order_item.temp_transfer_order_id = transfer_order.temp_id;

ALTER TABLE transfer_order_item DROP COLUMN temp_transfer_order_id;




ALTER TABLE invoice_field ADD COLUMN temp_layout_id bigint;
UPDATE invoice_field SET temp_layout_id = layout_id;

ALTER TABLE invoice_field ALTER COLUMN layout_id TYPE uuid USING NULL;

ALTER TABLE invoice_field ADD CONSTRAINT invoice_field_layout_id_fkey FOREIGN KEY (layout_id) REFERENCES invoice_layout (id) ON UPDATE CASCADE;

UPDATE invoice_field SET layout_id = invoice_layout.id
    FROM invoice_layout
    WHERE invoice_field.temp_layout_id = invoice_layout.temp_id;

ALTER TABLE invoice_field DROP COLUMN temp_layout_id;




ALTER TABLE invoice_printer ADD COLUMN temp_station_id bigint;
UPDATE invoice_printer SET temp_station_id = station_id;

ALTER TABLE invoice_printer ALTER COLUMN station_id TYPE uuid USING NULL;

ALTER TABLE invoice_printer ADD CONSTRAINT invoice_printer_station_id_fkey FOREIGN KEY (station_id) REFERENCES branch_station (id) ON UPDATE CASCADE;

UPDATE invoice_printer SET station_id = branch_station.id
    FROM branch_station
    WHERE invoice_printer.temp_station_id = branch_station.temp_id;

ALTER TABLE invoice_printer DROP COLUMN temp_station_id;




ALTER TABLE invoice_printer ADD COLUMN temp_layout_id bigint;
UPDATE invoice_printer SET temp_layout_id = layout_id;

ALTER TABLE invoice_printer ALTER COLUMN layout_id TYPE uuid USING NULL;

ALTER TABLE invoice_printer ADD CONSTRAINT invoice_printer_layout_id_fkey FOREIGN KEY (layout_id) REFERENCES invoice_layout (id) ON UPDATE CASCADE;

UPDATE invoice_printer SET layout_id = invoice_layout.id
    FROM invoice_layout
    WHERE invoice_printer.temp_layout_id = invoice_layout.temp_id;

ALTER TABLE invoice_printer DROP COLUMN temp_layout_id;




ALTER TABLE inventory ADD COLUMN temp_branch_id bigint;
UPDATE inventory SET temp_branch_id = branch_id;

ALTER TABLE inventory ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE inventory ADD CONSTRAINT inventory_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE inventory SET branch_id = branch.id
    FROM branch
    WHERE inventory.temp_branch_id = branch.temp_id;

ALTER TABLE inventory DROP COLUMN temp_branch_id;




ALTER TABLE inventory_item ADD COLUMN temp_product_id bigint;
UPDATE inventory_item SET temp_product_id = product_id;

ALTER TABLE inventory_item ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE inventory_item ADD CONSTRAINT inventory_item_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE inventory_item SET product_id = product.id
    FROM product
    WHERE inventory_item.temp_product_id = product.temp_id;

ALTER TABLE inventory_item DROP COLUMN temp_product_id;




ALTER TABLE inventory_item ADD COLUMN temp_inventory_id bigint;
UPDATE inventory_item SET temp_inventory_id = inventory_id;

ALTER TABLE inventory_item ALTER COLUMN inventory_id TYPE uuid USING NULL;

ALTER TABLE inventory_item ADD CONSTRAINT inventory_item_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES inventory (id) ON UPDATE CASCADE;

UPDATE inventory_item SET inventory_id = inventory.id
    FROM inventory
    WHERE inventory_item.temp_inventory_id = inventory.temp_id;

ALTER TABLE inventory_item DROP COLUMN temp_inventory_id;




ALTER TABLE inventory_item ADD COLUMN temp_cfop_data_id bigint;
UPDATE inventory_item SET temp_cfop_data_id = cfop_data_id;

ALTER TABLE inventory_item ALTER COLUMN cfop_data_id TYPE uuid USING NULL;

ALTER TABLE inventory_item ADD CONSTRAINT inventory_item_cfop_data_id_fkey FOREIGN KEY (cfop_data_id) REFERENCES cfop_data (id) ON UPDATE CASCADE;

UPDATE inventory_item SET cfop_data_id = cfop_data.id
    FROM cfop_data
    WHERE inventory_item.temp_cfop_data_id = cfop_data.temp_id;

ALTER TABLE inventory_item DROP COLUMN temp_cfop_data_id;




ALTER TABLE production_order ADD COLUMN temp_responsible_id bigint;
UPDATE production_order SET temp_responsible_id = responsible_id;

ALTER TABLE production_order ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE production_order ADD CONSTRAINT production_order_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES employee (id) ON UPDATE CASCADE;

UPDATE production_order SET responsible_id = employee.id
    FROM employee
    WHERE production_order.temp_responsible_id = employee.temp_id;

ALTER TABLE production_order DROP COLUMN temp_responsible_id;




ALTER TABLE production_order ADD COLUMN temp_branch_id bigint;
UPDATE production_order SET temp_branch_id = branch_id;

ALTER TABLE production_order ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE production_order ADD CONSTRAINT production_order_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE production_order SET branch_id = branch.id
    FROM branch
    WHERE production_order.temp_branch_id = branch.temp_id;

ALTER TABLE production_order DROP COLUMN temp_branch_id;




ALTER TABLE production_item ADD COLUMN temp_product_id bigint;
UPDATE production_item SET temp_product_id = product_id;

ALTER TABLE production_item ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE production_item ADD CONSTRAINT production_item_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE production_item SET product_id = product.id
    FROM product
    WHERE production_item.temp_product_id = product.temp_id;

ALTER TABLE production_item DROP COLUMN temp_product_id;




ALTER TABLE production_item ADD COLUMN temp_order_id bigint;
UPDATE production_item SET temp_order_id = order_id;

ALTER TABLE production_item ALTER COLUMN order_id TYPE uuid USING NULL;

ALTER TABLE production_item ADD CONSTRAINT production_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES production_order (id) ON UPDATE CASCADE;

UPDATE production_item SET order_id = production_order.id
    FROM production_order
    WHERE production_item.temp_order_id = production_order.temp_id;

ALTER TABLE production_item DROP COLUMN temp_order_id;




ALTER TABLE production_material ADD COLUMN temp_order_id bigint;
UPDATE production_material SET temp_order_id = order_id;

ALTER TABLE production_material ALTER COLUMN order_id TYPE uuid USING NULL;

ALTER TABLE production_material ADD CONSTRAINT production_material_order_id_fkey FOREIGN KEY (order_id) REFERENCES production_order (id) ON UPDATE CASCADE;

UPDATE production_material SET order_id = production_order.id
    FROM production_order
    WHERE production_material.temp_order_id = production_order.temp_id;

ALTER TABLE production_material DROP COLUMN temp_order_id;




ALTER TABLE production_material ADD COLUMN temp_product_id bigint;
UPDATE production_material SET temp_product_id = product_id;

ALTER TABLE production_material ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE production_material ADD CONSTRAINT production_material_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE production_material SET product_id = product.id
    FROM product
    WHERE production_material.temp_product_id = product.temp_id;

ALTER TABLE production_material DROP COLUMN temp_product_id;




ALTER TABLE production_service ADD COLUMN temp_service_id bigint;
UPDATE production_service SET temp_service_id = service_id;

ALTER TABLE production_service ALTER COLUMN service_id TYPE uuid USING NULL;

ALTER TABLE production_service ADD CONSTRAINT production_service_service_id_fkey FOREIGN KEY (service_id) REFERENCES service (id) ON UPDATE CASCADE;

UPDATE production_service SET service_id = service.id
    FROM service
    WHERE production_service.temp_service_id = service.temp_id;

ALTER TABLE production_service DROP COLUMN temp_service_id;




ALTER TABLE production_service ADD COLUMN temp_order_id bigint;
UPDATE production_service SET temp_order_id = order_id;

ALTER TABLE production_service ALTER COLUMN order_id TYPE uuid USING NULL;

ALTER TABLE production_service ADD CONSTRAINT production_service_order_id_fkey FOREIGN KEY (order_id) REFERENCES production_order (id) ON UPDATE CASCADE;

UPDATE production_service SET order_id = production_order.id
    FROM production_order
    WHERE production_service.temp_order_id = production_order.temp_id;

ALTER TABLE production_service DROP COLUMN temp_order_id;




ALTER TABLE loan ADD COLUMN temp_client_id bigint;
UPDATE loan SET temp_client_id = client_id;

ALTER TABLE loan ALTER COLUMN client_id TYPE uuid USING NULL;

ALTER TABLE loan ADD CONSTRAINT loan_client_id_fkey FOREIGN KEY (client_id) REFERENCES client (id) ON UPDATE CASCADE;

UPDATE loan SET client_id = client.id
    FROM client
    WHERE loan.temp_client_id = client.temp_id;

ALTER TABLE loan DROP COLUMN temp_client_id;




ALTER TABLE loan ADD COLUMN temp_responsible_id bigint;
UPDATE loan SET temp_responsible_id = responsible_id;

ALTER TABLE loan ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE loan ADD CONSTRAINT loan_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE loan SET responsible_id = login_user.id
    FROM login_user
    WHERE loan.temp_responsible_id = login_user.temp_id;

ALTER TABLE loan DROP COLUMN temp_responsible_id;




ALTER TABLE loan ADD COLUMN temp_branch_id bigint;
UPDATE loan SET temp_branch_id = branch_id;

ALTER TABLE loan ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE loan ADD CONSTRAINT loan_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE loan SET branch_id = branch.id
    FROM branch
    WHERE loan.temp_branch_id = branch.temp_id;

ALTER TABLE loan DROP COLUMN temp_branch_id;




ALTER TABLE loan_item ADD COLUMN temp_loan_id bigint;
UPDATE loan_item SET temp_loan_id = loan_id;

ALTER TABLE loan_item ALTER COLUMN loan_id TYPE uuid USING NULL;

ALTER TABLE loan_item ADD CONSTRAINT loan_item_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES loan (id) ON UPDATE CASCADE;

UPDATE loan_item SET loan_id = loan.id
    FROM loan
    WHERE loan_item.temp_loan_id = loan.temp_id;

ALTER TABLE loan_item DROP COLUMN temp_loan_id;




ALTER TABLE loan_item ADD COLUMN temp_sellable_id bigint;
UPDATE loan_item SET temp_sellable_id = sellable_id;

ALTER TABLE loan_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE loan_item ADD CONSTRAINT loan_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE loan_item SET sellable_id = sellable.id
    FROM sellable
    WHERE loan_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE loan_item DROP COLUMN temp_sellable_id;




ALTER TABLE stock_decrease ADD COLUMN temp_responsible_id bigint;
UPDATE stock_decrease SET temp_responsible_id = responsible_id;

ALTER TABLE stock_decrease ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease ADD CONSTRAINT stock_decrease_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE stock_decrease SET responsible_id = login_user.id
    FROM login_user
    WHERE stock_decrease.temp_responsible_id = login_user.temp_id;

ALTER TABLE stock_decrease DROP COLUMN temp_responsible_id;




ALTER TABLE stock_decrease ADD COLUMN temp_removed_by_id bigint;
UPDATE stock_decrease SET temp_removed_by_id = removed_by_id;

ALTER TABLE stock_decrease ALTER COLUMN removed_by_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease ADD CONSTRAINT stock_decrease_removed_by_id_fkey FOREIGN KEY (removed_by_id) REFERENCES employee (id) ON UPDATE CASCADE;

UPDATE stock_decrease SET removed_by_id = employee.id
    FROM employee
    WHERE stock_decrease.temp_removed_by_id = employee.temp_id;

ALTER TABLE stock_decrease DROP COLUMN temp_removed_by_id;




ALTER TABLE stock_decrease ADD COLUMN temp_branch_id bigint;
UPDATE stock_decrease SET temp_branch_id = branch_id;

ALTER TABLE stock_decrease ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease ADD CONSTRAINT stock_decrease_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE stock_decrease SET branch_id = branch.id
    FROM branch
    WHERE stock_decrease.temp_branch_id = branch.temp_id;

ALTER TABLE stock_decrease DROP COLUMN temp_branch_id;




ALTER TABLE stock_decrease ADD COLUMN temp_cfop_id bigint;
UPDATE stock_decrease SET temp_cfop_id = cfop_id;

ALTER TABLE stock_decrease ALTER COLUMN cfop_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease ADD CONSTRAINT stock_decrease_cfop_id_fkey FOREIGN KEY (cfop_id) REFERENCES cfop_data (id) ON UPDATE CASCADE;

UPDATE stock_decrease SET cfop_id = cfop_data.id
    FROM cfop_data
    WHERE stock_decrease.temp_cfop_id = cfop_data.temp_id;

ALTER TABLE stock_decrease DROP COLUMN temp_cfop_id;




ALTER TABLE stock_decrease_item ADD COLUMN temp_stock_decrease_id bigint;
UPDATE stock_decrease_item SET temp_stock_decrease_id = stock_decrease_id;

ALTER TABLE stock_decrease_item ALTER COLUMN stock_decrease_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease_item ADD CONSTRAINT stock_decrease_item_stock_decrease_id_fkey FOREIGN KEY (stock_decrease_id) REFERENCES stock_decrease (id) ON UPDATE CASCADE;

UPDATE stock_decrease_item SET stock_decrease_id = stock_decrease.id
    FROM stock_decrease
    WHERE stock_decrease_item.temp_stock_decrease_id = stock_decrease.temp_id;

ALTER TABLE stock_decrease_item DROP COLUMN temp_stock_decrease_id;




ALTER TABLE stock_decrease_item ADD COLUMN temp_sellable_id bigint;
UPDATE stock_decrease_item SET temp_sellable_id = sellable_id;

ALTER TABLE stock_decrease_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease_item ADD CONSTRAINT stock_decrease_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE stock_decrease_item SET sellable_id = sellable.id
    FROM sellable
    WHERE stock_decrease_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE stock_decrease_item DROP COLUMN temp_sellable_id;




ALTER TABLE account_transaction ADD COLUMN temp_source_account_id bigint;
UPDATE account_transaction SET temp_source_account_id = source_account_id;

ALTER TABLE account_transaction ALTER COLUMN source_account_id TYPE uuid USING NULL;

ALTER TABLE account_transaction ADD CONSTRAINT account_transaction_source_account_id_fkey FOREIGN KEY (source_account_id) REFERENCES account (id) ON UPDATE CASCADE;

UPDATE account_transaction SET source_account_id = account.id
    FROM account
    WHERE account_transaction.temp_source_account_id = account.temp_id;

ALTER TABLE account_transaction DROP COLUMN temp_source_account_id;




ALTER TABLE account_transaction ADD COLUMN temp_account_id bigint;
UPDATE account_transaction SET temp_account_id = account_id;

ALTER TABLE account_transaction ALTER COLUMN account_id TYPE uuid USING NULL;

ALTER TABLE account_transaction ADD CONSTRAINT account_transaction_account_id_fkey FOREIGN KEY (account_id) REFERENCES account (id) ON UPDATE CASCADE;

UPDATE account_transaction SET account_id = account.id
    FROM account
    WHERE account_transaction.temp_account_id = account.temp_id;

ALTER TABLE account_transaction DROP COLUMN temp_account_id;




ALTER TABLE account_transaction ADD COLUMN temp_payment_id bigint;
UPDATE account_transaction SET temp_payment_id = payment_id;

ALTER TABLE account_transaction ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE account_transaction ADD CONSTRAINT account_transaction_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE account_transaction SET payment_id = payment.id
    FROM payment
    WHERE account_transaction.temp_payment_id = payment.temp_id;

ALTER TABLE account_transaction DROP COLUMN temp_payment_id;




ALTER TABLE ui_field ADD COLUMN temp_ui_form_id bigint;
UPDATE ui_field SET temp_ui_form_id = ui_form_id;

ALTER TABLE ui_field ALTER COLUMN ui_form_id TYPE uuid USING NULL;

ALTER TABLE ui_field ADD CONSTRAINT ui_field_ui_form_id_fkey FOREIGN KEY (ui_form_id) REFERENCES ui_form (id) ON UPDATE CASCADE;

UPDATE ui_field SET ui_form_id = ui_form.id
    FROM ui_form
    WHERE ui_field.temp_ui_form_id = ui_form.temp_id;

ALTER TABLE ui_field DROP COLUMN temp_ui_form_id;




ALTER TABLE product_quality_test ADD COLUMN temp_product_id bigint;
UPDATE product_quality_test SET temp_product_id = product_id;

ALTER TABLE product_quality_test ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE product_quality_test ADD CONSTRAINT product_quality_test_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE product_quality_test SET product_id = product.id
    FROM product
    WHERE product_quality_test.temp_product_id = product.temp_id;

ALTER TABLE product_quality_test DROP COLUMN temp_product_id;




ALTER TABLE production_produced_item ADD COLUMN temp_order_id bigint;
UPDATE production_produced_item SET temp_order_id = order_id;

ALTER TABLE production_produced_item ALTER COLUMN order_id TYPE uuid USING NULL;

ALTER TABLE production_produced_item ADD CONSTRAINT production_produced_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES production_order (id) ON UPDATE CASCADE;

UPDATE production_produced_item SET order_id = production_order.id
    FROM production_order
    WHERE production_produced_item.temp_order_id = production_order.temp_id;

ALTER TABLE production_produced_item DROP COLUMN temp_order_id;




ALTER TABLE production_produced_item ADD COLUMN temp_product_id bigint;
UPDATE production_produced_item SET temp_product_id = product_id;

ALTER TABLE production_produced_item ALTER COLUMN product_id TYPE uuid USING NULL;

ALTER TABLE production_produced_item ADD CONSTRAINT production_produced_item_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;

UPDATE production_produced_item SET product_id = product.id
    FROM product
    WHERE production_produced_item.temp_product_id = product.temp_id;

ALTER TABLE production_produced_item DROP COLUMN temp_product_id;




ALTER TABLE production_produced_item ADD COLUMN temp_produced_by_id bigint;
UPDATE production_produced_item SET temp_produced_by_id = produced_by_id;

ALTER TABLE production_produced_item ALTER COLUMN produced_by_id TYPE uuid USING NULL;

ALTER TABLE production_produced_item ADD CONSTRAINT production_produced_item_produced_by_id_fkey FOREIGN KEY (produced_by_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE production_produced_item SET produced_by_id = login_user.id
    FROM login_user
    WHERE production_produced_item.temp_produced_by_id = login_user.temp_id;

ALTER TABLE production_produced_item DROP COLUMN temp_produced_by_id;




ALTER TABLE production_item_quality_result ADD COLUMN temp_produced_item_id bigint;
UPDATE production_item_quality_result SET temp_produced_item_id = produced_item_id;

ALTER TABLE production_item_quality_result ALTER COLUMN produced_item_id TYPE uuid USING NULL;

ALTER TABLE production_item_quality_result ADD CONSTRAINT production_item_quality_result_produced_item_id_fkey FOREIGN KEY (produced_item_id) REFERENCES production_produced_item (id) ON UPDATE CASCADE;

UPDATE production_item_quality_result SET produced_item_id = production_produced_item.id
    FROM production_produced_item
    WHERE production_item_quality_result.temp_produced_item_id = production_produced_item.temp_id;

ALTER TABLE production_item_quality_result DROP COLUMN temp_produced_item_id;




ALTER TABLE production_item_quality_result ADD COLUMN temp_quality_test_id bigint;
UPDATE production_item_quality_result SET temp_quality_test_id = quality_test_id;

ALTER TABLE production_item_quality_result ALTER COLUMN quality_test_id TYPE uuid USING NULL;

ALTER TABLE production_item_quality_result ADD CONSTRAINT production_item_quality_result_quality_test_id_fkey FOREIGN KEY (quality_test_id) REFERENCES product_quality_test (id) ON UPDATE CASCADE;

UPDATE production_item_quality_result SET quality_test_id = product_quality_test.id
    FROM product_quality_test
    WHERE production_item_quality_result.temp_quality_test_id = product_quality_test.temp_id;

ALTER TABLE production_item_quality_result DROP COLUMN temp_quality_test_id;




ALTER TABLE production_item_quality_result ADD COLUMN temp_tested_by_id bigint;
UPDATE production_item_quality_result SET temp_tested_by_id = tested_by_id;

ALTER TABLE production_item_quality_result ALTER COLUMN tested_by_id TYPE uuid USING NULL;

ALTER TABLE production_item_quality_result ADD CONSTRAINT production_item_quality_result_tested_by_id_fkey FOREIGN KEY (tested_by_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE production_item_quality_result SET tested_by_id = login_user.id
    FROM login_user
    WHERE production_item_quality_result.temp_tested_by_id = login_user.temp_id;

ALTER TABLE production_item_quality_result DROP COLUMN temp_tested_by_id;




ALTER TABLE credit_check_history ADD COLUMN temp_client_id bigint;
UPDATE credit_check_history SET temp_client_id = client_id;

ALTER TABLE credit_check_history ALTER COLUMN client_id TYPE uuid USING NULL;

ALTER TABLE credit_check_history ADD CONSTRAINT credit_check_history_client_id_fkey FOREIGN KEY (client_id) REFERENCES client (id) ON UPDATE CASCADE;

UPDATE credit_check_history SET client_id = client.id
    FROM client
    WHERE credit_check_history.temp_client_id = client.temp_id;

ALTER TABLE credit_check_history DROP COLUMN temp_client_id;




ALTER TABLE credit_check_history ADD COLUMN temp_user_id bigint;
UPDATE credit_check_history SET temp_user_id = user_id;

ALTER TABLE credit_check_history ALTER COLUMN user_id TYPE uuid USING NULL;

ALTER TABLE credit_check_history ADD CONSTRAINT credit_check_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE credit_check_history SET user_id = login_user.id
    FROM login_user
    WHERE credit_check_history.temp_user_id = login_user.temp_id;

ALTER TABLE credit_check_history DROP COLUMN temp_user_id;




ALTER TABLE transaction_entry ADD COLUMN temp_user_id bigint;
UPDATE transaction_entry SET temp_user_id = user_id;

ALTER TABLE transaction_entry ALTER COLUMN user_id TYPE uuid USING NULL;

ALTER TABLE transaction_entry ADD CONSTRAINT transaction_entry_user_id_fkey FOREIGN KEY (user_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE transaction_entry SET user_id = login_user.id
    FROM login_user
    WHERE transaction_entry.temp_user_id = login_user.temp_id;

ALTER TABLE transaction_entry DROP COLUMN temp_user_id;




ALTER TABLE transaction_entry ADD COLUMN temp_station_id bigint;
UPDATE transaction_entry SET temp_station_id = station_id;

ALTER TABLE transaction_entry ALTER COLUMN station_id TYPE uuid USING NULL;

ALTER TABLE transaction_entry ADD CONSTRAINT transaction_entry_station_id_fkey FOREIGN KEY (station_id) REFERENCES branch_station (id) ON UPDATE CASCADE;

UPDATE transaction_entry SET station_id = branch_station.id
    FROM branch_station
    WHERE transaction_entry.temp_station_id = branch_station.temp_id;

ALTER TABLE transaction_entry DROP COLUMN temp_station_id;




ALTER TABLE card_operation_cost ADD COLUMN temp_device_id bigint;
UPDATE card_operation_cost SET temp_device_id = device_id;

ALTER TABLE card_operation_cost ALTER COLUMN device_id TYPE uuid USING NULL;

ALTER TABLE card_operation_cost ADD CONSTRAINT card_operation_cost_device_id_fkey FOREIGN KEY (device_id) REFERENCES card_payment_device (id) ON UPDATE CASCADE;

UPDATE card_operation_cost SET device_id = card_payment_device.id
    FROM card_payment_device
    WHERE card_operation_cost.temp_device_id = card_payment_device.temp_id;

ALTER TABLE card_operation_cost DROP COLUMN temp_device_id;




ALTER TABLE card_operation_cost ADD COLUMN temp_provider_id bigint;
UPDATE card_operation_cost SET temp_provider_id = provider_id;

ALTER TABLE card_operation_cost ALTER COLUMN provider_id TYPE uuid USING NULL;

ALTER TABLE card_operation_cost ADD CONSTRAINT card_operation_cost_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES credit_provider (id) ON UPDATE CASCADE;

UPDATE card_operation_cost SET provider_id = credit_provider.id
    FROM credit_provider
    WHERE card_operation_cost.temp_provider_id = credit_provider.temp_id;

ALTER TABLE card_operation_cost DROP COLUMN temp_provider_id;




ALTER TABLE stock_decrease ADD COLUMN temp_group_id bigint;
UPDATE stock_decrease SET temp_group_id = group_id;

ALTER TABLE stock_decrease ALTER COLUMN group_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease ADD CONSTRAINT stock_decrease_group_id_fkey FOREIGN KEY (group_id) REFERENCES payment_group (id) ON UPDATE CASCADE;

UPDATE stock_decrease SET group_id = payment_group.id
    FROM payment_group
    WHERE stock_decrease.temp_group_id = payment_group.temp_id;

ALTER TABLE stock_decrease DROP COLUMN temp_group_id;




ALTER TABLE credit_card_data ADD COLUMN temp_device_id bigint;
UPDATE credit_card_data SET temp_device_id = device_id;

ALTER TABLE credit_card_data ALTER COLUMN device_id TYPE uuid USING NULL;

ALTER TABLE credit_card_data ADD CONSTRAINT credit_card_data_device_id_fkey FOREIGN KEY (device_id) REFERENCES card_payment_device (id) ON UPDATE CASCADE;

UPDATE credit_card_data SET device_id = card_payment_device.id
    FROM card_payment_device
    WHERE credit_card_data.temp_device_id = card_payment_device.temp_id;

ALTER TABLE credit_card_data DROP COLUMN temp_device_id;




ALTER TABLE payment ADD COLUMN temp_attachment_id bigint;
UPDATE payment SET temp_attachment_id = attachment_id;

ALTER TABLE payment ALTER COLUMN attachment_id TYPE uuid USING NULL;

ALTER TABLE payment ADD CONSTRAINT payment_attachment_id_fkey FOREIGN KEY (attachment_id) REFERENCES attachment (id) ON UPDATE CASCADE;

UPDATE payment SET attachment_id = attachment.id
    FROM attachment
    WHERE payment.temp_attachment_id = attachment.temp_id;

ALTER TABLE payment DROP COLUMN temp_attachment_id;




ALTER TABLE stock_transaction_history ADD COLUMN temp_responsible_id bigint;
UPDATE stock_transaction_history SET temp_responsible_id = responsible_id;

ALTER TABLE stock_transaction_history ALTER COLUMN responsible_id TYPE uuid USING NULL;

ALTER TABLE stock_transaction_history ADD CONSTRAINT stock_transaction_history_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE stock_transaction_history SET responsible_id = login_user.id
    FROM login_user
    WHERE stock_transaction_history.temp_responsible_id = login_user.temp_id;

ALTER TABLE stock_transaction_history DROP COLUMN temp_responsible_id;




ALTER TABLE stock_transaction_history ADD COLUMN temp_product_stock_item_id bigint;
UPDATE stock_transaction_history SET temp_product_stock_item_id = product_stock_item_id;

ALTER TABLE stock_transaction_history ALTER COLUMN product_stock_item_id TYPE uuid USING NULL;

ALTER TABLE stock_transaction_history ADD CONSTRAINT stock_transaction_history_product_stock_item_id_fkey FOREIGN KEY (product_stock_item_id) REFERENCES product_stock_item (id) ON UPDATE CASCADE ON DELETE CASCADE;

UPDATE stock_transaction_history SET product_stock_item_id = product_stock_item.id
    FROM product_stock_item
    WHERE stock_transaction_history.temp_product_stock_item_id = product_stock_item.temp_id;

ALTER TABLE stock_transaction_history DROP COLUMN temp_product_stock_item_id;




ALTER TABLE work_order ADD COLUMN temp_category_id bigint;
UPDATE work_order SET temp_category_id = category_id;

ALTER TABLE work_order ALTER COLUMN category_id TYPE uuid USING NULL;

ALTER TABLE work_order ADD CONSTRAINT work_order_category_id_fkey FOREIGN KEY (category_id) REFERENCES work_order_category (id) ON UPDATE CASCADE;

UPDATE work_order SET category_id = work_order_category.id
    FROM work_order_category
    WHERE work_order.temp_category_id = work_order_category.temp_id;

ALTER TABLE work_order DROP COLUMN temp_category_id;




ALTER TABLE work_order ADD COLUMN temp_client_id bigint;
UPDATE work_order SET temp_client_id = client_id;

ALTER TABLE work_order ALTER COLUMN client_id TYPE uuid USING NULL;

ALTER TABLE work_order ADD CONSTRAINT work_order_client_id_fkey FOREIGN KEY (client_id) REFERENCES client (id) ON UPDATE CASCADE;

UPDATE work_order SET client_id = client.id
    FROM client
    WHERE work_order.temp_client_id = client.temp_id;

ALTER TABLE work_order DROP COLUMN temp_client_id;




ALTER TABLE cost_center_entry ADD COLUMN temp_cost_center_id bigint;
UPDATE cost_center_entry SET temp_cost_center_id = cost_center_id;

ALTER TABLE cost_center_entry ALTER COLUMN cost_center_id TYPE uuid USING NULL;

ALTER TABLE cost_center_entry ADD CONSTRAINT cost_center_entry_cost_center_id_fkey FOREIGN KEY (cost_center_id) REFERENCES cost_center (id) ON UPDATE CASCADE;

UPDATE cost_center_entry SET cost_center_id = cost_center.id
    FROM cost_center
    WHERE cost_center_entry.temp_cost_center_id = cost_center.temp_id;

ALTER TABLE cost_center_entry DROP COLUMN temp_cost_center_id;




ALTER TABLE cost_center_entry ADD COLUMN temp_payment_id bigint;
UPDATE cost_center_entry SET temp_payment_id = payment_id;

ALTER TABLE cost_center_entry ALTER COLUMN payment_id TYPE uuid USING NULL;

ALTER TABLE cost_center_entry ADD CONSTRAINT cost_center_entry_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment (id) ON UPDATE CASCADE;

UPDATE cost_center_entry SET payment_id = payment.id
    FROM payment
    WHERE cost_center_entry.temp_payment_id = payment.temp_id;

ALTER TABLE cost_center_entry DROP COLUMN temp_payment_id;




ALTER TABLE cost_center_entry ADD COLUMN temp_stock_transaction_id bigint;
UPDATE cost_center_entry SET temp_stock_transaction_id = stock_transaction_id;

ALTER TABLE cost_center_entry ALTER COLUMN stock_transaction_id TYPE uuid USING NULL;

ALTER TABLE cost_center_entry ADD CONSTRAINT cost_center_entry_stock_transaction_id_fkey FOREIGN KEY (stock_transaction_id) REFERENCES stock_transaction_history (id) ON UPDATE CASCADE;

UPDATE cost_center_entry SET stock_transaction_id = stock_transaction_history.id
    FROM stock_transaction_history
    WHERE cost_center_entry.temp_stock_transaction_id = stock_transaction_history.temp_id;

ALTER TABLE cost_center_entry DROP COLUMN temp_stock_transaction_id;




ALTER TABLE sale ADD COLUMN temp_cost_center_id bigint;
UPDATE sale SET temp_cost_center_id = cost_center_id;

ALTER TABLE sale ALTER COLUMN cost_center_id TYPE uuid USING NULL;

ALTER TABLE sale ADD CONSTRAINT sale_cost_center_id_fkey FOREIGN KEY (cost_center_id) REFERENCES cost_center (id) ON UPDATE CASCADE;

UPDATE sale SET cost_center_id = cost_center.id
    FROM cost_center
    WHERE sale.temp_cost_center_id = cost_center.temp_id;

ALTER TABLE sale DROP COLUMN temp_cost_center_id;




ALTER TABLE stock_decrease ADD COLUMN temp_cost_center_id bigint;
UPDATE stock_decrease SET temp_cost_center_id = cost_center_id;

ALTER TABLE stock_decrease ALTER COLUMN cost_center_id TYPE uuid USING NULL;

ALTER TABLE stock_decrease ADD CONSTRAINT stock_decrease_cost_center_id_fkey FOREIGN KEY (cost_center_id) REFERENCES cost_center (id) ON UPDATE CASCADE;

UPDATE stock_decrease SET cost_center_id = cost_center.id
    FROM cost_center
    WHERE stock_decrease.temp_cost_center_id = cost_center.temp_id;

ALTER TABLE stock_decrease DROP COLUMN temp_cost_center_id;




ALTER TABLE work_order ADD COLUMN temp_branch_id bigint;
UPDATE work_order SET temp_branch_id = branch_id;

ALTER TABLE work_order ALTER COLUMN branch_id TYPE uuid USING NULL;

ALTER TABLE work_order ADD CONSTRAINT work_order_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE work_order SET branch_id = branch.id
    FROM branch
    WHERE work_order.temp_branch_id = branch.temp_id;

ALTER TABLE work_order DROP COLUMN temp_branch_id;




ALTER TABLE work_order ADD COLUMN temp_quote_responsible_id bigint;
UPDATE work_order SET temp_quote_responsible_id = quote_responsible_id;

ALTER TABLE work_order ALTER COLUMN quote_responsible_id TYPE uuid USING NULL;

ALTER TABLE work_order ADD CONSTRAINT work_order_quote_responsible_id_fkey FOREIGN KEY (quote_responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE work_order SET quote_responsible_id = login_user.id
    FROM login_user
    WHERE work_order.temp_quote_responsible_id = login_user.temp_id;

ALTER TABLE work_order DROP COLUMN temp_quote_responsible_id;




ALTER TABLE work_order ADD COLUMN temp_execution_responsible_id bigint;
UPDATE work_order SET temp_execution_responsible_id = execution_responsible_id;

ALTER TABLE work_order ALTER COLUMN execution_responsible_id TYPE uuid USING NULL;

ALTER TABLE work_order ADD CONSTRAINT work_order_execution_responsible_id_fkey FOREIGN KEY (execution_responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE work_order SET execution_responsible_id = login_user.id
    FROM login_user
    WHERE work_order.temp_execution_responsible_id = login_user.temp_id;

ALTER TABLE work_order DROP COLUMN temp_execution_responsible_id;




ALTER TABLE work_order ADD COLUMN temp_sale_id bigint;
UPDATE work_order SET temp_sale_id = sale_id;

ALTER TABLE work_order ALTER COLUMN sale_id TYPE uuid USING NULL;

ALTER TABLE work_order ADD CONSTRAINT work_order_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sale (id) ON UPDATE CASCADE;

UPDATE work_order SET sale_id = sale.id
    FROM sale
    WHERE work_order.temp_sale_id = sale.temp_id;

ALTER TABLE work_order DROP COLUMN temp_sale_id;




ALTER TABLE work_order_item ADD COLUMN temp_sellable_id bigint;
UPDATE work_order_item SET temp_sellable_id = sellable_id;

ALTER TABLE work_order_item ALTER COLUMN sellable_id TYPE uuid USING NULL;

ALTER TABLE work_order_item ADD CONSTRAINT work_order_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable (id) ON UPDATE CASCADE;

UPDATE work_order_item SET sellable_id = sellable.id
    FROM sellable
    WHERE work_order_item.temp_sellable_id = sellable.temp_id;

ALTER TABLE work_order_item DROP COLUMN temp_sellable_id;




ALTER TABLE work_order_item ADD COLUMN temp_order_id bigint;
UPDATE work_order_item SET temp_order_id = order_id;

ALTER TABLE work_order_item ALTER COLUMN order_id TYPE uuid USING NULL;

ALTER TABLE work_order_item ADD CONSTRAINT work_order_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES work_order (id) ON UPDATE CASCADE;

UPDATE work_order_item SET order_id = work_order.id
    FROM work_order
    WHERE work_order_item.temp_order_id = work_order.temp_id;

ALTER TABLE work_order_item DROP COLUMN temp_order_id;




ALTER TABLE work_order_package ADD COLUMN temp_send_responsible_id bigint;
UPDATE work_order_package SET temp_send_responsible_id = send_responsible_id;

ALTER TABLE work_order_package ALTER COLUMN send_responsible_id TYPE uuid USING NULL;

ALTER TABLE work_order_package ADD CONSTRAINT work_order_package_send_responsible_id_fkey FOREIGN KEY (send_responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE work_order_package SET send_responsible_id = login_user.id
    FROM login_user
    WHERE work_order_package.temp_send_responsible_id = login_user.temp_id;

ALTER TABLE work_order_package DROP COLUMN temp_send_responsible_id;




ALTER TABLE work_order_package ADD COLUMN temp_receive_responsible_id bigint;
UPDATE work_order_package SET temp_receive_responsible_id = receive_responsible_id;

ALTER TABLE work_order_package ALTER COLUMN receive_responsible_id TYPE uuid USING NULL;

ALTER TABLE work_order_package ADD CONSTRAINT work_order_package_receive_responsible_id_fkey FOREIGN KEY (receive_responsible_id) REFERENCES login_user (id) ON UPDATE CASCADE;

UPDATE work_order_package SET receive_responsible_id = login_user.id
    FROM login_user
    WHERE work_order_package.temp_receive_responsible_id = login_user.temp_id;

ALTER TABLE work_order_package DROP COLUMN temp_receive_responsible_id;




ALTER TABLE work_order_package ADD COLUMN temp_destination_branch_id bigint;
UPDATE work_order_package SET temp_destination_branch_id = destination_branch_id;

ALTER TABLE work_order_package ALTER COLUMN destination_branch_id TYPE uuid USING NULL;

ALTER TABLE work_order_package ADD CONSTRAINT work_order_package_destination_branch_id_fkey FOREIGN KEY (destination_branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE work_order_package SET destination_branch_id = branch.id
    FROM branch
    WHERE work_order_package.temp_destination_branch_id = branch.temp_id;

ALTER TABLE work_order_package DROP COLUMN temp_destination_branch_id;




ALTER TABLE work_order_package ADD COLUMN temp_source_branch_id bigint;
UPDATE work_order_package SET temp_source_branch_id = source_branch_id;

ALTER TABLE work_order_package ALTER COLUMN source_branch_id TYPE uuid USING NULL;

ALTER TABLE work_order_package ADD CONSTRAINT work_order_package_source_branch_id_fkey FOREIGN KEY (source_branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE work_order_package SET source_branch_id = branch.id
    FROM branch
    WHERE work_order_package.temp_source_branch_id = branch.temp_id;

ALTER TABLE work_order_package DROP COLUMN temp_source_branch_id;




ALTER TABLE work_order_package_item ADD COLUMN temp_order_id bigint;
UPDATE work_order_package_item SET temp_order_id = order_id;

ALTER TABLE work_order_package_item ALTER COLUMN order_id TYPE uuid USING NULL;

ALTER TABLE work_order_package_item ADD CONSTRAINT work_order_package_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES work_order (id) ON UPDATE CASCADE;

UPDATE work_order_package_item SET order_id = work_order.id
    FROM work_order
    WHERE work_order_package_item.temp_order_id = work_order.temp_id;

ALTER TABLE work_order_package_item DROP COLUMN temp_order_id;




ALTER TABLE work_order_package_item ADD COLUMN temp_package_id bigint;
UPDATE work_order_package_item SET temp_package_id = package_id;

ALTER TABLE work_order_package_item ALTER COLUMN package_id TYPE uuid USING NULL;

ALTER TABLE work_order_package_item ADD CONSTRAINT work_order_package_item_package_id_fkey FOREIGN KEY (package_id) REFERENCES work_order_package (id) ON UPDATE CASCADE;

UPDATE work_order_package_item SET package_id = work_order_package.id
    FROM work_order_package
    WHERE work_order_package_item.temp_package_id = work_order_package.temp_id;

ALTER TABLE work_order_package_item DROP COLUMN temp_package_id;




ALTER TABLE work_order ADD COLUMN temp_current_branch_id bigint;
UPDATE work_order SET temp_current_branch_id = current_branch_id;

ALTER TABLE work_order ALTER COLUMN current_branch_id TYPE uuid USING NULL;

ALTER TABLE work_order ADD CONSTRAINT work_order_current_branch_id_fkey FOREIGN KEY (current_branch_id) REFERENCES branch (id) ON UPDATE CASCADE;

UPDATE work_order SET current_branch_id = branch.id
    FROM branch
    WHERE work_order.temp_current_branch_id = branch.temp_id;

ALTER TABLE work_order DROP COLUMN temp_current_branch_id;

-- Post pass 13: updates the script didn't catch

ALTER TABLE inventory_item ADD COLUMN temp_batch_id bigint;
UPDATE inventory_item SET temp_batch_id = batch_id;
ALTER TABLE inventory_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE inventory_item ADD CONSTRAINT inventory_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE inventory_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE inventory_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE inventory_item DROP COLUMN temp_batch_id;

ALTER TABLE loan_item ADD COLUMN temp_batch_id bigint;
UPDATE loan_item SET temp_batch_id = batch_id;
ALTER TABLE loan_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE loan_item ADD CONSTRAINT loan_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE loan_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE loan_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE loan_item DROP COLUMN temp_batch_id;

ALTER TABLE product_stock_item ADD COLUMN temp_batch_id bigint;
UPDATE product_stock_item SET temp_batch_id = batch_id;
ALTER TABLE product_stock_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE product_stock_item ADD CONSTRAINT product_stock_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE product_stock_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE product_stock_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE product_stock_item DROP COLUMN temp_batch_id;

ALTER TABLE receiving_order_item ADD COLUMN temp_batch_id bigint;
UPDATE receiving_order_item SET temp_batch_id = batch_id;
ALTER TABLE receiving_order_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE receiving_order_item ADD CONSTRAINT receiving_order_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE receiving_order_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE receiving_order_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE receiving_order_item DROP COLUMN temp_batch_id;

ALTER TABLE returned_sale_item ADD COLUMN temp_batch_id bigint;
UPDATE returned_sale_item SET temp_batch_id = batch_id;
ALTER TABLE returned_sale_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE returned_sale_item ADD CONSTRAINT returned_sale_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE returned_sale_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE returned_sale_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE returned_sale_item DROP COLUMN temp_batch_id;

ALTER TABLE sale_item ADD COLUMN temp_batch_id bigint;
UPDATE sale_item SET temp_batch_id = batch_id;
ALTER TABLE sale_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE sale_item ADD CONSTRAINT sale_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE sale_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE sale_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE sale_item DROP COLUMN temp_batch_id;

ALTER TABLE stock_decrease_item ADD COLUMN temp_batch_id bigint;
UPDATE stock_decrease_item SET temp_batch_id = batch_id;
ALTER TABLE stock_decrease_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE stock_decrease_item ADD CONSTRAINT stock_decrease_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE stock_decrease_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE stock_decrease_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE stock_decrease_item DROP COLUMN temp_batch_id;

ALTER TABLE transfer_order_item ADD COLUMN temp_batch_id bigint;
UPDATE transfer_order_item SET temp_batch_id = batch_id;
ALTER TABLE transfer_order_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE transfer_order_item ADD CONSTRAINT transfer_order_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE transfer_order_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE transfer_order_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE transfer_order_item DROP COLUMN temp_batch_id;

ALTER TABLE work_order_item ADD COLUMN temp_batch_id bigint;
UPDATE work_order_item SET temp_batch_id = batch_id;
ALTER TABLE work_order_item ALTER COLUMN batch_id TYPE uuid USING NULL;
ALTER TABLE work_order_item ADD CONSTRAINT work_order_item_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES storable_batch (id) ON UPDATE CASCADE;
UPDATE work_order_item SET batch_id = storable_batch.id
    FROM storable_batch
    WHERE work_order_item.temp_batch_id = storable_batch.temp_id;
ALTER TABLE work_order_item DROP COLUMN temp_batch_id;

ALTER TABLE storable_batch ADD COLUMN temp_storable_id bigint;
UPDATE storable_batch SET temp_storable_id = storable_id;
ALTER TABLE storable_batch ALTER COLUMN storable_id TYPE uuid USING NULL;
ALTER TABLE storable_batch ADD CONSTRAINT storable_batch_storable_id_fkey FOREIGN KEY (storable_id) REFERENCES storable (id) ON UPDATE CASCADE;
UPDATE storable_batch SET storable_id = storable.id
    FROM storable
    WHERE storable_batch.temp_storable_id = storable.temp_id;
ALTER TABLE storable_batch DROP COLUMN temp_storable_id;

-- Pass 14: Add back temporarily disabled constraints

ALTER TABLE commission_source ADD CONSTRAINT check_exist_one_fkey
      CHECK (category_id IS NOT NULL AND sellable_id IS NULL OR
             category_id IS NULL AND sellable_id IS NOT NULL);
ALTER TABLE cost_center_entry ADD CONSTRAINT stock_transaction_or_payment
      CHECK ((payment_id IS NULL AND stock_transaction_id IS NOT NULL) OR
             (payment_id IS NOT NULL AND stock_transaction_id IS NULL));
ALTER TABLE product_component ADD CONSTRAINT different_products
      CHECK (product_id != component_id);
ALTER TABLE work_order_package ADD CONSTRAINT different_branches
      CHECK (source_branch_id != destination_branch_id);

ALTER TABLE account_transaction ALTER COLUMN account_id SET NOT NULL;
ALTER TABLE account_transaction ALTER COLUMN source_account_id SET NOT NULL;
ALTER TABLE branch_synchronization ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE commission ALTER COLUMN payment_id SET NOT NULL;
ALTER TABLE commission ALTER COLUMN sale_id SET NOT NULL;
ALTER TABLE commission ALTER COLUMN salesperson_id SET NOT NULL;
ALTER TABLE cost_center_entry ALTER COLUMN cost_center_id SET NOT NULL;
ALTER TABLE fiscal_book_entry ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE inventory_item ALTER COLUMN inventory_id SET NOT NULL;
ALTER TABLE inventory_item ALTER COLUMN product_id SET NOT NULL;
ALTER TABLE loan ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE payment ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE payment_method ALTER COLUMN destination_account_id SET NOT NULL;
ALTER TABLE payment_renegotiation ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE product_history ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE product_stock_item ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE product_supplier_info ALTER COLUMN product_id SET NOT NULL;
ALTER TABLE product_supplier_info ALTER COLUMN supplier_id SET NOT NULL;
ALTER TABLE production_order ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE purchase_order ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE quotation ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE quote_group ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE receiving_order ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE receiving_order ALTER COLUMN purchase_id SET NOT NULL;
ALTER TABLE returned_sale ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE sale ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE stock_decrease ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE stock_transaction_history ALTER COLUMN product_stock_item_id SET NOT NULL;
ALTER TABLE stock_transaction_history ALTER COLUMN responsible_id SET NOT NULL;
ALTER TABLE storable_batch ALTER COLUMN storable_id SET NOT NULL;
ALTER TABLE till_entry ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE till_entry ALTER COLUMN till_id SET NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN destination_branch_id SET NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN destination_responsible_id SET NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN source_branch_id SET NOT NULL;
ALTER TABLE transfer_order ALTER COLUMN source_responsible_id SET NOT NULL;
ALTER TABLE transfer_order_item ALTER COLUMN sellable_id SET NOT NULL;
ALTER TABLE transfer_order_item ALTER COLUMN transfer_order_id SET NOT NULL;
ALTER TABLE user_branch_access ALTER COLUMN branch_id SET NOT NULL;
ALTER TABLE user_branch_access ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE work_order_package ALTER COLUMN source_branch_id SET NOT NULL;
ALTER TABLE work_order_package_item ALTER COLUMN order_id SET NOT NULL;
ALTER TABLE work_order_package_item ALTER COLUMN package_id SET NOT NULL;

-- Pass 15: Migrate stock_transaction_history.object_id

\set TYPE_INITIAL 0 -- NULL
\set TYPE_SELL 1 -- sale_item
\set TYPE_RETURNED_SALE 2 -- returned_sale_item
\set TYPE_CANCELED_SALE 3 -- sale_item
\set TYPE_RECEIVED_PURCHASE 4 -- receiving_order_item
\set TYPE_RETURNED_LOAN 5 -- loan_item
\set TYPE_LOANED 6 -- loan_item
\set TYPE_PRODUCTION_ALLOCATED 7 -- production_material
\set TYPE_PRODUCTION_PRODUCED 8 -- production_item
\set TYPE_PRODUCTION_RETURNED 9 -- production_material
\set TYPE_STOCK_DECREASE 10 -- stock_decrease
\set TYPE_TRANSFER_FROM 11 -- transfer_order_item
\set TYPE_TRANSFER_TO 12 -- transfer_order_item
\set TYPE_INVENTORY_ADJUST 13 -- inventory_item
\set TYPE_PRODUCTION_SENT 14 -- production_produced_item
\set TYPE_IMPORTED 15 -- NULL
\set TYPE_CONSIGNMENT_RETURNED 16 -- purchase_item
\set TYPE_WORK_ORDER_USED 17 -- purchase_item

ALTER TABLE stock_transaction_history ADD COLUMN temp_object_id bigint;
UPDATE stock_transaction_history SET temp_object_id = object_id;
UPDATE stock_transaction_history SET object_id = NULL;
ALTER TABLE stock_transaction_history ALTER COLUMN object_id TYPE uuid USING NULL;
UPDATE stock_transaction_history SET object_id = NULL
  WHERE "type" in (:TYPE_INITIAL, :TYPE_IMPORTED);
UPDATE stock_transaction_history SET object_id = t.id FROM sale_item AS t
  WHERE "type" in (:TYPE_SELL, :TYPE_CANCELED_SALE);
UPDATE stock_transaction_history SET object_id = t.id FROM returned_sale_item AS t
  WHERE "type" in (:TYPE_RETURNED_SALE);
UPDATE stock_transaction_history SET object_id = t.id FROM receiving_order_item AS t
  WHERE "type" in (:TYPE_RECEIVED_PURCHASE);
UPDATE stock_transaction_history SET object_id = t.id FROM loan_item AS t
  WHERE "type" in (:TYPE_RETURNED_LOAN, :TYPE_LOANED);
UPDATE stock_transaction_history SET object_id = t.id FROM production_material AS t
  WHERE "type" in (:TYPE_PRODUCTION_ALLOCATED, :TYPE_PRODUCTION_RETURNED);
UPDATE stock_transaction_history SET object_id = t.id FROM production_item AS t
  WHERE "type" in (:TYPE_PRODUCTION_PRODUCED);
UPDATE stock_transaction_history SET object_id = t.id FROM stock_decrease AS t
  WHERE "type" in (:TYPE_STOCK_DECREASE);
UPDATE stock_transaction_history SET object_id = t.id FROM transfer_order_item AS t
  WHERE "type" in (:TYPE_TRANSFER_TO, :TYPE_TRANSFER_FROM);
UPDATE stock_transaction_history SET object_id = t.id FROM inventory_item AS t
  WHERE "type" in (:TYPE_INVENTORY_ADJUST);
UPDATE stock_transaction_history SET object_id = t.id FROM production_produced_item AS t
  WHERE "type" in (:TYPE_PRODUCTION_SENT);
UPDATE stock_transaction_history SET object_id = t.id FROM purchase_item AS t
  WHERE "type" in (:TYPE_CONSIGNMENT_RETURNED, :TYPE_WORK_ORDER_USED);
ALTER TABLE stock_transaction_history DROP COLUMN temp_object_id;

-- Pass 16: Migrate parameters

UPDATE parameter_data SET field_value = t.id::text
  FROM branch AS t
  WHERE parameter_data.field_name = 'MAIN_COMPANY' AND
                        t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM employee_role AS t
  WHERE parameter_data.field_name = 'DEFAULT_SALESPERSON_ROLE' AND
         t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM supplier AS t
  WHERE parameter_data.field_name = 'SUGGESTED_SUPPLIER' AND
            t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM sellable_unit AS t
 WHERE parameter_data.field_name = 'SUGGESTED_UNIT' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM image AS t
 WHERE parameter_data.field_name = 'CUSTOM_LOGO_FOR_REPORTS' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM service AS t
 WHERE parameter_data.field_name = 'DELIVERY_SERVICE' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM cfop_data AS t
 WHERE parameter_data.field_name = 'DEFAULT_SALES_CFOP' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM cfop_data AS t
 WHERE parameter_data.field_name = 'DEFAULT_RETURN_SALES_CFOP' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM cfop_data AS t
 WHERE parameter_data.field_name = 'DEFAULT_STOCK_DECREASE_CFOP' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM cfop_data AS t
 WHERE parameter_data.field_name = 'DEFAULT_RECEIVING_CFOP' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM sellable_tax_constant AS t
 WHERE parameter_data.field_name = 'DEFAULT_PRODUCT_TAX_CONSTANT' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM account AS t
 WHERE parameter_data.field_name = 'BANKS_ACCOUNT' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM account AS t
 WHERE parameter_data.field_name = 'TILLS_ACCOUNT' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM account AS t
 WHERE parameter_data.field_name = 'IMBALANCE_ACCOUNT' AND
     t.temp_id = parameter_data.field_value::bigint;

UPDATE parameter_data SET field_value = t.id::text
  FROM branch AS t
 WHERE parameter_data.field_name = 'LOCAL_BRANCH' AND
     t.temp_id = parameter_data.field_value::bigint;

-- Pass 17: Migrate ECF plugin

CREATE OR REPLACE FUNCTION patch_04_20_migrate_ecf_plugin() RETURNS VOID AS $$
DECLARE
BEGIN

  PERFORM plugin_name FROM installed_plugin WHERE plugin_name = 'ecf';
  IF NOT FOUND THEN

    ALTER TABLE device_constant ADD COLUMN temp_device_settings_id bigint;
    UPDATE device_constant SET temp_device_settings_id = device_settings_id;

    ALTER TABLE device_constant ALTER COLUMN device_settings_id TYPE uuid USING NULL;

    ALTER TABLE device_constant ADD CONSTRAINT device_constant_device_settings_id_fkey FOREIGN KEY (device_settings_id) REFERENCES device_settings (id) ON UPDATE CASCADE;

    UPDATE device_constant SET device_settings_id = device_settings.id
      FROM device_settings
     WHERE device_constant.temp_device_settings_id = device_settings.temp_id;

    ALTER TABLE device_constant DROP COLUMN temp_device_settings_id;

    RETURN;
  END IF;

  -- Pass 1: Add new column
  ALTER TABLE ecf_printer ADD COLUMN temp_id bigint;
  ALTER TABLE ecf_document_history ADD COLUMN temp_id bigint;

  -- Pass 2: Copy over the ID to the temporary column
  UPDATE ecf_printer SET temp_id = id;
  UPDATE ecf_document_history SET temp_id = id;

  -- Pass 3: Remove the default serial value
  ALTER TABLE ecf_printer ALTER COLUMN id DROP DEFAULT;
  ALTER TABLE ecf_document_history ALTER COLUMN id DROP DEFAULT;

  -- Pass 4: Remove the constraints for the ID columns
  ALTER TABLE ecf_printer DROP CONSTRAINT ecf_printer_pkey CASCADE;
  ALTER TABLE ecf_document_history DROP CONSTRAINT ecf_document_history_pkey CASCADE;

  -- Pass 5: Remove NOT NULL for the ID columns
  ALTER TABLE ecf_printer ALTER COLUMN id DROP NOT NULL;
  ALTER TABLE ecf_document_history ALTER COLUMN id DROP NOT NULL;

  -- Pass 6: Reset the old ID columns
  UPDATE ecf_printer SET id = NULL;
  UPDATE ecf_document_history SET id = NULL;

  -- Pass 7: Change the column type to uuid
  ALTER TABLE ecf_printer ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
  ALTER TABLE ecf_document_history ALTER COLUMN id TYPE uuid USING uuid_generate_v1();

  -- Pass 8: Add back a default
  ALTER TABLE ecf_printer ALTER COLUMN id SET DEFAULT uuid_generate_v1();
  ALTER TABLE ecf_document_history ALTER COLUMN id SET DEFAULT uuid_generate_v1();

  -- Pass 9: Add back the primary keys
  ALTER TABLE ecf_printer ADD CONSTRAINT ecf_printer_pkey PRIMARY KEY(id);
  ALTER TABLE ecf_document_history ADD CONSTRAINT ecf_document_history_pkey PRIMARY KEY(id);

  -- Pass 10: Add back NOT NULL for the id column
  ALTER TABLE ecf_printer ALTER COLUMN id SET NOT NULL;
  ALTER TABLE ecf_printer ALTER COLUMN id SET NOT NULL;

  -- Pass 11: Update foreign keys

  ALTER TABLE ecf_printer ADD COLUMN temp_station_id bigint;
  UPDATE ecf_printer SET temp_station_id = station_id;
  ALTER TABLE ecf_printer ALTER COLUMN station_id DROP NOT NULL;
  ALTER TABLE ecf_printer ALTER COLUMN station_id TYPE uuid USING NULL;
  ALTER TABLE ecf_printer ADD CONSTRAINT ecf_printer_station_id_fkey FOREIGN KEY (station_id) REFERENCES branch_station (id) ON UPDATE CASCADE;
  UPDATE ecf_printer SET station_id = branch_station.id
    FROM branch_station
    WHERE ecf_printer.temp_station_id = branch_station.temp_id;
  ALTER TABLE ecf_printer DROP COLUMN temp_station_id;
  ALTER TABLE ecf_printer ALTER COLUMN station_id SET NOT NULL;

  ALTER TABLE ecf_printer ADD COLUMN temp_last_sale_id bigint;
  UPDATE ecf_printer SET temp_last_sale_id = last_sale_id;
  ALTER TABLE ecf_printer ALTER COLUMN last_sale_id TYPE uuid USING NULL;
  ALTER TABLE ecf_printer ADD CONSTRAINT ecf_printer_last_sale_id_fkey FOREIGN KEY (last_sale_id) REFERENCES sale (id) ON UPDATE CASCADE;
  UPDATE ecf_printer SET last_sale_id = sale.id
    FROM sale
    WHERE ecf_printer.temp_last_sale_id = sale.temp_id;
  ALTER TABLE ecf_printer DROP COLUMN temp_last_sale_id;

  ALTER TABLE ecf_printer ADD COLUMN temp_last_till_entry_id bigint;
  UPDATE ecf_printer SET temp_last_till_entry_id = last_till_entry_id;
  ALTER TABLE ecf_printer ALTER COLUMN last_till_entry_id TYPE uuid USING NULL;
  ALTER TABLE ecf_printer ADD CONSTRAINT ecf_printer_last_till_entry_id_fkey FOREIGN KEY (last_till_entry_id) REFERENCES till_entry (id) ON UPDATE CASCADE;
  UPDATE ecf_printer SET last_till_entry_id = till_entry.id
    FROM till_entry
    WHERE ecf_printer.temp_last_till_entry_id = till_entry.temp_id;
  ALTER TABLE ecf_printer DROP COLUMN temp_last_till_entry_id;

  ALTER TABLE ecf_document_history ADD COLUMN temp_printer_id bigint;
  UPDATE ecf_document_history SET temp_printer_id = printer_id;
  ALTER TABLE ecf_document_history ALTER COLUMN printer_id DROP NOT NULL;
  ALTER TABLE ecf_document_history ALTER COLUMN printer_id TYPE uuid USING NULL;
  ALTER TABLE ecf_document_history ADD CONSTRAINT ecf_document_history_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES ecf_printer (id) ON UPDATE CASCADE;
  UPDATE ecf_document_history SET printer_id = ecf_printer.id
    FROM ecf_printer
    WHERE ecf_document_history.temp_printer_id = ecf_printer.temp_id;
  ALTER TABLE ecf_document_history DROP COLUMN temp_printer_id;
  ALTER TABLE ecf_document_history ALTER COLUMN printer_id SET NOT NULL;

  ALTER TABLE device_constant ADD COLUMN temp_printer_id bigint;
  UPDATE device_constant SET temp_printer_id = printer_id;
  ALTER TABLE device_constant ALTER COLUMN printer_id TYPE uuid USING NULL;
  ALTER TABLE device_constant ADD CONSTRAINT device_constant_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES ecf_printer (id) ON UPDATE CASCADE;
  UPDATE device_constant SET printer_id = ecf_printer.id
    FROM ecf_printer
    WHERE device_constant.temp_printer_id = ecf_printer.temp_id;
  ALTER TABLE device_constant DROP COLUMN temp_printer_id;

  -- Pass 12: Remove temporary ID columns
  ALTER TABLE ecf_printer DROP COLUMN temp_id;
  ALTER TABLE ecf_document_history DROP COLUMN temp_id;

END;
$$ LANGUAGE plpgsql;

SELECT patch_04_20_migrate_ecf_plugin();
DROP FUNCTION patch_04_20_migrate_ecf_plugin();

-- Pass 18: Migrate books plugin

CREATE OR REPLACE FUNCTION patch_04_20_migrate_books_plugin() RETURNS VOID AS $$
DECLARE
BEGIN

  PERFORM plugin_name FROM installed_plugin WHERE plugin_name = 'books';
  IF NOT FOUND THEN
    RETURN;
  END IF;

  -- Pass 1: Add new column
  ALTER TABLE book ADD COLUMN temp_id bigint;
  ALTER TABLE book_publisher ADD COLUMN temp_id bigint;

  -- Pass 2: Copy over the ID to the temporary column
  UPDATE book SET temp_id = id;
  UPDATE book_publisher SET temp_id = id;

  -- Pass 3: Remove the default serial value
  ALTER TABLE book ALTER COLUMN id DROP DEFAULT;
  ALTER TABLE book_publisher ALTER COLUMN id DROP DEFAULT;

  -- Pass 4: Remove the constraints for the ID columns
  ALTER TABLE book DROP CONSTRAINT product_adapt_to_book_pkey CASCADE;
  ALTER TABLE book_publisher DROP CONSTRAINT person_adapt_to_publisher_pkey CASCADE;

  -- Pass 5: Remove NOT NULL for the ID columns
  ALTER TABLE book ALTER COLUMN id DROP NOT NULL;
  ALTER TABLE book_publisher ALTER COLUMN id DROP NOT NULL;

  -- Pass 6: Reset the old ID columns
  UPDATE book SET id = NULL;
  UPDATE book_publisher SET id = NULL;

  -- Pass 7: Change the column type to uuid
  ALTER TABLE book ALTER COLUMN id TYPE uuid USING uuid_generate_v1();
  ALTER TABLE book_publisher ALTER COLUMN id TYPE uuid USING uuid_generate_v1();

  -- Pass 8: Add back a default
  ALTER TABLE book ALTER COLUMN id SET DEFAULT uuid_generate_v1();
  ALTER TABLE book_publisher ALTER COLUMN id SET DEFAULT uuid_generate_v1();

  -- Pass 9: Add back the primary keys
  ALTER TABLE book ADD CONSTRAINT book_pkey PRIMARY KEY(id);
  ALTER TABLE book_publisher ADD CONSTRAINT book_publisher_pkey PRIMARY KEY(id);

  -- Pass 10: Add back NOT NULL for the id column
  ALTER TABLE book ALTER COLUMN id SET NOT NULL;
  ALTER TABLE book_publisher ALTER COLUMN id SET NOT NULL;

  -- Pass 11: Update foreign keys
  ALTER TABLE book ADD COLUMN temp_product_id bigint;
  UPDATE book SET temp_product_id = product_id;
  ALTER TABLE book ALTER COLUMN product_id TYPE uuid USING NULL;
  ALTER TABLE book ADD CONSTRAINT book_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) ON UPDATE CASCADE;
  UPDATE book SET product_id = product.id
    FROM product
    WHERE book.temp_product_id = product.temp_id;
  ALTER TABLE book DROP COLUMN temp_product_id;

  ALTER TABLE book ADD COLUMN temp_publisher_id bigint;
  UPDATE book SET temp_publisher_id = publisher_id;
  ALTER TABLE book ALTER COLUMN publisher_id TYPE uuid USING NULL;
  ALTER TABLE book ADD CONSTRAINT book_publisher_id_fkey FOREIGN KEY (publisher_id) REFERENCES book_publisher (id) ON UPDATE CASCADE;
  UPDATE book SET publisher_id = book_publisher.id
    FROM book_publisher
    WHERE book.temp_publisher_id = book_publisher.temp_id;
  ALTER TABLE book DROP COLUMN temp_publisher_id;

  ALTER TABLE book_publisher ADD COLUMN temp_person_id bigint;
  UPDATE book_publisher SET temp_person_id = person_id;
  ALTER TABLE book_publisher ALTER COLUMN person_id TYPE uuid USING NULL;
  ALTER TABLE book_publisher ADD CONSTRAINT book_publisher_person_id_fkey FOREIGN KEY (person_id) REFERENCES person (id) ON UPDATE CASCADE;
  UPDATE book_publisher SET person_id = person.id
    FROM person
    WHERE book_publisher.temp_person_id = person.temp_id;
  ALTER TABLE book_publisher DROP COLUMN temp_person_id;

  -- Pass 12: Remove temporary ID columns
  ALTER TABLE book DROP COLUMN temp_id;
  ALTER TABLE book_publisher DROP COLUMN temp_id;

END;
$$ LANGUAGE plpgsql;

SELECT patch_04_20_migrate_books_plugin();
DROP FUNCTION patch_04_20_migrate_books_plugin();

-- Pass 19: Remove temporary ID columns

ALTER TABLE account DROP COLUMN temp_id;
ALTER TABLE account_transaction DROP COLUMN temp_id;
ALTER TABLE address DROP COLUMN temp_id;
ALTER TABLE attachment DROP COLUMN temp_id;
ALTER TABLE bank_account DROP COLUMN temp_id;
ALTER TABLE bill_option DROP COLUMN temp_id;
ALTER TABLE branch DROP COLUMN temp_id;
ALTER TABLE branch_station DROP COLUMN temp_id;
ALTER TABLE calls DROP COLUMN temp_id;
ALTER TABLE card_installment_settings DROP COLUMN temp_id;
ALTER TABLE card_installments_provider_details DROP COLUMN temp_id;
ALTER TABLE card_installments_store_details DROP COLUMN temp_id;
ALTER TABLE card_operation_cost DROP COLUMN temp_id;
ALTER TABLE card_payment_device DROP COLUMN temp_id;
ALTER TABLE cfop_data DROP COLUMN temp_id;
ALTER TABLE check_data DROP COLUMN temp_id;
ALTER TABLE client DROP COLUMN temp_id;
ALTER TABLE client_category DROP COLUMN temp_id;
ALTER TABLE client_category_price DROP COLUMN temp_id;
ALTER TABLE client_salary_history DROP COLUMN temp_id;
ALTER TABLE commission DROP COLUMN temp_id;
ALTER TABLE commission_source DROP COLUMN temp_id;
ALTER TABLE company DROP COLUMN temp_id;
ALTER TABLE contact_info DROP COLUMN temp_id;
ALTER TABLE cost_center DROP COLUMN temp_id;
ALTER TABLE cost_center_entry DROP COLUMN temp_id;
ALTER TABLE credit_card_data DROP COLUMN temp_id;
ALTER TABLE credit_card_details DROP COLUMN temp_id;
ALTER TABLE credit_check_history DROP COLUMN temp_id;
ALTER TABLE credit_provider DROP COLUMN temp_id;
ALTER TABLE delivery DROP COLUMN temp_id;
ALTER TABLE device_constant DROP COLUMN temp_id;
ALTER TABLE device_settings DROP COLUMN temp_id;
ALTER TABLE employee DROP COLUMN temp_id;
ALTER TABLE employee_role DROP COLUMN temp_id;
ALTER TABLE employee_role_history DROP COLUMN temp_id;
ALTER TABLE fiscal_book_entry DROP COLUMN temp_id;
ALTER TABLE fiscal_day_history DROP COLUMN temp_id;
ALTER TABLE fiscal_day_tax DROP COLUMN temp_id;
ALTER TABLE fiscal_sale_history DROP COLUMN temp_id;
ALTER TABLE image DROP COLUMN temp_id;
ALTER TABLE individual DROP COLUMN temp_id;
ALTER TABLE installed_plugin DROP COLUMN temp_id;
ALTER TABLE inventory DROP COLUMN temp_id;
ALTER TABLE inventory_item DROP COLUMN temp_id;
ALTER TABLE invoice_field DROP COLUMN temp_id;
ALTER TABLE invoice_layout DROP COLUMN temp_id;
ALTER TABLE invoice_printer DROP COLUMN temp_id;
ALTER TABLE loan DROP COLUMN temp_id;
ALTER TABLE loan_item DROP COLUMN temp_id;
ALTER TABLE login_user DROP COLUMN temp_id;
ALTER TABLE military_data DROP COLUMN temp_id;
ALTER TABLE parameter_data DROP COLUMN temp_id;
ALTER TABLE payment DROP COLUMN temp_id;
ALTER TABLE payment_category DROP COLUMN temp_id;
ALTER TABLE payment_change_history DROP COLUMN temp_id;
ALTER TABLE payment_comment DROP COLUMN temp_id;
ALTER TABLE payment_flow_history DROP COLUMN temp_id;
ALTER TABLE payment_group DROP COLUMN temp_id;
ALTER TABLE payment_method DROP COLUMN temp_id;
ALTER TABLE payment_renegotiation DROP COLUMN temp_id;
ALTER TABLE person DROP COLUMN temp_id;
ALTER TABLE product DROP COLUMN temp_id;
ALTER TABLE product_component DROP COLUMN temp_id;
ALTER TABLE product_history DROP COLUMN temp_id;
ALTER TABLE product_icms_template DROP COLUMN temp_id;
ALTER TABLE production_item DROP COLUMN temp_id;
ALTER TABLE production_item_quality_result DROP COLUMN temp_id;
ALTER TABLE production_material DROP COLUMN temp_id;
ALTER TABLE production_order DROP COLUMN temp_id;
ALTER TABLE production_produced_item DROP COLUMN temp_id;
ALTER TABLE production_service DROP COLUMN temp_id;
ALTER TABLE product_ipi_template DROP COLUMN temp_id;
ALTER TABLE product_manufacturer DROP COLUMN temp_id;
ALTER TABLE product_quality_test DROP COLUMN temp_id;
ALTER TABLE product_stock_item DROP COLUMN temp_id;
ALTER TABLE product_supplier_info DROP COLUMN temp_id;
ALTER TABLE product_tax_template DROP COLUMN temp_id;
ALTER TABLE profile_settings DROP COLUMN temp_id;
ALTER TABLE purchase_item DROP COLUMN temp_id;
ALTER TABLE purchase_order DROP COLUMN temp_id;
ALTER TABLE quotation DROP COLUMN temp_id;
ALTER TABLE quote_group DROP COLUMN temp_id;
ALTER TABLE receiving_order DROP COLUMN temp_id;
ALTER TABLE receiving_order_item DROP COLUMN temp_id;
ALTER TABLE returned_sale DROP COLUMN temp_id;
ALTER TABLE returned_sale_item DROP COLUMN temp_id;
ALTER TABLE sale DROP COLUMN temp_id;
ALTER TABLE sale_item DROP COLUMN temp_id;
ALTER TABLE sale_item_icms DROP COLUMN temp_id;
ALTER TABLE sale_item_ipi DROP COLUMN temp_id;
ALTER TABLE sales_person DROP COLUMN temp_id;
ALTER TABLE sellable DROP COLUMN temp_id;
ALTER TABLE sellable_category DROP COLUMN temp_id;
ALTER TABLE sellable_tax_constant DROP COLUMN temp_id;
ALTER TABLE sellable_unit DROP COLUMN temp_id;
ALTER TABLE service DROP COLUMN temp_id;
ALTER TABLE stock_decrease DROP COLUMN temp_id;
ALTER TABLE stock_decrease_item DROP COLUMN temp_id;
ALTER TABLE stock_transaction_history DROP COLUMN temp_id;
ALTER TABLE storable DROP COLUMN temp_id;
ALTER TABLE storable_batch DROP COLUMN temp_id;
ALTER TABLE supplier DROP COLUMN temp_id;
ALTER TABLE till DROP COLUMN temp_id;
ALTER TABLE till_entry DROP COLUMN temp_id;
ALTER TABLE transfer_order DROP COLUMN temp_id;
ALTER TABLE transfer_order_item DROP COLUMN temp_id;
ALTER TABLE transporter DROP COLUMN temp_id;
ALTER TABLE ui_field DROP COLUMN temp_id;
ALTER TABLE ui_form DROP COLUMN temp_id;
ALTER TABLE user_branch_access DROP COLUMN temp_id;
ALTER TABLE user_profile DROP COLUMN temp_id;
ALTER TABLE voter_data DROP COLUMN temp_id;
ALTER TABLE work_order DROP COLUMN temp_id;
ALTER TABLE work_order_category DROP COLUMN temp_id;
ALTER TABLE work_order_item DROP COLUMN temp_id;
ALTER TABLE work_order_package DROP COLUMN temp_id;
ALTER TABLE work_order_package_item DROP COLUMN temp_id;
ALTER TABLE work_permit_data DROP COLUMN temp_id;
