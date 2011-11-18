-- Renomenado parametro

UPDATE parameter_data SET field_name = 'ALLOW_OUTDATED_OPERATIONS'
    WHERE field_name = 'ALLOW_OUTDATED_PURCHASES';
