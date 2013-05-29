-- Allow products that dont need stock managment

ALTER TABLE product ADD COLUMN manage_stock boolean DEFAULT True;

