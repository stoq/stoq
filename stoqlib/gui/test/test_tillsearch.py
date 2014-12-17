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

import mock
from decimal import Decimal

from stoqlib.database.runtime import get_current_user
from stoqlib.lib.dateutils import localdate
from stoqlib.domain.till import TillClosedView
from stoqlib.gui.search.tillsearch import TillClosedSearch
from stoqlib.gui.dialogs.tilldetails import TillDetailsDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.test.uitestutils import GUITest


class TestTillSearch(GUITest):

    def test_show(self):
        dialog = TillClosedSearch(self.store)
        self.check_dialog(dialog, 'till-closed-search-show')

    def test_date_search(self):
        till1 = self.create_till()
        till1.open_till()
        till1.close_till(u"Bla")
        till1.opening_date = localdate(2014, 1, 1).date()
        till1.closing_date = localdate(2014, 1, 1).date()
        till1.responsible_open_id = self.create_user().id
        till1.initial_cash_amount = Decimal(66.43)
        till1.final_cash_amount = Decimal(12366.43)

        till2 = self.create_till()
        till2.open_till()
        till2.close_till(u"TESTE")
        till2.opening_date = localdate(2014, 2, 3).date()
        till2.closing_date = localdate(2014, 2, 3).date()
        till2.initial_cash_amount = Decimal(6734.43)
        till2.final_cash_amount = Decimal(347347.11)

        dialog = TillClosedSearch(self.store)
        dialog.date_filter.select(DateSearchFilter.Type.USER_DAY)
        dialog.date_filter.start_date.update(till1.closing_date)
        self.click(dialog.search.search_button)
        self.check_dialog(dialog, 'till-closed-search-day')

    def test_run_dialog(self):
        observations = (
            u"Mussum ipsum cacilds, vidis litro abertis. "
            "Consetis adipiscings elitis. Pra la , depois "
            "divoltis porris, paradis. Paisis, filhis, "
            "espiritis santis. Me faiz elementum girarzis, "
            "nisi eros vermeio, in elementis me pra quem e "
            "amistosis quis leo. Manduma pindureta quium dia "
            "nois paga. Sapien in monti palavris qui num "
            "significa nadis i pareci latim. Interessantiss "
            "quisso pudia ce receita de bolis, mais bolis eu num gostis.")
        till = self.create_till()
        till.open_till()
        till.close_till(observations)

        model = self.store.find(TillClosedView, id=till.id).one()
        self.assertEquals(observations, model.observations)
        self.assertEquals(get_current_user(self.store).get_description(),
                          model.responsible_open_name)
        self.assertEquals(get_current_user(self.store).get_description(),
                          model.responsible_close_name)
        self.assertEquals(observations, model.observations)

        dialog = TillClosedSearch(self.store)
        dialog.search.refresh()
        self.assertNotSensitive(dialog._details_slave, ['details_button'])
        with mock.patch("stoqlib.gui.search.tillsearch.run_dialog") as r_dialog:
            dialog.results.select(model)
            self.assertSensitive(dialog._details_slave, ['details_button'])
            self.click(dialog._details_slave.details_button)
            r_dialog.assert_called_once_with(TillDetailsDialog, dialog,
                                             dialog.store, model)
