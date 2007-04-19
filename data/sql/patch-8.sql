ALTER TABLE transaction_entry
    ADD CONSTRAINT transaction_entry_user_id_fkey FOREIGN KEY
        (user_id) REFERENCES person_adapt_to_user (id),
    ADD CONSTRAINT transaction_entry_station_id_fkey FOREIGN KEY
        (station_id) REFERENCES branch_station (id);

ALTER TABLE person_adapt_to_client
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
    ADD CONSTRAINT positive_days_late
        CHECK (days_late >= 0);

ALTER TABLE person_adapt_to_credit_provider
    ADD CONSTRAINT valid_provider_type
        CHECK (provider_type >= 0 AND provider_type < 2);

ALTER TABLE person_adapt_to_individual
    ADD CONSTRAINT valid_marital_status
        CHECK (marital_status >= 0 AND marital_status < 6),
    ADD CONSTRAINT valid_gender
        CHECK (gender >= 0 AND gender < 2);

ALTER TABLE person_adapt_to_employee
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
    ADD CONSTRAINT positive_dependent_person_number
        CHECK (dependent_person_number >= 0);

ALTER TABLE bank_account
    ADD CONSTRAINT positive_bank_id
        CHECK (bank_id >= 0);

ALTER TABLE person_adapt_to_sales_person
    ADD CONSTRAINT positive_comission
        CHECK (comission >= 0),
    ADD CONSTRAINT check_valid_comission_type
        CHECK (comission_type >= 0 AND comission_type < 7);

ALTER TABLE person_adapt_to_supplier
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 3);

ALTER TABLE product_supplier_info
    ADD CONSTRAINT positive_base_cost
        CHECK (base_cost >= 0),
    ADD CONSTRAINT positive_icms
        CHECK (icms >= 0);

ALTER TABLE base_sellable_info
    ADD CONSTRAINT positive_price
        CHECK (price >= 0);

ALTER TABLE on_sale_info
    ADD CONSTRAINT positive_on_sale_price
        CHECK (on_sale_price >= 0);

ALTER TABLE sellable_unit
    ADD CONSTRAINT positive_unit_index
        CHECK (unit_index >= 0);

ALTER TABLE sellable_tax_constant
    ADD CONSTRAINT valid_tax_type
        CHECK (tax_type >= 41 AND tax_type < 46);

ALTER TABLE asellable
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
    ADD CONSTRAINT positive_cost
        CHECK (cost >= 0);

ALTER TABLE purchase_order
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 5),
    ADD CONSTRAINT valid_freight_type
        CHECK (freight_type >= 0 AND freight < 2),
    ADD CONSTRAINT positive_freight
        CHECK (freight >= 0),
    ADD CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0),
    ADD CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0);

ALTER TABLE purchase_item
    ADD CONSTRAINT positive_base_cost
        CHECK (base_cost >= 0),
    ADD CONSTRAINT positive_cost
        CHECK (cost >= 0);

ALTER TABLE till
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 3),
    ADD CONSTRAINT positive_initial_cash_amount
        CHECK (initial_cash_amount >= 0),
    ADD CONSTRAINT positive_final_cash_amount
        CHECK (final_cash_amount >= 0);

ALTER TABLE sale
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 5),
    ADD CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    ADD CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0);

ALTER TABLE asellable_item
    ADD CONSTRAINT positive_base_price
        CHECK (base_price >= 0),
    ADD CONSTRAINT positive_price
        CHECK (price >= 0);

ALTER TABLE address
    ADD CONSTRAINT positive_number
        CHECK (number > 0);

ALTER TABLE abstract_payment_group
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 4),
    ADD CONSTRAINT positive_default_method
        CHECK (default_method >= 0),
    ADD CONSTRAINT positive_installments_number
        CHECK (installments_number > 0);

ALTER TABLE bill_check_group_data
    ADD CONSTRAINT positive_installments_number
        CHECK (installments_number > 0);

ALTER TABLE card_installments_provider_details
    ADD CONSTRAINT positive_max_installments_number
        CHECK (max_installments_number > 0);

ALTER TABLE card_installments_store_details
     ADD CONSTRAINT positive_max_installments_number
        CHECK (max_installments_number > 0);

ALTER TABLE payment
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 6),
    ADD CONSTRAINT positive_paid_value
        CHECK (paid_value > 0),
    ADD CONSTRAINT positive_base_value
        CHECK (base_value >= 0),
    ADD CONSTRAINT positive_value
        CHECK (value >= 0),
    ADD CONSTRAINT positive_discount
        CHECK (discount >= 0);

ALTER TABLE credit_provider_group_data
    ADD CONSTRAINT positive_installments_number
        CHECK (installments_number > 0);

ALTER TABLE debit_card_details
    ADD CONSTRAINT positive_receive_days
        CHECK (receive_days >= 0);

ALTER TABLE device_settings
    ADD CONSTRAINT valid_type
        CHECK (type >= 0 AND type < 4),
    ADD CONSTRAINT valid_device
        CHECK (device >= 0 AND device < 4);

ALTER TABLE device_constant
    ADD CONSTRAINT valid_constant_type
        CHECK (constant_type >= 0 AND constant_type < 3),
    ADD CONSTRAINT positive_constant_value
        CHECK (constant_value >= 0),
    ADD CONSTRAINT valid_constant_enum
        CHECK ((constant_enum >= 0 AND constant_enum < 8) OR
                (constant_enum >= 20 AND constant_enum < 25) OR
                (constant_enum >= 40 AND constant_enum < 46));

ALTER TABLE finance_details
    ADD CONSTRAINT positive_receive_days
        CHECK (receive_days >= 0);

ALTER TABLE bill_p_m
    ADD CONSTRAINT positive_max_installments_number
        CHECK (max_installments_number > 0);

ALTER TABLE check_p_m
    ADD CONSTRAINT positive_max_installments_number
        CHECK (max_installments_number > 0);

ALTER TABLE receiving_order
    ADD CONSTRAINT valid_status
        CHECK (status >= 0 AND status < 2),
    ADD CONSTRAINT positive_freight_total
        CHECK (freight_total >= 0),
    ADD CONSTRAINT positive_surcharge_value
        CHECK (surcharge_value >= 0),
    ADD CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    ADD CONSTRAINT positive_invoice_total
        CHECK (invoice_total >= 0);

ALTER TABLE receiving_order_item
    ADD CONSTRAINT positive_cost
        CHECK (cost >= 0);

ALTER TABLE abstract_fiscal_book_entry
    ADD CONSTRAINT positive_invoice_number
        CHECK (invoice_number >= 0);

ALTER TABLE system_table
    ADD CONSTRAINT positive_patchlevel
        CHECK (patchlevel >= 0),
    ADD CONSTRAINT positive_generation
        CHECK (generation >= 0);
