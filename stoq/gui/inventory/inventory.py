# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##              George Kussumoto            <george@async.com.br>
##
""" Main gui definition for inventory application. """

import gettext
from decimal import Decimal
import pango
import gtk

from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.widgets.list import Column

from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.interfaces import IBranch
from stoqlib.domain.person import Person
from stoqlib.domain.views import ProductFullStockView

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class InventoryApp(SearchableAppWindow):
    app_name = _('inventory')
    app_icon_name = 'stoq-inventory-app'
    gladefile = "inventory"
    search_table = ProductFullStockView
    search_labels = _('Matching:')
    klist_selection_mode = gtk.SELECTION_MULTIPLE

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.executer.set_query(self.query)
        self.set_text_field_columns(['description'])
        self.branch_filter = ComboSearchFilter(
            _('Show products at:'), self._get_branches())
        self.branch_filter.select(get_current_branch(self.conn))
        self.add_filter(self.branch_filter, position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [Column('id', title=_('Code'), sorted=True,
                       data_type=int, format='%03d'),
                Column('description', title=_("Description"),
                       data_type=str, expand=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('stock', title=_('Quantity'),
                       data_type=Decimal),
                Column('unit', title=_("Unit"), data_type=str)]

    def query(self, query, conn):
        branch = self.branch_filter.get_state().value
        return self.search_table.select_by_branch(query, branch,
                                                  connection=conn)

    #
    # Private API
    #

    def _setup_widgets(self):
        self.search.set_summary_label(column='stock',
                                      label=_('<b>Stock Total:</b>'),
                                      format='<b>%s</b>')

    def _get_branches(self):
        items = [(b.person.name, b)
                  for b in Person.iselect(IBranch, connection=self.conn)]
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        items.insert(0, [_('All branches'), None])
        return items

    def _update_widgets(self):
        self.print_button.set_sensitive(False)
        self.adjust_button.set_sensitive(False)

    def _update_filter_slave(self, slave):
        self.refresh()

    #
    # Callbacks
    #

    def on_adjust_button__clicked(self, button):
        # To be implemented
        pass

    def on_results__selection_changed(self, results, product):
        self._update_widgets()

    def on_print_button__clicked(self, button):
        # To be implemented
        pass
