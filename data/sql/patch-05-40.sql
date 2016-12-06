CREATE TYPE invoice_mode AS ENUM ('nfe', 'nfce');
ALTER TABLE invoice ADD mode invoice_mode;
ALTER TABLE invoice ADD series INTEGER;
ALTER TABLE invoice DROP CONSTRAINT invoice_branch_id_invoice_number_key;
CREATE UNIQUE INDEX invoice_mode_series_invoice_number_branch_id_key ON invoice (mode, series, invoice_number, branch_id);

-- Migrate the invoice mode from the nfe_data table from the nfe plugin if it exists.
DO $$DECLARE nfe_mode_exists INTEGER;
BEGIN
  SELECT COUNT(1) INTO nfe_mode_exists FROM information_schema.columns WHERE table_name = 'nfe_data' AND column_name = 'nfe_mode';
  IF nfe_mode_exists >= 1 THEN
    -- We need to double cast here since postgres dont allow us to set it directly.
    UPDATE invoice SET mode = nfe_data.nfe_mode::text::invoice_mode FROM nfe_data WHERE nfe_data.invoice_id = invoice.id;
  END IF;
END$$;

-- This should be de ideal check, but postgres (As 9.4 does not support
-- deferred check constraints). We'll do this in python
-- ALTER TABLE invoice ADD CONSTAINT CHECK_INVOICE_DATA CHECK (
--     (mode IS NULL AND serie IS NULL AND invoice_number IS NULL) OR
--     (mode IS NOT NULL AND serie IS NOT NULL AND invoice_number IS NOT NULL)
-- ) INITIALLY DEFERRED;
