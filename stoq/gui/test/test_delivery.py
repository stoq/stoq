# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import datetime

from stoq.gui.delivery import DeliveryApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestServices(BaseGUITest):
    def test_initial(self):
        for i in range(2):
            sale = self.create_sale()
            sale.identifier = 666 + i
            self.add_product(sale)

            delivery = self.create_delivery()
            delivery.open_date = datetime.datetime(2017, 1, 1)
            delivery.invoice_id = sale.invoice_id

        app = self.create_app(DeliveryApp, u'delivery')
        self.assertEqual(len(app.results), 2)

        self.check_app(app, u'delivery')
