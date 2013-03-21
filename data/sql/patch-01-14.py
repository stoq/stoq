# -*- coding: utf-8 -*-

# 3501: Código do produto deve ter possuir 14 caractere.

from stoqlib.domain.sellable import Sellable


def apply_patch(store):
    store.execute('ALTER TABLE sellable ADD COLUMN code text;')

    # data migration
    for sellable in store.find(Sellable):
        sellable.code = u'%d' % sellable.id
        barcode = u'%014s' % sellable.barcode
        # Update barcode only if we already have one.
        if barcode.strip():
            sellable.barcode = barcode.replace(' ', '0')

    store.commit()
