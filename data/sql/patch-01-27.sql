-- #3964: Adicao de coluna "Conferido por" no dialogo de recebimento de compras de estoque.

ALTER TABLE purchase_order
    ADD COLUMN responsible_id bigint REFERENCES person_adapt_to_user(id);
