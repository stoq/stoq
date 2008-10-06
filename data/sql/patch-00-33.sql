-- #3636: Erro ao atualizar o banco de dados quando tem-se cadastrado
-- um branch.

UPDATE parameter_data
    SET field_value=1
    WHERE field_name='MAIN_COMPANY';
