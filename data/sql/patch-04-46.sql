-- Adjust quantity_decreased on sale_item/work_order_item since on sometimes
-- the column was not being updated for services and products without storable

-- sale.status (1, 2, 5, 7) == (CONFIRMED, PAID, RETURNED, RENEGOTIATED)
UPDATE sale_item
    SET quantity_decreased = sale_item.quantity - returned.quantity
    FROM sale,
        (SELECT sale_item_id, sum(quantity) as quantity
         FROM returned_sale_item GROUP BY sale_item_id) AS returned
    WHERE returned.sale_item_id = sale_item.id
        AND sale_item.sale_id = sale.id
        AND sale.status IN (1, 2, 5, 7);

-- sale.status 3 == CANCELLED
UPDATE sale_item
    SET quantity_decreased = 0
    FROM sale
    WHERE sale_item.sale_id = sale.id AND sale.status = 3;
