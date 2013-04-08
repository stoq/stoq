-- 5412: Add quantity_decreased column on sale_item
-- sale status (1, 2) are (CONFIRMED, PAID)

ALTER TABLE sale_item
ADD COLUMN quantity_decreased numeric(20, 3) DEFAULT 0
    CONSTRAINT valid_quantity_decreased CHECK (quantity_decreased <= quantity);

UPDATE sale_item
SET quantity_decreased = sale_item.quantity - returned.quantity
FROM sale,
    (SELECT sale_item_id, sum(quantity) as quantity
     FROM returned_sale_item GROUP BY sale_item_id) AS returned
WHERE returned.sale_item_id = sale_item.id
    AND sale_item.sale_id = sale.id
    AND sale.status IN (1,2);
