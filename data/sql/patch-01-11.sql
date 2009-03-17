-- #3604: Dados como part-number e fabricantes devem ser inseridos no cadastro
-- de produtos.

ALTER TABLE product ADD COLUMN part_number text, ADD COLUMN manufacturer text;
