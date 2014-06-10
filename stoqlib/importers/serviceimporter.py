# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_default_store
from stoqlib.domain.service import Service
from stoqlib.domain.sellable import (Sellable,
                                     SellableTaxConstant)
from stoqlib.importers.csvimporter import CSVImporter


class ServiceImporter(CSVImporter):
    fields = ['description',
              'barcode',
              'price',
              'cost',
              ]

    def __init__(self):
        super(ServiceImporter, self).__init__()
        default_store = get_default_store()
        self.tax_constant = SellableTaxConstant.get_by_type(
            TaxType.SERVICE, default_store)

        self._code = 11
        assert self.tax_constant

    def process_one(self, data, fields, store):
        tax = store.fetch(self.tax_constant)
        sellable = Sellable(store=store,
                            description=data.description,
                            price=int(data.price),
                            cost=int(data.cost))
        sellable.tax_constant = tax
        sellable.code = u'%02d' % self._code
        self._code += 1
        sellable.barcode = data.barcode

        Service(sellable=sellable,
                store=store)
