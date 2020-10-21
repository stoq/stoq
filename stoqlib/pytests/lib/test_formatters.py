import pytest

from stoqlib.lib import formatters


def test_format_quantity():
    assert formatters.format_quantity(1.69) == "1.690"


def test_get_formatted_cost():
    assert formatters.get_formatted_cost(1.69) == "R$ 1,69"


def test_format_phone_number():
    assert formatters.format_phone_number("1231234") == "123-1234"


def test_format_postal_code():
    assert formatters.format_postal_code("12345678") == "12345-678"


def test_format_document():
    assert formatters.format_document("12345678901") == "123.456.789-01"
    assert formatters.format_document("12345678000101") == "12.345.678/0001-01"
    with pytest.raises(ValueError):
        formatters.format_document("")
