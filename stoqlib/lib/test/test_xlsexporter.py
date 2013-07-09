# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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

import os

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exporters.xlsexporter import XLSExporter

from kiwi.ui.objectlist import ObjectList, Column


class Fruit:
    def __init__(self, name, price):
        self.name = name
        self.price = price


class XLSExporterTest(DomainTest):
    def test_export_from_object_list(self):
        fruits = ObjectList([Column('name', data_type=str),
                             Column('price', data_type=int)])

        for name, price in [('Apple', 4),
                            ('Pineapple', 2),
                            ('Kiwi', 8),
                            ('Banana', 3),
                            ('Melon', 5)]:
            fruits.append(Fruit(name, price))

        ofx = XLSExporter()

        ofx.add_from_object_list(fruits)

        try:
            temp_file = ofx.save()
            data = open(temp_file.name).read()

            # We should use xlrd to 're-open' the spreadsheet and parse its content.
            self.assertTrue(len(data) > 0)

        finally:
            temp_file.close()
            os.unlink(temp_file.name)
