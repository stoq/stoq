-- We need to drop this rule before, other else it wont update it properly
DROP RULE update_te ON purchase_order;

UPDATE purchase_order SET open_date = transaction_entry.te_time
    FROM transaction_entry
        WHERE transaction_entry.id = purchase_order.te_id AND purchase_order.open_date is NULL;

CREATE RULE update_te AS
    ON UPDATE TO purchase_order DO  SELECT update_te(old.te_id) AS update_te;

ALTER TABLE purchase_order ALTER COLUMN open_date SET NOT NULL;
