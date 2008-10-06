-- 3822: Renomar coluna assellable para sellable da tabela commission_source

ALTER TABLE commission_source RENAME asellable_id TO sellable_id;

ALTER TABLE commission_source
    DROP CONSTRAINT check_exist_one_fkey;

ALTER TABLE commission_source
    ADD CONSTRAINT check_exist_one_fkey
        CHECK ((((category_id IS NOT NULL) AND (sellable_id IS NULL)) OR
                ((category_id IS NULL) AND (sellable_id IS NOT NULL))));
