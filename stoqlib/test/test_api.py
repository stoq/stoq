# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from stoqlib.api import api
from stoqlib.domain.person import Client, Individual
from stoqlib.domain.test.domaintest import DomainTest


class APITest(DomainTest):
    def test_for_combo_all(self):
        client = self.create_client()
        client.credit_limit = 99
        clients = self.store.find(Client, credit_limit=99,
                                  )
        items = api.for_combo(clients)
        self.assertEquals(items, [('Client', client)])

    def test_for_combo_items(self):
        client = self.create_client()
        client.credit_limit = 99
        results = self.store.find(Client, credit_limit=99)
        items = api.for_combo(results)
        self.assertEquals(items, [('Client', client)])

    def test_for_combo_attr(self):
        individual = self.create_individual()
        individual.father_name = u'Daddy'
        individual.mother_name = u'Mommy'
        results = self.store.find(Individual, father_name=u'Daddy')
        items = api.for_combo(results, attr=u'mother_name')
        self.assertEquals(items, [('Mommy', individual)])

    def test_for_combo_empty(self):
        client = self.create_client()
        client.credit_limit = 99
        results = self.store.find(Client, credit_limit=99)
        items = api.for_combo(results,
                              empty=u'All')
        self.assertEquals(items, [('All', None),
                                  ('Client', client)])
