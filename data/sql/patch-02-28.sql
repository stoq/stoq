--
--  #4338 - Produtos com unidades não fracionáveis
--          estão sendo vendidos como fração.
--  Add allow_fraction column on sellable_unit table.
--

ALTER TABLE sellable_unit
    ADD COLUMN allow_fraction boolean DEFAULT TRUE;

