--3813: Make a new schema generation

-- last schema adjustments (missing in the other patches)

DROP VIEW IF EXISTS till_fiscal_operations_view;

ALTER TABLE person_adapt_to_transporter
	ALTER COLUMN freight_percentage SET NOT NULL;

-- Basically, we will rename all the old constraints, except the primary key
-- constraints. So, difference between a updated database with a new database
-- will be that constraint names.

ALTER TABLE commission_source
    ADD CONSTRAINT commission_source_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE commission_source
    ADD CONSTRAINT commission_source_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE commission
    ADD CONSTRAINT commission_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE commission
    ADD CONSTRAINT commission_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE device_constant
	DROP CONSTRAINT valid_constant_enum;

ALTER TABLE device_constant
	ADD CONSTRAINT device_constant_constant_enum_check CHECK (((((constant_enum >= 0) AND (constant_enum < 8)) OR ((constant_enum >= 20) AND (constant_enum < 25))) OR ((constant_enum >= 40) AND (constant_enum < 46))));

ALTER TABLE fiscal_book_entry
	DROP CONSTRAINT abstract_fiscal_book_entry_branch_id_fkey;

ALTER TABLE fiscal_book_entry
	DROP CONSTRAINT abstract_fiscal_book_entry_cfop_id_fkey;

ALTER TABLE fiscal_book_entry
	DROP CONSTRAINT abstract_fiscal_book_entry_drawee_id_fkey;

ALTER TABLE fiscal_book_entry
	DROP CONSTRAINT abstract_fiscal_book_entry_payment_group_id_fkey;

ALTER TABLE fiscal_book_entry
	DROP CONSTRAINT abstract_fiscal_book_entry_te_created_id_fkey;

ALTER TABLE fiscal_book_entry
	DROP CONSTRAINT abstract_fiscal_book_entry_te_modified_id_fkey;

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES person_adapt_to_branch(id);

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_cfop_id_fkey FOREIGN KEY (cfop_id) REFERENCES cfop_data(id);

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_drawee_id_fkey FOREIGN KEY (drawee_id) REFERENCES person(id);

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_payment_group_id_fkey FOREIGN KEY (payment_group_id) REFERENCES payment_group(id);

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE fiscal_book_entry
	ADD CONSTRAINT fiscal_book_entry_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE fiscal_sale_history
	DROP CONSTRAINT paulista_invoice_te_created_id_key;

ALTER TABLE fiscal_sale_history
	DROP CONSTRAINT paulista_invoice_te_modified_id_key;

ALTER TABLE fiscal_sale_history
	DROP CONSTRAINT paulista_invoice_sale_id_fkey;

ALTER TABLE fiscal_sale_history
	DROP CONSTRAINT paulista_invoice_te_created_id_fkey;

ALTER TABLE fiscal_sale_history
	DROP CONSTRAINT paulista_invoice_te_modified_id_fkey;

ALTER TABLE fiscal_sale_history
	ADD CONSTRAINT fiscal_sale_history_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE fiscal_sale_history
	ADD CONSTRAINT fiscal_sale_history_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE fiscal_sale_history
	ADD CONSTRAINT fiscal_sale_history_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sale(id);

ALTER TABLE fiscal_sale_history
	ADD CONSTRAINT fiscal_sale_history_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE fiscal_sale_history
	ADD CONSTRAINT fiscal_sale_history_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE payment
	DROP CONSTRAINT positive_paid_value;

ALTER TABLE payment
	ADD CONSTRAINT positive_paid_value CHECK ((paid_value >= (0)::numeric));

ALTER TABLE payment_change_history
	DROP CONSTRAINT payment_due_date_info_te_created_id_key;

ALTER TABLE payment_change_history
	DROP CONSTRAINT payment_due_date_info_te_modified_id_key;

ALTER TABLE payment_change_history
	DROP CONSTRAINT payment_due_date_info_payment_id_fkey;

ALTER TABLE payment_change_history
	DROP CONSTRAINT payment_due_date_info_te_created_id_fkey;

ALTER TABLE payment_change_history
	DROP CONSTRAINT payment_due_date_info_te_modified_id_fkey;

