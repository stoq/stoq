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

from stoq.gui.till import TillApp
from stoq.gui.test.baseguitest import BaseGUITest

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.sale import Sale


class TestTill(BaseGUITest):
    def testInitial(self):
        app = self.create_app(TillApp, 'till')
        self.check_app(app, 'till')

    def testSelect(self):
        sale = self.create_sale(branch=get_current_branch(self.trans))
        self.add_product(sale)
        sale.status = Sale.STATUS_CONFIRMED

        app = self.create_app(TillApp, 'till')
        results = app.main_window.results
        results.select(results[0])
