-- Remove unique constraint of plugin_version column in installed_plugin table.

ALTER TABLE installed_plugin DROP CONSTRAINT installed_plugin_plugin_version_key;
