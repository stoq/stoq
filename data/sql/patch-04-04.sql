-- #5358: Adicionar pagamentos a Saida Manual

ALTER TABLE stock_decrease ADD COLUMN group_id bigint
    REFERENCES payment_group(id) ON UPDATE CASCADE;
ALTER TABLE stock_decrease_item ADD COLUMN cost numeric(20, 8) DEFAULT 0;
