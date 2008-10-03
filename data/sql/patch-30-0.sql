-- #3556: Erro ao imprimir relatório de pedido de compra
-- Add missing constraint in person_adapt_to_transporter table

-- Updates values from table first
UPDATE person_adapt_to_transporter
   SET freight_percentage = 0
 WHERE freight_percentage is null;

-- Add constraint now
   ALTER TABLE person_adapt_to_transporter
ADD CONSTRAINT positive_freight_percentage
         CHECK (freight_percentage >= 0);
