-- #3517: o selecionar o parametro de "confirmar venda no caixa" um erro
-- é gerado

-- Remove client_role column from sale
ALTER TABLE sale DROP COLUMN client_role;
