# -*- coding: utf-8 -*-

# 3964: Adicao de coluna "Conferido por" no dialogo de recebimento de compras de estoque.

from stoqlib.domain.purchase import PurchaseOrder


def apply_patch(store):
    store.execute('''
        ALTER TABLE purchase_order
            ADD COLUMN responsible_id bigint REFERENCES person_adapt_to_user(id);''')
    for order in store.find(PurchaseOrder):
        responsible = order.te_modified.user
        order.responsible = responsible

    store.commit()
