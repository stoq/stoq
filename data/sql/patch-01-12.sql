-- 3612: Implementar quantidade mínima de compra.

ALTER TABLE product_supplier_info
    ADD COLUMN minimum_purchase numeric(10,2) DEFAULT 1;
