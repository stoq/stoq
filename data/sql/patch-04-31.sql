-- #5489: Indicar o número de parcelas máximas por operadora
ALTER TABLE credit_provider ALTER COLUMN max_installments SET DEFAULT 12;
UPDATE credit_provider SET max_installments = 12 WHERE max_installments IS NULL;
