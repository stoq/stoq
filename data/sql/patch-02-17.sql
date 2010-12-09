-- usar 3 casas decimais quantidade de produtos na venda

ALTER TABLE sale_item ALTER COLUMN quantity TYPE numeric(10, 3);
