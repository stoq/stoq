-- # Gerenciamento de items de producao.

ALTER TABLE production_item ADD COLUMN produced numeric(10, 2) DEFAULT 0
    CONSTRAINT positive_produced CHECK (produced >= 0);

ALTER TABLE production_item ADD COLUMN lost numeric(10, 2) DEFAULT 0
    CONSTRAINT positive_lost CHECK (lost >= 0);
