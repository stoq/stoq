-- Fazendo merge das tabelas on_sale_info e base_sellable_info dentro de
-- sellable.

-- base_sellable_info
ALTER TABLE sellable ADD COLUMN base_price numeric(20, 2)
        CONSTRAINT positive_price CHECK (base_price >= 0);
ALTER TABLE sellable ADD COLUMN description text;
ALTER TABLE sellable ADD COLUMN max_discount numeric(10, 2);
ALTER TABLE sellable ADD COLUMN commission numeric(10, 2);

-- on_sale_info
ALTER TABLE sellable ADD COLUMN on_sale_price numeric(20,2)
        CONSTRAINT positive_on_sale_price CHECK (on_sale_price >= 0);
ALTER TABLE sellable ADD COLUMN on_sale_start_date timestamp;
ALTER TABLE sellable ADD COLUMN on_sale_end_date timestamp;


-- UPDATE
UPDATE sellable
    SET base_price = b.price,
        description = b.description,
        max_discount = b.max_discount,
        commission = b.commission
    FROM base_sellable_info b
    WHERE b.id = base_sellable_info_id;

UPDATE sellable
    SET on_sale_price = o.on_sale_price,
        on_sale_start_date = o.on_sale_start_date,
        on_sale_end_date = o.on_sale_end_date
    FROM on_sale_info o
    WHERE o.id = on_sale_info_id;

-- drop old tables
ALTER TABLE sellable DROP COLUMN base_sellable_info_id;
DROP TABLE base_sellable_info;

ALTER TABLE sellable DROP COLUMN on_sale_info_id;
DROP TABLE on_sale_info;
