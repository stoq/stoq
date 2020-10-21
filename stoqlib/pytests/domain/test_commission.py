from decimal import Decimal

from stoqlib.domain.commission import Commission, CommissionView


def test_commission(store, example_creator):
    payment = example_creator.create_payment()
    sale = example_creator.create_sale()
    sale.group = payment.group
    Commission(
        store=store,
        value=666,
        sale=sale,
        payment=payment,
    )
    view = store.find(CommissionView, payment_id=payment.id).one()

    assert view.method_description == "Money"
    assert view.payment_amount == Decimal('-10')
    assert view.total_amount == Decimal('0')
