from decimal import Decimal

from stoqlib.lib.barcode import parse_barcode, BarcodeInfo


def test_barcode_parse_barcode_price():
    info = parse_barcode('2000100005279', BarcodeInfo.OPTION_4_DIGITS_PRICE)

    assert info.code == '0001'
    assert info.price == Decimal('5.27')
    assert info.weight is None
    assert info.mode == BarcodeInfo.MODE_PRICE


def test_barcode_parse_barcode_weight():
    info = parse_barcode('2123456005279', BarcodeInfo.OPTION_6_DIGITS_WEIGHT)

    assert info.code == '123456'
    assert info.price is None
    assert info.weight == Decimal('0.527')
    assert info.mode == BarcodeInfo.MODE_WEIGHT
