# -*- coding: utf-8 -*-
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

from decimal import Decimal

from stoqlib.lib.dateutils import localdate
from stoqlib.domain.till import TillClosedView
from stoqlib.gui.dialogs.tilldetails import TillDetailsDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestTillDetailsDialog(GUITest):

    def test_show(self):
        till = self.create_till()
        till.open_till()
        till.close_till(u"Observation...")
        till.opening_date = localdate(2014, 5, 6).date()
        till.closing_date = localdate(2014, 5, 6).date()
        till.responsible_open_id = self.create_user().id
        till.initial_cash_amount = Decimal(5656.64)
        till.final_cash_amount = Decimal(246823.22)

        model = self.store.find(TillClosedView, id=till.id).one()

        dialog = TillDetailsDialog(self.store, model)
        self.check_dialog(dialog, 'till-details-dialog-show')
