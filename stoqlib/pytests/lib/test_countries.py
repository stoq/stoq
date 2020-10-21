from stoqlib.lib.countries import get_countries


def test_get_countries():
    countries = get_countries()

    assert ("Angola", "Angola") in countries
    assert len(countries) == 253
