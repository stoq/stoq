-- #3785: Preciso de um campo de localizacao de um componente no estoque.

ALTER TABLE product ADD COLUMN location text;
