# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

# pylint: enable=E1101
"""Views related to Daily Movement Reports"""

from storm.expr import Join, LeftJoin, Sum, Alias, Select, Coalesce
from storm.info import ClassAlias

from stoqlib.database.expr import Field, NullIf
from stoqlib.domain.payment.views import InPaymentView, OutPaymentView
from stoqlib.domain.person import Branch, Client, Company, Person, SalesPerson
from stoqlib.domain.sale import Sale, SaleItem, InvoiceItemIpi


_SaleItemSummary = Select(columns=[SaleItem.sale_id,
                                   Alias(Sum(SaleItem.quantity * SaleItem.price +
                                         InvoiceItemIpi.v_ipi), 'subtotal')],
                          tables=[SaleItem,
                                  LeftJoin(InvoiceItemIpi,
                                           SaleItem.ipi_info_id == InvoiceItemIpi.id)],
                          group_by=[SaleItem.sale_id])

SaleItemSummary = Alias(_SaleItemSummary, '_sale_items')


class DailyInPaymentView(InPaymentView):

    SalesPersonPerson = ClassAlias(Person, 'salesperson_person')
    ClientPerson = ClassAlias(Person, 'client_person')
    PersonBranch = ClassAlias(Person, 'person_branch')

    salesperson_name = SalesPersonPerson.name
    client_name = ClientPerson.name
    branch_name = Coalesce(NullIf(Company.fancy_name, u''), PersonBranch.name)

    sale_subtotal = Field('_sale_items', 'subtotal')

    tables = InPaymentView.tables[:]
    tables.extend([
        Join(PersonBranch, Branch.person_id == PersonBranch.id),
        Join(Company, Branch.person_id == Company.person_id),
        LeftJoin(SalesPerson, Sale.salesperson_id == SalesPerson.id),
        LeftJoin(SalesPersonPerson,
                 SalesPerson.person_id == SalesPersonPerson.id),
        LeftJoin(Client, Sale.client_id == Client.id),
        LeftJoin(ClientPerson, Client.person_id == ClientPerson.id),
        LeftJoin(SaleItemSummary, Field('_sale_items', 'sale_id') == Sale.id),
    ])


class DailyOutPaymentView(OutPaymentView):

    SalesPersonPerson = ClassAlias(Person, 'salesperson_person')
    ClientPerson = ClassAlias(Person, 'client_person')
    PersonBranch = ClassAlias(Person, 'person_branch')

    salesperson_name = SalesPersonPerson.name
    client_name = ClientPerson.name
    branch_name = Coalesce(NullIf(Company.fancy_name, u''), PersonBranch.name)

    sale_subtotal = Field('_sale_items', 'subtotal')

    tables = OutPaymentView.tables[:]
    tables.extend([
        Join(PersonBranch, Branch.person_id == PersonBranch.id),
        Join(Company, Branch.person_id == Company.person_id),
        LeftJoin(SalesPerson, Sale.salesperson_id == SalesPerson.id),
        LeftJoin(SalesPersonPerson,
                 SalesPerson.person_id == SalesPersonPerson.id),
        LeftJoin(Client, Sale.client_id == Client.id),
        LeftJoin(ClientPerson, Client.person_id == ClientPerson.id),
        LeftJoin(SaleItemSummary, Field('_sale_items', 'sale_id') == Sale.id),
    ])
