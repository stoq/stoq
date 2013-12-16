-- new parameter

-- Also fix parameter renaming
UPDATE parameter_data SET field_value = '0'
WHERE field_name = 'RETURN_MONEY_ON_SALES';

UPDATE parameter_data SET field_name = 'RETURN_POLICY_ON_SALES'
WHERE field_name = 'RETURN_MONEY_ON_SALES';
