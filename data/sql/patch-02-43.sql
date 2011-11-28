-- Renomenado parametro

UPDATE parameter_data SET field_name = 'COST_PRECISION_DIGITS'
    WHERE field_name = 'USE_FOUR_PRECISION_DIGITS';

UPDATE parameter_data SET field_value = '4'
    WHERE field_name = 'COST_PRECISION_DIGITS' AND field_value = '1';
UPDATE parameter_data SET field_value = '2'
    WHERE field_name = 'COST_PRECISION_DIGITS' AND field_value = '0';
