from decimal import Decimal
from unittest import mock
import os

import datetime
import pytest
import xlwt

from stoqlib.exporters.xlsexporter import XLSExporter


@pytest.fixture
def xls_exporter():
    return XLSExporter()


def test_xls_exporter_add_row(xls_exporter):
    xls_exporter.set_column_headers(('name', 'age'))
    xls_exporter.set_column_types((str, int))
    cell = ('Tomás', 69)

    xls_exporter.add_cells([cell], filter_description="foo")

    assert xls_exporter._n_columns == 2
    assert xls_exporter._current_column == 3
    assert xls_exporter._headers == ('name', 'age')


def test_xls_exporter_add_row_invalid(xls_exporter):
    xls_exporter.set_column_headers(('name', 'age'))

    with pytest.raises(ValueError):
        xls_exporter.add_cells([('Tomás', 69, 'foobar')])


@pytest.mark.parametrize("prefix,filename", (
    ("", "Stoq-"),
    ("eita", "Stoq-eita-"),
))
def test_xls_exporter_save(prefix, filename, xls_exporter):
    xls_exporter.set_column_headers(('name', 'age'))
    xls_exporter.set_column_types((str, int))
    cell = ('Tomás', 69)
    xls_exporter.add_cells([cell] * 3)

    f = xls_exporter.save(prefix=prefix)

    assert filename in f.name
    assert f.file

    os.remove(f.name)


def test_xls_exporter_write_one(xls_exporter):
    xls_exporter._ws = mock.Mock()
    style = xlwt.XFStyle()
    i = 10

    xls_exporter._write_one(i, 'foo', style)

    xls_exporter._ws.write.assert_called_once_with(0, i, 'foo', style)


@pytest.mark.parametrize('data, expected_value', (
    (None, ''),
    (69, 69),
    ('foo', 'foo'),
    (Decimal('6.9'), Decimal('6.9')),
    (datetime.date(2020, 1, 7), '2020-01-07'),
    (b'foo', 'foo'),
))
def test_xls_exporter_convert_one(data, expected_value, xls_exporter):
    assert xls_exporter._convert_one(data) == expected_value
