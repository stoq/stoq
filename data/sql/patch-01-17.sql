-- #3691: usar 4 casas decimais em preço de produto.

 ALTER TABLE sellable ALTER COLUMN cost TYPE numeric(10, 4);
 ALTER TABLE purchase_item ALTER COLUMN base_cost TYPE numeric(10, 4);
 ALTER TABLE purchase_item ALTER COLUMN cost TYPE numeric(10, 4);
 ALTER TABLE receiving_order_item ALTER COLUMN cost TYPE numeric(10, 4);
 ALTER TABLE inventory_item ALTER COLUMN product_cost TYPE numeric(10, 4);
 ALTER TABLE product_supplier_info ALTER COLUMN base_cost TYPE numeric(10, 4);
