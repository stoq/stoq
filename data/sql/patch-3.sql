-- #3282: Separate Till and Payments
ALTER TABLE till_entry ALTER COLUMN till_id SET NOT NULL;
ALTER TABLE till_entry DROP COLUMN payment_group_id CASCADE;
ALTER TABLE till_entry ADD COLUMN payment_id integer;
DROP TABLE till_adapt_to_payment_group;
DELETE FROM abstract_payment_group where child_name = 'TillAdaptToPaymentGroup';
