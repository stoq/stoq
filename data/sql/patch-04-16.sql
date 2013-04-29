-- #5455: Migrate quantity_decreased for renegotiated sales.
-- This status was missing from the patch 04-12
-- the sale status 7 is the RENEGOTIATED status

UPDATE sale_item
    SET quantity_decreased = sale_item.quantity - returned.quantity
    FROM sale,
        (SELECT sale_item_id, sum(quantity) as quantity
         FROM returned_sale_item GROUP BY sale_item_id) AS returned
    WHERE returned.sale_item_id = sale_item.id
        AND sale_item.sale_id = sale.id
        AND sale.status = 7;
