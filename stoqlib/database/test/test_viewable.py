# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Tests for module :class:`stoqlib.database.viewable.Viewable`"""

import datetime

from storm.expr import LeftJoin, Sum

from stoqlib.database.viewable import Viewable
from stoqlib.domain.account import AccountTransaction
from stoqlib.domain.commission import Commission
from stoqlib.domain.payment.method import CheckData
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.domain.person import Person, Client, Individual
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.till import TillEntry


class ClientView(Viewable):
    person = Person
    client = Client

    id = Client.id
    person_name = Person.name
    total_sales = Sum(Sale.total_amount)

    tables = [
        Client,
        LeftJoin(Person, Person.id == Client.person_id),
        LeftJoin(Sale, Sale.client_id == Client.id),
    ]

    group_by = [Person, Client, person_name]


class ViewableTest(DomainTest):

    def test_sync(self):
        self.clean_domain([CheckData, AccountTransaction, Commission,
                           TillEntry, Payment])

        # Create a payment
        due_date = datetime.date(2011, 9, 30)
        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                                      date=due_date)
        # Results should have only one item
        results = list(self.store.find(OutPaymentView))
        self.assertEquals(len(results), 1)

        # And the viewable result should be for the same payment (and have same
        # due_date)
        viewable = results[0]
        self.assertEquals(viewable.payment, payment)
        self.assertEquals(viewable.due_date.date(), due_date)

        # Update the payment due date
        new_due_date = datetime.date(2010, 4, 22)
        payment.due_date = new_due_date

        # Before syncing, the due date still have the old value
        self.assertEquals(viewable.due_date.date(), due_date)

        # Sync the viewable object and the due date should update to the new
        # value
        viewable.sync()
        self.assertEquals(viewable.due_date.date(), new_due_date)

    def test_eq(self):
        client = self.create_client(name=u'Fulano')
        view = self.store.find(ClientView, Client.id == client.id).one()
        self.failIf(view == client)

        view2 = self.store.find(ClientView, Client.id == client.id).one()
        self.assertEqual(view, view2)

    def test_store(self):
        item = self.store.find(ClientView).any()
        self.assertEquals(item.store, self.store)

    def test_hash(self):
        item = self.store.find(ClientView).any()
        self.assertEquals(hash(item), hash(item.id))

    def test_viewable_with_group_by(self):
        client = self.create_client(name=u'Fulano')
        sale = self.create_sale(client=client)
        sale.total_amount = 111

        sale = self.create_sale(client=client)
        sale.total_amount = 253

        views = self.store.find(ClientView)
        for view in views:
            if view.client == client:
                self.assertEquals(view.person, client.person)
                self.assertEquals(view.person_name, u'Fulano')
                self.assertEquals(view.total_sales, 364)
                break
        else:
            raise AssertionError('client should be found in the view')

    def test_extend_viewable(self):
        client = self.create_client(name=u'Fulano')
        client.person.individual.cpf = u'123.123.123-12'

        new_joins = [LeftJoin(Individual, Individual.person_id == Person.id)]
        new_attrs = dict(cpf=Individual.cpf)

        item = self.store.find(ClientView, Client.id == client.id).one()

        NewViewable = ClientView.extend_viewable(new_attrs=new_attrs,
                                                 new_joins=new_joins)

        item = self.store.find(NewViewable, Client.id == client.id).one()
        self.assertEquals(item.cpf, '123.123.123-12')

        item = self.store.find(ClientView, Client.id == client.id).one()
        self.assertFalse(hasattr(item, 'cpf'))

    def test_viewable_without_id(self):

        class SimpleViewable(Viewable):
            name = Person.name
            tables = [Person]

        # It should still be possible to find viewables that dont have an id
        items = self.store.find(SimpleViewable)

        # And we still can hash the object
        assert hash(items[0])

    def test_has_column(self):
        self.assertTrue(ClientView.has_column(column=ClientView.client))
        self.assertFalse(ClientView.has_column(column=Sellable.description))

    def test_has_join_with(self):
        self.assertTrue(ClientView.has_join_with(table=Client))
        self.assertTrue(ClientView.has_join_with(table=Sale))
        self.assertFalse(ClientView.has_join_with(table=Sellable))
