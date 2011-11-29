# -*- coding: utf-8 -*-

#3501: Código do produto deve ter possuir 14 caractere.

from stoqlib.domain.sellable import Sellable

def apply_patch(trans):
    trans.query('ALTER TABLE sellable ADD COLUMN code text;')

    # data migration
    for sellable in Sellable.select(connection=trans):
        sellable.code = u'%d' % sellable.id
        barcode = u'%014s' % sellable.barcode
        # Update barcode only if we already have one.
        if barcode.strip():
            sellable.barcode = barcode.replace(' ', '0')

    trans.commit()
