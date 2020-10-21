import pytest

from stoqlib.lib.boleto import _banks, get_all_banks, get_bank_info_by_number


def test_get_all_banks():
    assert get_all_banks() is _banks


def test_get_bank_info_by_number():
    with pytest.raises(NotImplementedError):
        get_bank_info_by_number(696969696699669696969699669)
