-- #3104: No wizard do warehouse em seu terceiro passo criar campo de desconto, seguro e despesas acessórias

--
-- Adding columns secure_value and expense_value
--
ALTER TABLE receiving_order ADD COLUMN secure_value numeric(10,2)
    CONSTRAINT positive_secure_value CHECK (secure_value >= 0);
ALTER TABLE receiving_order ADD COLUMN expense_value numeric(10,2)
    CONSTRAINT positive_expense_value CHECK (expense_value >= 0);
