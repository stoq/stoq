ALTER TABLE card_payment_device ADD supplier_id uuid REFERENCES supplier(id) ON UPDATE CASCADE;
