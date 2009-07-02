-- #3337: No recebimento de uma compra ao adicionarmos frete temos duas situacoes distintas.

ALTER TABLE purchase_order RENAME COLUMN freight TO expected_freight;
ALTER TABLE purchase_order DROP CONSTRAINT positive_freight;
ALTER TABLE purchase_order ADD CONSTRAINT positive_expected_freight CHECK (expected_freight >= 0);
