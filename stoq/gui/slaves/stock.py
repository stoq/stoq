# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s):  Evandro Vale Miquelito  <evandro@async.com.br>
##
"""
stoq/gui/slaves/stock.py:

    Slaves for stock management
"""

import gobject
from kiwi.utils import gsignal
from stoqlib.gui.editors import BaseEditorSlave
from stoqlib.exceptions import DatabaseInconsistency

from stoq.domain.person import PersonAdaptToBranch
from stoq.lib.defaults import ALL_BRANCHES


class FilterStockSlave(BaseEditorSlave):
    model_type = None
    gladefile = 'FilterStockSlave'
    widgets = ('branch_combo',)
    gsignal('branchcombo-changed')

    def __init__(self, conn):
        BaseEditorSlave.__init__(self, conn)
        self.setup_branch_combo()

    def setup_branch_combo(self):
        table = PersonAdaptToBranch

        branch_list = table.select(connection=self.conn)
        items = [(o.get_adapted().name, o) for o in branch_list]
        items.append(ALL_BRANCHES)
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        self.branch_combo.prefill(items)
        self.branch_combo.select_item_by_data(ALL_BRANCHES[1])
        if len(items) == 1:
            self.branch_combo.set_sensitive(False)

    def get_selected_branch(self):
        return self.branch_combo.get_selected_data()

    def on_branch_combo__content_changed(self, *args):
        self.emit('branchcombo-changed')

gobject.type_register(FilterStockSlave)
