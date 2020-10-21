import pytest

from stoqlib.lib import importutils


def test_import_from_string():
    assert importutils.import_from_string('stoqlib.lib.importutils') == importutils

    func = importutils.import_from_string('stoqlib.lib.importutils.import_from_string')
    assert func == importutils.import_from_string

    with pytest.raises(ImportError) as excinfo:
        importutils.import_from_string('stoqlib.this.module.does.not.exists')
    excinfo.match("No module named 'stoqlib.this'")

    with pytest.raises(ImportError) as excinfo:
        importutils.import_from_string('stoqlib.lib.importutils.this_func_does_not_exists')
    excinfo.match('Failed to import')
