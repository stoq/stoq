-- #3773: Deve ser possível cancelar um inventário aberto

ALTER TABLE inventory DROP CONSTRAINT valid_status;

ALTER TABLE inventory ADD CONSTRAINT valid_status
    CHECK (status >= 0 AND status < 3);
