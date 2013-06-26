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
