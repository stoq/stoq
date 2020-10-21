import pytest

from stoqlib.lib.stringutils import strip_accents


@pytest.mark.parametrize('accented_string, stripped_string', (
    ('áâãäåāăąàÁÂÃÄÅĀĂĄÀ', 'aaaaaaaaaAAAAAAAAA'),
    ('èééêëēĕėęěĒĔĖĘĚ', 'eeeeeeeeeeEEEEE'),
    ('ìíîïìĩīĭÌÍÎÏÌĨĪĬ', 'iiiiiiiiIIIIIIII'),
    ('óôõöōŏőÒÓÔÕÖŌŎŐ', 'oooooooOOOOOOOO'),
    ('ùúûüũūŭůÙÚÛÜŨŪŬŮ', 'uuuuuuuuUUUUUUUU'),
    ('çÇ', 'cC'),
))
def test_strip_accents(accented_string, stripped_string):
    assert strip_accents(accented_string) == stripped_string
