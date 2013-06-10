# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.domain.person import Person
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.transfer import TransferOrder
from stoqlib.importers.csvimporter import CSVImporter


class TransferImporter(CSVImporter):
    fields = ['source_branch_name',
              'source_employee_name',
              'dest_branch_name',
              'dest_employee_name',
              'sellable_list',  # ids separated by | or * for all
              'open_date',
              'receival_date',
              'quantity']

    def process_one(self, data, fields, store):
        person = store.find(Person, name=data.source_branch_name).one()
        if person is None or person.branch is None:
            raise ValueError("%s is not a valid branch" % (
                data.source_branch_name, ))
        source_branch = person.branch

        person = store.find(Person, name=data.source_employee_name).one()
        if person is None or person.employee is None:
            raise ValueError("%s is not a valid employee" % (
                data.source_employee_name, ))
        source_employee = person.employee

        person = store.find(Person, name=data.dest_branch_name).one()
        if person is None or person.branch is None:
            raise ValueError("%s is not a valid branch" % (
                data.dest_branch_name, ))
        dest_branch = person.branch

        person = store.find(Person, name=data.dest_employee_name).one()
        if person is None or person.employee is None:
            raise ValueError("%s is not a valid employee" % (
                data.dest_employee_name, ))
        dest_employee = person.employee

        sellables = self.parse_multi(Sellable, data.sellable_list, store)

        order = TransferOrder(store=store,
                              open_date=self.parse_date(data.open_date),
                              receival_date=None,
                              source_branch=source_branch,
                              destination_branch=dest_branch,
                              source_responsible=source_employee,
                              destination_responsible=None)

        for sellable in sellables:
            if not sellable.product:
                continue
            order.add_sellable(sellable, batch=None,
                               quantity=int(data.quantity))

        order.send()
        order.receive(dest_employee)