ALTER TABLE payment_change_history
	ADD CONSTRAINT payment_change_history_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE payment_change_history
	ADD CONSTRAINT payment_change_history_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE payment_change_history
	ADD CONSTRAINT payment_change_history_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment(id);

ALTER TABLE payment_change_history
	ADD CONSTRAINT payment_change_history_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE payment_change_history
	ADD CONSTRAINT payment_change_history_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE payment_group
	DROP CONSTRAINT abstract_payment_group_te_created_id_key;

ALTER TABLE payment_group
	DROP CONSTRAINT abstract_payment_group_te_modified_id_key;

ALTER TABLE payment_group
	DROP CONSTRAINT abstract_payment_group_payer_id_fkey;

ALTER TABLE payment_group
	DROP CONSTRAINT abstract_payment_group_recipient_id_fkey;

ALTER TABLE payment_group
	DROP CONSTRAINT abstract_payment_group_te_created_id_fkey;

ALTER TABLE payment_group
	DROP CONSTRAINT abstract_payment_group_te_modified_id_fkey;

ALTER TABLE payment_group
	ADD CONSTRAINT payment_group_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE payment_group
	ADD CONSTRAINT payment_group_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE payment_group
	ADD CONSTRAINT payment_group_payer_id_fkey FOREIGN KEY (payer_id) REFERENCES person(id);

ALTER TABLE payment_group
	ADD CONSTRAINT payment_group_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES person(id);

ALTER TABLE payment_group
	ADD CONSTRAINT payment_group_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE payment_group
	ADD CONSTRAINT payment_group_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE payment_destination
	ADD CONSTRAINT payment_destination_te_created_id_key UNIQUE (te_created_id);

 ALTER TABLE payment_destination
	ADD CONSTRAINT payment_destination_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE payment_method
	DROP CONSTRAINT apayment_method_daily_penalty_check;

ALTER TABLE payment_method
	DROP CONSTRAINT apayment_method_method_name_key;

ALTER TABLE payment_method
	DROP CONSTRAINT apayment_method_destination_id_fkey;

ALTER TABLE payment_method
	DROP CONSTRAINT apayment_method_te_created_id_fkey;

ALTER TABLE payment_method
	DROP CONSTRAINT apayment_method_te_modified_id_fkey;

ALTER TABLE payment_method
	ADD CONSTRAINT positive_max_installments CHECK ((max_installments > 0));

ALTER TABLE payment_method
	ADD CONSTRAINT valid_daily_penalty CHECK (((daily_penalty >= (0)::numeric) AND (daily_penalty <= (100)::numeric)));

ALTER TABLE payment_method
	ADD CONSTRAINT payment_method_method_name_key UNIQUE (method_name);

ALTER TABLE payment_method
	ADD CONSTRAINT payment_method_destination_id_fkey FOREIGN KEY (destination_id) REFERENCES payment_destination(id);

ALTER TABLE payment_method
	ADD CONSTRAINT payment_method_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE payment_method
	ADD CONSTRAINT payment_method_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE payment_method
	ADD CONSTRAINT payment_method_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE payment_method
	ADD CONSTRAINT payment_method_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE product_history
	DROP CONSTRAINT positive_quantity_retended;

ALTER TABLE product_history
	ADD CONSTRAINT positive_quantity_retained CHECK ((quantity_retained >= (0)::numeric));

ALTER TABLE product_stock_item
	DROP CONSTRAINT abstract_stock_item_branch_id_fkey;

ALTER TABLE product_stock_item
	DROP CONSTRAINT abstract_stock_item_storable_id_fkey;

ALTER TABLE product_stock_item
	DROP CONSTRAINT abstract_stock_item_te_created_id_fkey;

ALTER TABLE product_stock_item
	DROP CONSTRAINT abstract_stock_item_te_modified_id_fkey;

ALTER TABLE product_stock_item
	ADD CONSTRAINT product_stock_item_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES person_adapt_to_branch(id);

ALTER TABLE product_stock_item
	ADD CONSTRAINT product_stock_item_storable_id_fkey FOREIGN KEY (storable_id) REFERENCES product_adapt_to_storable(id);

