-- 5374: Registrar se o boleto de pagamento já foi recebido

ALTER TABLE payment
	ADD COLUMN bill_received BOOLEAN DEFAULT FALSE;
