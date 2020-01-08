import pytest


@pytest.fixture
def sale(example_creator):
    return example_creator.create_sale()


def test_sale_invoice_subtotal(sale):
    assert sale.invoice_subtotal == sale.get_sale_subtotal()


def test_sale_invoice_total(sale):
    assert sale.invoice_total == sale.get_total_sale_amount()
