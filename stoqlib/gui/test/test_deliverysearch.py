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

from stoqlib.domain.sale import Delivery
from stoqlib.gui.search.deliverysearch import DeliverySearch
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate


class TestDeliverySearch(GUITest):
    def _show_search(self):
        search = DeliverySearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        address = self.create_address()
        service_item = self.create_sale_item()
        service_item.sale.identifier = 10
        transporter = self.create_transporter(name=u'Hall')
        delivery = Delivery(transporter=transporter,
                            address=address,
                            service_item=service_item,
                            open_date=localdate(2012, 1, 1).date(),
                            store=self.store)
        delivery.tracking_code = u'45'

        service_item = self.create_sale_item()
        service_item.sale.identifier = 20
        transporter = self.create_transporter(name=u'Torvalds')
        delivery = Delivery(transporter=transporter,
                            address=address,
                            service_item=service_item,
                            open_date=localdate(2012, 2, 2).date(),
                            deliver_date=localdate(2012, 3, 3).date(),
                            receive_date=localdate(2012, 4, 4).date(),
                            store=self.store)
        delivery.tracking_code = u'78'
        delivery.status = Delivery.STATUS_RECEIVED

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'delivery-no-filter')

        search.set_searchbar_search_string('45')
        search.search.refresh()
        self.check_search(search, 'delivery-string-filter')

        search.set_searchbar_search_string('')
        search.status_filter.set_state(Delivery.STATUS_RECEIVED)
        search.search.refresh()
        self.check_search(search, 'delivery-status-filter')