ALTER TABLE product_stock_item
	ADD CONSTRAINT product_stock_item_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE product_stock_item
	ADD CONSTRAINT product_stock_item_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE product_stock_item
	ADD CONSTRAINT product_stock_item_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE product_stock_item
	ADD CONSTRAINT product_stock_item_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE quotation
	DROP CONSTRAINT purchase_order_adapt_to_quote_te_created_id_key;

ALTER TABLE quotation
	DROP CONSTRAINT purchase_order_adapt_to_quote_te_modified_id_key;

ALTER TABLE quotation
	DROP CONSTRAINT purchase_order_adapt_to_quote_group_id_fkey;

ALTER TABLE quotation
	DROP CONSTRAINT purchase_order_adapt_to_quote_original_id_fkey;

ALTER TABLE quotation
	DROP CONSTRAINT purchase_order_adapt_to_quote_te_created_id_fkey;

ALTER TABLE quotation
	DROP CONSTRAINT purchase_order_adapt_to_quote_te_modified_id_fkey;

ALTER TABLE quotation
	ADD CONSTRAINT quotation_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE quotation
	ADD CONSTRAINT quotation_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE quotation
	ADD CONSTRAINT quotation_group_id_fkey FOREIGN KEY (group_id) REFERENCES quote_group(id);

ALTER TABLE quotation
	ADD CONSTRAINT quotation_purchase_id_fkey FOREIGN KEY (purchase_id) REFERENCES purchase_order(id);

ALTER TABLE quotation
	ADD CONSTRAINT quotation_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE quotation
	ADD CONSTRAINT quotation_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE receiving_order
	DROP CONSTRAINT positive_invoice_total;

ALTER TABLE sale_item
	DROP CONSTRAINT asellable_item_sale_id_fkey;

ALTER TABLE sale_item
	DROP CONSTRAINT asellable_item_sellable_id_fkey;

ALTER TABLE sale_item
	DROP CONSTRAINT asellable_item_te_created_id_fkey;

ALTER TABLE sale_item
	DROP CONSTRAINT asellable_item_te_modified_id_fkey;

ALTER TABLE sale_item
	ADD CONSTRAINT sale_item_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES sale(id);

ALTER TABLE sale_item
	ADD CONSTRAINT sale_item_sellable_id_fkey FOREIGN KEY (sellable_id) REFERENCES sellable(id);

ALTER TABLE sale_item
	ADD CONSTRAINT sale_item_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE sale_item
	ADD CONSTRAINT sale_item_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE sale_item
	ADD CONSTRAINT sale_item_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE sale_item
	ADD CONSTRAINT sale_item_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE sale_item_adapt_to_delivery
	DROP CONSTRAINT service_sellable_item_adapt_to_delivery_te_created_id_key;

ALTER TABLE sale_item_adapt_to_delivery
	DROP CONSTRAINT service_sellable_item_adapt_to_delivery_te_modified_id_key;

ALTER TABLE sale_item_adapt_to_delivery
	DROP CONSTRAINT service_sellable_item_adapt_to_delivery_original_id_fkey;

ALTER TABLE sale_item_adapt_to_delivery
	DROP CONSTRAINT service_sellable_item_adapt_to_delivery_te_created_id_fkey;

ALTER TABLE sale_item_adapt_to_delivery
	DROP CONSTRAINT service_sellable_item_adapt_to_delivery_te_modified_id_fkey;

ALTER TABLE sale_item_adapt_to_delivery
	ADD CONSTRAINT sale_item_adapt_to_delivery_original_id_key UNIQUE (original_id);

ALTER TABLE sale_item_adapt_to_delivery
	ADD CONSTRAINT sale_item_adapt_to_delivery_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE sale_item_adapt_to_delivery
	ADD CONSTRAINT sale_item_adapt_to_delivery_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE sale_item_adapt_to_delivery
	ADD CONSTRAINT sale_item_adapt_to_delivery_original_id_fkey FOREIGN KEY (original_id) REFERENCES sale_item(id);

