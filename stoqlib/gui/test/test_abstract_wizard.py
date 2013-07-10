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

import mock
from stoqlib.domain.views import ProductFullStockView
from stoqlib.domain.sellable import Sellable
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.wizards.abstractwizard import AdvancedSellableSearch

from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestAbstractWizard(GUITest):
    @mock.patch('stoqlib.gui.search.searcheditor.api.new_store')
    @mock.patch('stoqlib.gui.search.searcheditor.run_dialog')
    def test_run_editor(self, run_dialog, new_store):
        run_dialog.return_value = None
        new_store.return_value = self.store
        query = Sellable.get_unblocked_sellables_query(self.store)
        dialog = AdvancedSellableSearch(store=self.store,
                                        table=ProductFullStockView,
                                        query=query)
        dialog.search.refresh()
        dialog.results.select(dialog.results[0])
        product = dialog.results[0].product

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(dialog._toolbar.edit_button)
                run_dialog.assert_called_once_with(ProductEditor, dialog, self.store, product, visual_mode=False)
