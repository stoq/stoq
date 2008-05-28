-- #3418: Cancelamento de Cupom Fiscal deve cancelar qualquer tipo de lançamento.

ALTER TABLE ecf_printer ADD COLUMN user_number int;
ALTER TABLE ecf_printer ADD COLUMN register_date timestamp;
ALTER TABLE ecf_printer ADD COLUMN register_cro int;
