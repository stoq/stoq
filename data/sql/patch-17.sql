-- #2299: Implementar infra-estrutura de plugins

CREATE TABLE installed_plugin (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    plugin_name text UNIQUE NOT NULL,
    plugin_version integer UNIQUE CONSTRAINT positive_plugin_version 
                                  CHECK (plugin_version >= 0)
);
