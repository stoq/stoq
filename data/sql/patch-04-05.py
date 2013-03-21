# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
# Adicionando controle de maquinetas de cartões

from storm.references import Reference

from stoqlib.database.properties import PercentCol, PriceCol, UnicodeCol, IntCol
from stoqlib.database.properties import BoolCol
from stoqlib.migration.domainv1 import Domain
from stoqlib.lib.translation import stoqlib_gettext as _


class CreditCardData(object):
    TYPE_CREDIT = 0
    TYPE_DEBIT = 1
    TYPE_CREDIT_INSTALLMENTS_STORE = 2
    TYPE_CREDIT_INSTALLMENTS_PROVIDER = 3
    TYPE_DEBIT_PRE_DATED = 4


class CardPaymentDevice(Domain):
    __storm_table__ = 'card_payment_device'
    monthly_cost = PriceCol()
    description = UnicodeCol()


class CardOperationCost(Domain):
    __storm_table__ = 'card_operation_cost'
    device_id = IntCol(default=None)
    device = Reference(device_id, CardPaymentDevice.id)
    provider_id = IntCol(default=None)
    card_type = IntCol(default=0)
    installment_start = IntCol(default=1)
    installment_end = IntCol(default=1)
    payment_days = IntCol(default=30)
    fee = PercentCol(default=0)
    fare = PriceCol(default=0)


class PaymentMethod(Domain):
    __storm_table__ = 'payment_method'

    method_name = UnicodeCol()
    is_active = BoolCol(default=True)
    daily_interest = PercentCol(default=0)
    penalty = PercentCol(default=0)
    payment_day = IntCol(default=None)
    closing_day = IntCol(default=None)
    max_installments = IntCol(default=1)
    destination_account_id = IntCol(default=None)


def apply_patch(store):
    # Apagando referencias para person de credit_provider
    # This is not safe to execute, since the user may have changed the records
    # (even creating new ones), that other tables may reference
    # query = """SELECT credit_provider.id, credit_provider.person_id
    #    FROM credit_provider"""
    # data = store.execute(query).get_all()
    # for (provider_id, person_id) in data:
    #    store.execute("""DELETE FROM address WHERE person_id = ?;""", (person_id,))
    #    store.execute("""DELETE FROM company WHERE person_id = ?;""", (person_id,))
    #    store.execute("""UPDATE credit_provider
    #                  SET person_id = NULL WHERE id = ?;""", (provider_id,))
    #    store.execute("""DELETE FROM person WHERE id = ?;""", (person_id,))

    # Droping column person_id from credit_provider
    store.execute('''ALTER TABLE credit_provider DROP COLUMN person_id;''')

    # Creating new tables
    store.execute("""
        CREATE TABLE card_payment_device (
            id serial NOT NULL PRIMARY KEY,
            te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
            te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

            monthly_cost numeric(20, 2),
            description text
        );

        CREATE TABLE card_operation_cost (
            id serial NOT NULL PRIMARY KEY,
            te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
            te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

            device_id bigint REFERENCES card_payment_device(id) ON UPDATE CASCADE,
            provider_id bigint REFERENCES credit_provider(id) ON UPDATE CASCADE,
            card_type integer CONSTRAINT valid_status
                CHECK (card_type >= 0 AND card_type < 5),

            installment_start integer CONSTRAINT positive_installment_start
                CHECK (installment_start>=1),
            installment_end integer CONSTRAINT positive_installment_end
                CHECK (installment_end>=1),
            payment_days integer CHECK (payment_days >= 0),
            fee numeric(10, 2),
            fare numeric(20, 2),
            CONSTRAINT valid_installment_range
                CHECK (installment_start <= installment_end)
        );""")

    # Updating existing tables
    store.execute("""
        ALTER TABLE credit_card_data ADD COLUMN fare numeric(20, 2);
        UPDATE credit_card_data SET fare = 0;
        ALTER TABLE credit_card_data ADD COLUMN device_id bigint
            REFERENCES card_payment_device(id) ON UPDATE CASCADE;""")

    # Migrating old data to new format
    card = store.find(PaymentMethod, method_name=u'card').one()

    device = CardPaymentDevice(description=_(u'Default'), store=store)
    query = """SELECT id, credit_fee, credit_installments_store_fee,
                      credit_installments_provider_fee, debit_fee,
                      debit_pre_dated_fee, max_installments
                FROM credit_provider"""
    data = store.execute(query).get_all()
    for (provider_id, credit_fee, credit_store_fee, credit_provider_fee,
         debit_fee, pre_date_fee, max_installments) in data:
        # Credit
        if credit_fee:
            CardOperationCost(device=device, provider_id=provider_id,
                              card_type=CreditCardData.TYPE_CREDIT,
                              payment_days=30, fee=credit_fee,
                              store=store)
        # Debit
        if debit_fee:
            CardOperationCost(device=device, provider_id=provider_id,
                              card_type=CreditCardData.TYPE_DEBIT,
                              payment_days=1, fee=debit_fee,
                              store=store)
        # Credit Installments Store
        if credit_store_fee:
            CardOperationCost(device=device, provider_id=provider_id,
                              card_type=CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE,
                              payment_days=31, fee=credit_store_fee,
                              installment_start=1,
                              installment_end=card.max_installments,
                              store=store)
        # Credit Installments provider
        if credit_provider_fee:
            CardOperationCost(device=device, provider_id=provider_id,
                              card_type=CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER,
                              payment_days=31, fee=credit_provider_fee,
                              installment_start=1, installment_end=max_installments,
                              store=store)
        # Debit Pre dated
        if pre_date_fee:
            CardOperationCost(device=device, provider_id=provider_id,
                              card_type=CreditCardData.TYPE_DEBIT_PRE_DATED,
                              payment_days=30, fee=pre_date_fee,
                              store=store)

    # Droping old columns
    store.execute("""
        ALTER TABLE credit_provider
            DROP COLUMN provider_type,
            DROP COLUMN payment_day,
            DROP COLUMN closing_day,
            DROP COLUMN monthly_fee,
            DROP COLUMN credit_fee,
            DROP COLUMN credit_installments_store_fee,
            DROP COLUMN credit_installments_provider_fee,
            DROP COLUMN debit_fee,
            DROP COLUMN debit_pre_dated_fee;
            """)
