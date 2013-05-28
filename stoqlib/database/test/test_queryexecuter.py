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
""" This module tests stoq/database/database.py """

import mock

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.person import ClientCategory
from stoqlib.database.queryexecuter import (QueryExecuter,
                                            StringQueryState)


class QueryExecuterTest(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self.qe = QueryExecuter(self.store)
        self.qe.set_search_spec(ClientCategory)
        self.sfilter = mock.Mock()
        self.qe.set_filter_columns(self.sfilter, ['name'])

    def _search_string_all(self, text):
        return self.qe.search([
            StringQueryState(filter=self.sfilter,
                             mode=StringQueryState.CONTAINS_ALL,
                             text=text)])

    def _search_string_exactly(self, text):
        return self.qe.search([
            StringQueryState(filter=self.sfilter,
                             mode=StringQueryState.CONTAINS_EXACTLY,
                             text=text)])

    def _search_string_not(self, text):
        return self.qe.search([
            StringQueryState(filter=self.sfilter,
                             mode=StringQueryState.NOT_CONTAINS,
                             text=text)])

    def test_string_query(self):
        self.assertEquals(self.store.find(ClientCategory).count(), 0)
        self.create_client_category(u'EYE MOON FLARE 110 0.5')
        self.create_client_category(u'EYE MOON FLARE 120 1.0')
        self.create_client_category(u'EYE SUN FLARE 120 1.0')
        self.create_client_category(u'EYE SUN FLARE 110 1.0')
        self.create_client_category(u'EYE SUN STONE 120 0.5')

        self.assertEquals(self._search_string_all(u'eye flare 110').count(), 2)
        self.assertEquals(self._search_string_all(u'eye 0.5').count(), 2)
        self.assertEquals(self._search_string_all(u'eye 120').count(), 3)

        self.assertEquals(self._search_string_exactly(u'eye flare 110').count(), 0)
        self.assertEquals(self._search_string_exactly(u'eye 0.5').count(), 0)
        self.assertEquals(self._search_string_exactly(u'eye 120').count(), 0)

        self.assertEquals(self._search_string_not(u'stone 110').count(), 2)
        self.assertEquals(self._search_string_not(u'eye').count(), 0)
        self.assertEquals(self._search_string_not(u'moon 120').count(), 1)
