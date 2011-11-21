-- adicionando tempo de produção para um produto

ALTER TABLE product ADD COLUMN production_time integer DEFAULT 0;
ALTER TABLE product ADD COLUMN is_composed boolean DEFAULT FALSE;


UPDATE product set is_composed = 't'
    FROM product_component
    WHERE product_component.product_id = product.id;
