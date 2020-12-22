from decimal import Decimal
import pytest

from stoqlib.domain.payment.payment import Payment


@pytest.fixture
def payment(example_creator):
    return example_creator.create_payment()


def test_payment(payment):
    payment.status = Payment.STATUS_PREVIEW
    assert payment.is_preview() is True

    payment.status = Payment.STATUS_CANCELLED
    assert payment.is_preview() is False


@pytest.mark.parametrize('value, expected_change', (('50', '0'), ('0', '50'), ('49.99', '0.01')))
def test_payment_change(value, expected_change, payment):
    payment.base_value = Decimal('50')
    payment.value = Decimal(value)
    assert payment.change == Decimal(expected_change)


@pytest.mark.parametrize('value', ('50', '50.01', '70'))
def test_payment_change_null(value, payment):
    payment.base_value = Decimal('50')
    payment.value = Decimal(value)
    assert payment.change == Decimal('0')
