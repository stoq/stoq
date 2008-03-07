-- #3418: Cancelamento de Cupom Fiscal deve cancelar qualquer tipo de lançamento.

ALTER TABLE ecf_printer
    ADD COLUMN last_sale_id bigint UNIQUE REFERENCES sale(id);
ALTER TABLE ecf_printer
    ADD COLUMN last_till_entry_id bigint UNIQUE REFERENCES till_entry(id);
