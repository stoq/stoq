# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
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

from stoqlib.domain.invoice import InvoiceLayout, InvoiceField
from stoqlib.importers.csvimporter import CSVImporter


class InvoiceImporter(CSVImporter):

    fields = ['layout_description',
              'layout_width',
              'layout_height',
              'field_name',
              'field_x',
              'field_y',
              'field_width',
              'field_height',
              ]

    def _get_or_create(self, table, store, **attributes):
        obj = store.find(table, **attributes).one()
        if obj is None:
            obj = table(store=store, **attributes)
        return obj

    def process_one(self, data, fields, store):
        layout = self._get_or_create(
            InvoiceLayout, store,
            description=data.layout_description,
            width=int(data.layout_width),
            height=int(data.layout_height))

        InvoiceField(layout=layout,
                     field_name=data.field_name,
                     x=int(data.field_x),
                     y=int(data.field_y),
                     width=int(data.field_width),
                     height=int(data.field_height),
                     store=store)
