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

from stoqlib.domain.service import Service, ServiceView
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.parameters import sysparam


class TestServiceSearch(GUITest):
    def tearDown(self):
        super(TestServiceSearch, self).tearDown()

        # FIXME: The clean_domain + sysparam override bellow makes the cache
        # keep DELIVERY_SERVICE as None, breaking other tests.
        sysparam.clear_cache()

    def test_search(self):
        self.clean_domain([Service])

        self.create_service(u'Delivery', 25).sellable.code = u'1'
        self.create_service(u'Painting', 12).sellable.code = u'2'

        # clean_domain will remove the delivery service, but SellableSearch
        # needs it to do the "exclude delivery service" logic. In this case,
        # we are working around that and also making sure that this service
        # will appear on the list (this is the only search that should show it)
        with self.sysparam(DELIVERY_SERVICE=self.create_service(u"My Delivery")):
            search = ServiceSearch(self.store)

        search.search.refresh()
        self.check_search(search, 'service-no-filter')

        search.set_searchbar_search_string('e')
        search.search.refresh()
        self.check_search(search, 'service-description-filter')

    def test_get_editor_model(self):
        sellable = self.create_sellable(product=True, description=u'Test')
        service = self.create_service(u'Delivery', 25)
        service.sellable = sellable

        dialog = ServiceSearch(self.store)
        service_item = self.store.find(ServiceView, service_id=service.id).one()
        results = dialog.get_editor_model(model=service_item)
        self.assertEquals(service, results)
