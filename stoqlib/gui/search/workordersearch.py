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

import datetime

from kiwi.currency import currency

from stoqlib.domain.workorder import (WorkOrder, WorkOrderView,
                                      WorkOrderFinishedView)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.columns import IdentifierColumn, SearchColumn
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class WorkOrderSearch(SearchDialog):
    """A search for |workorders|"""

    title = _("Search for work orders")
    size = (700, 450)
    search_table = WorkOrderView
    editor_class = WorkOrderEditor

    #
    #  SearchDialog
    #

    def create_filters(self):
        self.set_text_field_columns(['equipment', 'client_name'])

    def get_columns(self):
        return [
            IdentifierColumn('identifier', title=_(u'#'), sorted=True),
            SearchColumn('work_order.status_str', title=_('Status'),
                         search_attribute='status', visible=False,
                         valid_values=self._get_status_values(), data_type=str),
            SearchColumn('equipment', title=_('Equipment'),
                         data_type=str, expand=True),
            SearchColumn('client_name', title=_('Client'),
                         data_type=str),
            SearchColumn('open_date', title=_('Open date'),
                         data_type=datetime.date),
            SearchColumn('approve_date', title=_('Approval date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('finish_date', title=_('Finish date'),
                         data_type=datetime.date),
            SearchColumn('total', title=_('Total'),
                         data_type=currency),
        ]

    #
    #  Private
    #

    def _get_status_values(self):
        return ([(_('Any'), None)] +
                [(v, k) for k, v in WorkOrder.statuses.items()])

    #
    #  Callbacks
    #

    def on_details_button_clicked(self, button):
        work_order_view = self.results.get_selected()
        if not work_order_view:
            return

        run_dialog(WorkOrderEditor, self, self.store,
                   model=work_order_view.work_order, visual_mode=True)


class WorkOrderFinishedSearch(WorkOrderSearch):
    search_table = WorkOrderFinishedView
