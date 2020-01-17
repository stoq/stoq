from decimal import Decimal
from unittest import mock

import datetime
import pytest
import xlwt

from stoqlib.exporters.xlsexporter import XLSExporter


def test_xls_exporter_write_one():
    exporter = XLSExporter()
    exporter._ws = mock.Mock()
    style = xlwt.XFStyle()
    i = 10

    exporter._write_one(i, 'foo', style)

    exporter._ws.write.assert_called_once_with(1, i, 'foo', style)


@pytest.mark.parametrize('data, expected_value', (
    (None, ''),
    (69, 69),
    ('foo', 'foo'),
    (Decimal('6.9'), Decimal('6.9')),
    (datetime.date(2020, 1, 7), '2020-01-07'),
    (b'foo', 'foo'),
))
def test_xls_exporter_convert_one(data, expected_value):
    exporter = XLSExporter()

    assert exporter._convert_one(data) == expected_value
