-- #Bug 3733 fail to update schema from 0.9.5 to 0.9.6


-- In case the parameter MAIN_COMPANY is greater then the last id of the available branches,
-- this probably means bug 3733 happend, and we should update that parameter.


UPDATE parameter_data SET field_value =
    CASE WHEN (SELECT max(id) FROM person_adapt_to_branch) < field_value::integer THEN
        (SELECT id::text FROM person_adapt_to_branch WHERE original_id = field_value)
    ELSE
        field_value
    END
    WHERE field_name='MAIN_COMPANY';
