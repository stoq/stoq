import os
from unittest import mock

import pkg_resources
import pytest

from stoqlib.database.migration import Patch, SchemaMigration, StoqlibSchemaMigration
from stoqlib.exceptions import DatabaseInconsistency


def test_patch_dunder_methods():
    first_patch = Patch('patch-01-00.sql', None)
    second_patch = Patch('patch-01-01.sql', None)

    assert first_patch == first_patch
    assert second_patch == second_patch
    assert first_patch != second_patch
    assert first_patch < second_patch
    assert second_patch > first_patch


def test_patch_invalid_file():
    patch = Patch('patch-01-00.java', mock.Mock())

    with pytest.raises(AssertionError):
        patch.apply(None)


def test_schema_migration_invalid_class_attributes():
    class InvalidSchemaMigration(SchemaMigration):
        pass

    with pytest.raises(ValueError) as exc_info:
        InvalidSchemaMigration()

    exc_info.match("needs to have the patch_resource")

    class InvalidSchemaMigration(SchemaMigration):
        patch_resource = "domain"
        patch_patterns = None

    with pytest.raises(ValueError) as exc_info:
        InvalidSchemaMigration()

    exc_info.match("needs to have the patch_patterns")


@mock.patch("stoqlib.database.migration.error")
@mock.patch("stoqlib.database.migration.check_extensions")
def test_schema_migration_missing_postgres_extensions(check_extensions_mock, error_mock):
    check_extensions_mock.side_effect = ValueError

    class Migration(SchemaMigration):
        patch_resource = "domain"

    Migration()

    msg = "Missing PostgreSQL extension on the server, please install postgresql-contrib"
    error_mock.assert_called_once_with(msg)


def test_schema_migration_get_patches_invalid_patch_name(schema_migration, capsys):
    migration_path = pkg_resources.resource_filename(schema_migration.patch_resource_domain,
                                                     schema_migration.patch_resource)
    migration_filename = "{}/patch-10.py".format(migration_path)
    with open(migration_filename, 'w') as f:
        f.write("foobar")

    patches = schema_migration._get_patches()

    captured = capsys.readouterr()
    assert captured.out == "Invalid patch name: patch-10.py\n"
    patches_filenames = {patch.filename for patch in patches}
    assert "patch-10.py" not in patches_filenames

    os.remove(migration_filename)


@pytest.fixture
def schema_migration():
    return StoqlibSchemaMigration()


def test_schema_migration_check_uptodate(schema_migration):
    assert schema_migration.check_uptodate() is True


def test_schema_migration_check_uptodate_not_up_to_date(schema_migration):
    schema_migration.get_current_version = mock.Mock(return_value=(0, 0))

    assert schema_migration.check_uptodate() is False


def test_schema_migration_check_uptodate_not_inconsistent(schema_migration):
    schema_migration.get_current_version = mock.Mock(return_value=(999, 666))

    with pytest.raises(DatabaseInconsistency):
        assert schema_migration.check_uptodate()


def test_schema_migration_update(schema_migration, capsys):
    schema_migration.get_current_version = mock.Mock(return_value=(6, 9))
    schema_migration.check_uptodate = mock.Mock(return_value=True)

    schema_migration.update()

    captured = capsys.readouterr()
    assert "Database is already at the latest version 6.9\n" in captured.out
