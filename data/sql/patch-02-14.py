# -*- coding: utf-8 -*-

# bug 4201: Atualizacão de dados existentes na tabela 'credit_card_data'

from stoqlib.domain.payment.method import CreditCardData

def apply_patch(trans):
    # Patch 2-24 introduces these ones
    try:
        CreditCardData.sqlmeta.delColumn('nsu')
        CreditCardData.sqlmeta.delColumn('auth')
        CreditCardData.sqlmeta.delColumn('installments')
        CreditCardData.sqlmeta.delColumn('entrance_value')
    except KeyError:
        pass

    for data in CreditCardData.select(connection=trans):
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
    trans.commit()
