-- #5549: Add is_adjusted flag on inventory_item
ALTER TABLE inventory_item ADD COLUMN is_adjusted boolean NOT NULL DEFAULT false;

-- Until now, an inventory_item was considered adjusted if it had a cfop
UPDATE inventory_item SET is_adjusted = true
    WHERE inventory_item.cfop_data_id IS NOT NULL;
