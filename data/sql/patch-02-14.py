# -*- coding: utf-8 -*-

# bug 4201: Atualizacão de dados existentes na tabela 'credit_card_data'

from stoqlib.database.properties import IntCol, PriceCol

from stoqlib.domain.payment.method import CreditCardData  # pylint: disable=E0611


def apply_patch(store):
    # Patch 2-24 introduces these ones
    try:
        CreditCardData.sqlmeta.delColumn('nsu')
        CreditCardData.sqlmeta.delColumn('auth')
        CreditCardData.sqlmeta.delColumn('installments')
        CreditCardData.sqlmeta.delColumn('entrance_value')
    except KeyError:
        pass

    for data in store.find(CreditCardData):
        payment = data.payment
        provider = data.provider

        # Before, provider_fee had percentual data type
        # With this change, monthly_fee has monetary data type

        data.fee = provider.monthly_fee
        data.fee_value = payment.value * data.fee / 100
        provider.credit_fee = provider.monthly_fee
        provider.credit_installments_store_fee = provider.monthly_fee
        provider.credit_installments_provider_fee = provider.monthly_fee
        provider.debit_fee = provider.monthly_fee
        provider.debit_pre_dated_fee = provider.monthly_fee
        provider.monthly_fee = 0
    store.commit()

    try:
        CreditCardData.sqlmeta.addColumn(IntCol('nsu', default=None))
    except KeyError:
        pass

    try:
        CreditCardData.sqlmeta.addColumn(IntCol('auth', default=None))
    except KeyError:
        pass

    try:
        CreditCardData.sqlmeta.addColumn(IntCol('installments', default=1))
    except KeyError:
        pass

    try:
        CreditCardData.sqlmeta.addColumn(PriceCol('entrance_value', default=0))
    except KeyError:
        pass
