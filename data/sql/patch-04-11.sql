-- #5301: Permitir cadastrar mais de 1 telefone

ALTER TABLE liaison
    RENAME TO contact_info;

ALTER TABLE contact_info
    RENAME COLUMN name TO description;

ALTER TABLE contact_info
    RENAME COLUMN phone_number TO contact_info;
