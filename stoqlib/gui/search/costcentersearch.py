# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""Search class for |costcenter| objects"""

from kiwi.currency import currency

from stoqlib.domain.costcenter import CostCenter
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.editors.costcentereditor import CostCenterEditor
from stoqlib.gui.dialogs.costcenterdialog import CostCenterDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CostCenterSearch(SearchEditor):
    title = _('Search for cost centers')
    size = (-1, 300)
    search_spec = CostCenter
    editor_class = CostCenterEditor

    def create_filters(self):
        self.set_text_field_columns(['name', 'description'])

    def get_columns(self):
        return [
            SearchColumn('name', title=_('Name'), data_type=str, sorted=True,
                         expand=True),
            SearchColumn('budget', title=_('Budget'), data_type=currency),
            SearchColumn('is_active', title=_('Active'), data_type=bool),
        ]

    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        if selected:
            run_dialog(CostCenterDialog, self, self.store, selected)

    def row_activate(self, obj):
        run_dialog(CostCenterDialog, self, self.store, obj)


def test():  # pragma: no cover
    from stoqlib.api import api
    ec = api.prepare_test()
    run_dialog(CostCenterSearch, None, ec.store)


if __name__ == '__main__':
    test()
