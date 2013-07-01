-- #5549: Add is_adjusted flag on inventory_item
ALTER TABLE inventory_item ADD COLUMN is_adjusted boolean NOT NULL DEFAULT false;

-- Until now, an inventory_item was considered adjusted if it had a cfop
UPDATE inventory_item SET is_adjusted = true
    WHERE inventory_item.cfop_data_id IS NOT NULL;

-- Add responsible to inventory
ALTER TABLE inventory ADD COLUMN responsible_id uuid
    REFERENCES login_user(id) ON UPDATE CASCADE;
UPDATE inventory SET responsible_id = transaction_entry.user_id
    FROM transaction_entry WHERE inventory.te_id = transaction_entry.id;
-- Add not NULL after the migration above
ALTER TABLE inventory ALTER COLUMN responsible_id SET NOT NULL;

-- Add counted_quantity column on inventory_item
ALTER TABLE inventory_item ADD COLUMN counted_quantity numeric(20, 3)
    CONSTRAINT positive_counted_quantity CHECK (counted_quantity >= 0);
UPDATE inventory_item SET counted_quantity = actual_quantity;
-- On opened/cancelled (status 0/2) inventories, set actual_quantity to null
-- since that the new behaviour (actual_quantity will be updated on adjustment)
UPDATE inventory_item SET actual_quantity = NULL FROM inventory WHERE
    inventory.id = inventory_item.inventory_id AND inventory.status IN (0, 2);
