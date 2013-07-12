# -*- coding: utf-8 -*-

# Populates PaymentFlowHistory based on the existing payments.

# pylint: disable=E0611
from stoqlib.domain.payment.payment import Payment, PaymentFlowHistory
from stoqlib.lib.message import info


def apply_patch(store):
    info(u'The schema update might take a long time to complete, depending '
         'the size of your database and your hardware.')

    for payment in store.find(Payment).order_by(['due_date',
                                                 'paid_date',
                                                 'cancel_date']):
        if payment.is_preview():
            continue

        if payment.due_date:
            history_date = payment.due_date.date()
        else:
            history_date = payment.open_date.date()

        PaymentFlowHistory.add_payment(store, payment, history_date)

        if payment.is_paid():
            PaymentFlowHistory.add_paid_payment(store, payment,
                                                payment.paid_date.date())
        elif payment.is_cancelled():
            if payment.paid_date:
                PaymentFlowHistory.add_paid_payment(store, payment,
                                                    payment.paid_date.date())
                PaymentFlowHistory.remove_paid_payment(store, payment,
                                                       payment.cancel_date.date())
            else:
                PaymentFlowHistory.remove_payment(store, payment,
                                                  payment.due_date.date())