ALTER TABLE sale_item_adapt_to_delivery
	ADD CONSTRAINT sale_item_adapt_to_delivery_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE sale_item_adapt_to_delivery
	ADD CONSTRAINT sale_item_adapt_to_delivery_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE sellable
	DROP CONSTRAINT asellable_base_sellable_info_id_fkey;

ALTER TABLE sellable
	DROP CONSTRAINT asellable_category_id_fkey;

ALTER TABLE sellable
	DROP CONSTRAINT asellable_on_sale_info_id_fkey;

ALTER TABLE sellable
	DROP CONSTRAINT asellable_tax_constant_id_fkey;

ALTER TABLE sellable
	DROP CONSTRAINT asellable_te_created_id_fkey;

ALTER TABLE sellable
	DROP CONSTRAINT asellable_te_modified_id_fkey;

ALTER TABLE sellable
	DROP CONSTRAINT asellable_unit_id_fkey;

ALTER TABLE sellable
	ADD CONSTRAINT sellable_base_sellable_info_id_fkey FOREIGN KEY (base_sellable_info_id) REFERENCES base_sellable_info(id);

ALTER TABLE sellable
	ADD CONSTRAINT sellable_category_id_fkey FOREIGN KEY (category_id) REFERENCES sellable_category(id);

ALTER TABLE sellable
	ADD CONSTRAINT sellable_on_sale_info_id_fkey FOREIGN KEY (on_sale_info_id) REFERENCES on_sale_info(id);

ALTER TABLE sellable
	ADD CONSTRAINT sellable_tax_constant_id_fkey FOREIGN KEY (tax_constant_id) REFERENCES sellable_tax_constant(id);

ALTER TABLE sellable
	ADD CONSTRAINT sellable_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE sellable
	ADD CONSTRAINT sellable_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE sellable
	ADD CONSTRAINT sellable_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES sellable_unit(id);

ALTER TABLE sellable
    ADD CONSTRAINT sellable_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE sellable
    ADD CONSTRAINT sellable_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE sellable_category
	DROP CONSTRAINT asellable_category_category_id_fkey;

ALTER TABLE sellable_category
	DROP CONSTRAINT asellable_category_te_created_id_fkey;

ALTER TABLE sellable_category
	DROP CONSTRAINT asellable_category_te_modified_id_fkey;

ALTER TABLE sellable_category
	ADD CONSTRAINT sellable_category_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE sellable_category
	ADD CONSTRAINT sellable_category_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE sellable_category
	ADD CONSTRAINT sellable_category_category_id_fkey FOREIGN KEY (category_id) REFERENCES sellable_category(id);

ALTER TABLE sellable_category
	ADD CONSTRAINT sellable_category_te_created_id_fkey FOREIGN KEY (te_created_id) REFERENCES transaction_entry(id);

ALTER TABLE sellable_category
	ADD CONSTRAINT sellable_category_te_modified_id_fkey FOREIGN KEY (te_modified_id) REFERENCES transaction_entry(id);

ALTER TABLE transfer_order
	ADD CONSTRAINT transfer_order_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE transfer_order
	ADD CONSTRAINT transfer_order_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE transfer_order_item
	ADD CONSTRAINT transfer_order_item_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE transfer_order_item
	ADD CONSTRAINT transfer_order_item_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE invoice_layout
	ADD CONSTRAINT invoice_layout_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE invoice_layout
	ADD CONSTRAINT invoice_layout_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE invoice_field
	ADD CONSTRAINT invoice_field_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE invoice_field
	ADD CONSTRAINT invoice_field_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE invoice_printer
	ADD CONSTRAINT invoice_printer_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE invoice_printer
	ADD CONSTRAINT invoice_printer_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE inventory
	ADD CONSTRAINT inventory_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE inventory
	ADD CONSTRAINT inventory_te_modified_id_key UNIQUE (te_modified_id);

ALTER TABLE inventory_item
	ADD CONSTRAINT inventory_item_te_created_id_key UNIQUE (te_created_id);

ALTER TABLE inventory_item
	ADD CONSTRAINT inventory_item_te_modified_id_key UNIQUE (te_modified_id);
