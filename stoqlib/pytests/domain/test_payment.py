from stoqlib.domain.payment.payment import Payment


def test_payment(example_creator):
    payment = example_creator.create_payment()

    payment.status = Payment.STATUS_PREVIEW
    assert payment.is_preview() is True

    payment.status = Payment.STATUS_CANCELLED
    assert payment.is_preview() is False
