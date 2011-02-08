-- Removendo ValidatableDomain

DELETE FROM receiving_order_item
    WHERE receiving_order_id IN
        (SELECT id FROM receiving_order WHERE is_valid_model = 'f');

DELETE FROM delivery_item WHERE delivery_id IN
    (SELECT sale_item_adapt_to_delivery.id
       FROM sale_item_adapt_to_delivery, sale_item, sale
      WHERE sale_item.sale_id = sale.id
        AND sale_item_adapt_to_delivery.original_id = sale_item.id
        AND sale.is_valid_model = 'f');

DELETE FROM sale_item_adapt_to_delivery WHERE original_id IN
    (SELECT sale_item.id FROM sale_item, sale
      WHERE sale_item.sale_id = sale.id
        AND sale.is_valid_model = 'f');

DELETE FROM sale_item
    WHERE sale_id IN
        (SELECT id FROM sale WHERE is_valid_model = 'f');

DELETE FROM purchase_item
    WHERE order_id IN
        (SELECT id FROM purchase_order WHERE is_valid_model = 'f');

DELETE FROM sale where is_valid_model = 'f';
DELETE FROM purchase_order where is_valid_model = 'f';
DELETE FROM receiving_order where is_valid_model = 'f';

ALTER TABLE sale DROP COLUMN is_valid_model;
ALTER TABLE purchase_order DROP COLUMN is_valid_model;
ALTER TABLE receiving_order DROP COLUMN is_valid_model;
