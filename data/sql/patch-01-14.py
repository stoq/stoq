# -*- coding: utf-8 -*-

#3501: Código do produto deve ter possuir 14 caractere.

from stoqlib.domain.sellable import Sellable

def apply_patch(trans):
   trans.query('ALTER TABLE sellable ADD COLUMN code text;')

   # data migration
   for sellable in Sellable.select(connection=trans):
       #old_code = sellable.id
       sellable.code = u'%d' % sellable.id
       barcode = u'%014s' % sellable.barcode
       sellable.barcode = barcode.replace(' ', '0')

   trans.commit()
