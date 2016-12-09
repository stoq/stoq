# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.sale import SaleView
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.test.uitestutils import GUITest

from ecf.couponnumberslave import CouponNumberSlave


class TestCouponNumberSlave(GUITest):

    def test_show(self):
        sale = self.create_sale()
        # SaleDetailsDialog needs a SaleView model
        model = self.store.find(SaleView, id=sale.id).one()
        slave = CouponNumberSlave(self.store, model)
        self.check_slave(slave, 'slave-couponumber')

    def test_attach_slave(self):
        sale = self.create_sale()
        sale.identifier = 1001
        # SaleDetailsDialog needs a SaleView model
        model = self.store.find(SaleView, id=sale.id).one()
        dialog = SaleDetailsDialog(self.store, model)
        dialog.attach_slave('coupon_number_holder', CouponNumberSlave(self.store, model))
        self.check_dialog(dialog, 'dialog-saledetails-with-couponumberslave')
