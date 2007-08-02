-- #3294: Alterar as informações enviadas ao arquivo sintegra referente
--        ao Registro Tipo 11

ALTER TABLE person_adapt_to_branch DROP COLUMN manager_id;

ALTER TABLE person_adapt_to_branch ADD COLUMN manager_id bigint
    REFERENCES person_adapt_to_employee(id);
