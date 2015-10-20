CREATE TYPE product_pis_template_calculo AS ENUM ('percentage', 'value');
CREATE TYPE product_cofins_template_calculo AS ENUM ('percentage', 'value');
CREATE TYPE product_ipi_template_calculo AS ENUM ('aliquot', 'unit');
CREATE TYPE product_tax_template_tax_type AS ENUM ('icms', 'ipi', 'pis', 'cofins');

-- Creating table to PIS tax.
CREATE TABLE product_pis_template (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_tax_template_id UUID REFERENCES product_tax_template(id) ON UPDATE CASCADE,
    cst INTEGER,
    calculo product_pis_template_calculo NOT NULL DEFAULT 'percentage',
    v_bc numeric(10, 2),
    p_pis numeric(10, 2),
    v_aliq_prod numeric(10, 2),
    q_bc_prod numeric(10, 4)
);

-- Creating table to Cofins tax.
CREATE TABLE product_cofins_template (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_tax_template_id UUID REFERENCES product_tax_template(id) ON UPDATE CASCADE,
    cst INTEGER,
    calculo product_cofins_template_calculo NOT NULL DEFAULT 'percentage',
    v_bc numeric(10, 2),
    p_cofins numeric(10, 2),
    v_aliq_prod numeric(10, 2),
    q_bc_prod numeric(10, 4)
);

CREATE TABLE invoice_item_pis(
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_tax_template_id UUID REFERENCES product_tax_template(id) ON UPDATE CASCADE,
    cst INTEGER,
    calculo product_pis_template_calculo NOT NULL DEFAULT 'percentage',
    v_bc numeric(10, 2),
    p_pis numeric(10, 2),
    v_aliq_prod numeric(10, 2),
    q_bc_prod numeric(10, 4),
    v_pis numeric(10, 2)
);

CREATE TABLE invoice_item_cofins(
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    product_tax_template_id UUID REFERENCES product_tax_template(id) ON UPDATE CASCADE,
    cst INTEGER,
    calculo product_cofins_template_calculo NOT NULL DEFAULT 'percentage',
    v_bc numeric(10, 2),
    p_cofins numeric(10, 2),
    v_aliq_prod numeric(10, 2),
    q_bc_prod numeric(10, 4),
    v_cofins numeric(10, 2)
);

-- TAX
-- Create a temporary column and copying the values.
ALTER TABLE product_tax_template ADD COLUMN temp_tax_type INTEGER;
UPDATE product_tax_template SET temp_tax_type = tax_type;
UPDATE product_tax_template SET tax_type = NULL;
ALTER TABLE product_tax_template ALTER COLUMN tax_type TYPE product_tax_template_tax_type USING 'icms';

-- Setting back the column status with its new value
UPDATE product_tax_template set tax_type = 'icms' WHERE temp_tax_type = 0;
UPDATE product_tax_template set tax_type = 'ipi' WHERE temp_tax_type = 1;
UPDATE product_tax_template set tax_type = 'pis' WHERE temp_tax_type = 2;
UPDATE product_tax_template set tax_type = 'cofins' WHERE temp_tax_type = 3;

-- Removing the temporary column created.
ALTER TABLE product_tax_template DROP COLUMN temp_tax_type;

-- IPI
-- Create a temporary column and copying the values.
ALTER TABLE product_ipi_template ADD COLUMN temp_calculo INTEGER;
UPDATE product_ipi_template SET temp_calculo = calculo;
UPDATE product_ipi_template SET calculo = NULL;
ALTER TABLE product_ipi_template ALTER COLUMN calculo TYPE product_ipi_template_calculo USING 'aliquot';
ALTER TABLE product_ipi_template ALTER COLUMN calculo SET NOT NULL;

-- Setting back the column status with its new value
UPDATE product_ipi_template set calculo = 'aliquot' WHERE temp_calculo = 0;
UPDATE product_ipi_template set calculo = 'unit' WHERE temp_calculo = 1;

-- Removing the temporary column created.
ALTER TABLE product_ipi_template DROP COLUMN temp_calculo;

-- INVOICE_IPI
-- Create a temporary column and copying the values.
ALTER TABLE invoice_item_ipi ADD COLUMN temp_calculo INTEGER;
UPDATE invoice_item_ipi SET temp_calculo = calculo;
UPDATE invoice_item_ipi SET calculo = NULL;
ALTER TABLE invoice_item_ipi ALTER COLUMN calculo TYPE product_ipi_template_calculo USING 'aliquot';

-- Setting back the column status with its new value
UPDATE invoice_item_ipi set calculo = 'aliquot' WHERE temp_calculo = 0;
UPDATE invoice_item_ipi set calculo = 'unit' WHERE temp_calculo = 1;

-- Removing the temporary column created.
ALTER TABLE invoice_item_ipi DROP COLUMN temp_calculo;
