-- Bug 4016 : Exibir imagem do produto em tamanho real

ALTER TABLE product ADD COLUMN full_image bytea;
UPDATE product SET full_image = image;

