-- #3526: Erro na geração de comissões ao retornar uma venda.
ALTER TABLE commission DROP CONSTRAINT positive_value;
