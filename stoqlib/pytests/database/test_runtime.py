import pytest
from unittest import mock


@pytest.mark.parametrize('table_exists, expected_result', ((True, True), (False, False)))
def test_is_link_server(table_exists, expected_result, store):
    store.table_exists = mock.Mock(return_value=table_exists)

    rv = store.is_link_server()

    assert rv is expected_result
