from stoqlib.database.tables import _get_tables_cache, _tables_cache, _tables


def test_get_tables_cache():
    _tables_cache.clear()

    cache = _get_tables_cache()

    assert len(cache) >= len(_tables)
