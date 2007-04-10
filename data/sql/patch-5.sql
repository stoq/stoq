-- #3297: Remove ReceivingOrder IPaymentGroup implementation
DROP TABLE receiving_order_adapt_to_payment_group;
DELETE FROM abstract_payment_group where child_name = 'ReceivingOrderAdaptToPaymentGroup';
ALTER TABLE receiving_order ALTER COLUMN purchase_id SET NOT NULL;
