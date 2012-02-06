-- #4850: Remove IInPaymente and IOutPayment
ALTER TABLE payment ADD COLUMN payment_type integer;

-- This is correct, we used to have a join to represent a boolean!
UPDATE payment SET payment_type = 0 FROM payment_adapt_to_in_payment
 WHERE payment_adapt_to_in_payment.original_id = payment.id;
UPDATE payment SET payment_type = 1 FROM payment_adapt_to_out_payment
 WHERE payment_adapt_to_out_payment.original_id = payment.id;

DROP TABLE payment_adapt_to_out_payment;
DROP TABLE payment_adapt_to_in_payment;

-- This should be safe and is needed to be able to add a proper
-- constraint. This will apply to Payments created without the
-- addFacet() call afterwards, these payments will never show up
-- anywhere.
DELETE FROM payment WHERE payment_type NOT IN (0, 1);
ALTER TABLE payment ADD CONSTRAINT valid_payment_type
     CHECK (payment_type >= 0 AND payment_type < 2);
