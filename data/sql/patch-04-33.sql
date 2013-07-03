-- #5488: Indicar qual o disposivivo padrão para uma operadora
ALTER TABLE credit_provider ADD default_device_id uuid REFERENCES card_payment_device(id) ON UPDATE CASCADE;
