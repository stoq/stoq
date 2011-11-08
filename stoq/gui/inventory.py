# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
""" Main gui definition for inventory application. """

import gettext
import datetime
import gtk

from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import Column, SearchColumn

from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.interfaces import IBranch
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.person import Person
from stoqlib.domain.product import ProductStockItem
from stoqlib.exceptions import DatabaseInconsistency
from stoq.gui.application import SearchableAppWindow
from stoqlib.gui.dialogs.openinventorydialog import OpenInventoryDialog
from stoqlib.gui.dialogs.productadjustmentdialog import ProductsAdjustmentDialog
from stoqlib.gui.dialogs.productcountingdialog import ProductCountingDialog
from stoqlib.lib.message import yesno
from stoqlib.reporting.product import ProductCountingReport

_ = gettext.gettext


class InventoryApp(SearchableAppWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_name = _('Inventory')
    app_icon_name = 'stoq-inventory-app'
    gladefile = "inventory"
    search_table = Inventory
    search_labels = _('Matching:')

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._update_widgets()

    #
    # Application
    #

    def create_actions(self):
        ui_string = """<ui>
         <menubar action="menubar">
            <menu action="InventoryMenu">
              <menuitem action="new_inventory"/>
              <menuitem action="counting_action"/>
              <menuitem action="adjust_action"/>
              <separator name="sep"/>
              <menuitem action="ExportCSV"/>
              <separator name="sep2"/>
              <menuitem action="Quit"/>
            </menu>
         </menubar>
         <toolbar action="main_toolbar">
           <toolitem action="counting_action"/>
           <toolitem action="adjust_action"/>
         </toolbar>
        </ui>"""

        actions = [
            ('menubar', None, ''),
            # Inventory
            ("InventoryMenu", None, _("Inventory")),
            ('new_inventory', None, _('Open I_nventry'), '<Control>i'),
            ('counting_action', gtk.STOCK_INDEX, _('_Count inventory...'),
             '<Control>a'),
            ('adjust_action', gtk.STOCK_CONVERT, _('_Adjust inventory...'),
             '<Control>c'),
            ('ExportCSV', gtk.STOCK_SAVE_AS, _('Export CSV...')),
            ("Quit", gtk.STOCK_QUIT),

        ]
        self.add_ui_actions(ui_string, actions)
        self.adjust_action.set_short_label(_("Adjust"))
        self.counting_action.set_short_label(_("Count"))
        self.add_help_ui(_("Inventory help"), 'inventario-inicio')
        self.add_user_ui()

    def create_ui(self):
        self.menubar = self.uimanager.get_widget('/menubar')
        self.main_vbox.pack_start(self.menubar, False, False)
        self.main_vbox.reorder_child(self.menubar, 0)

        self.main_toolbar = self.uimanager.get_widget('/main_toolbar')
        self.main_vbox.pack_start(self.main_toolbar, False, False)
        self.main_vbox.reorder_child(self.main_toolbar, 1)

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        # Disable string search right now, until we use a proper Viewable
        # for this application
        self.disable_search_entry()
        self.branch_filter = ComboSearchFilter(
            _('Show inventories at:'), self._get_branches_for_filter())
        self.add_filter(self.branch_filter,
                        position=SearchFilterPosition.TOP,
                        columns=["branchID"])

    def get_columns(self):
        return [SearchColumn('id', title=_('Code'), sorted=True,
                       order=gtk.SORT_DESCENDING,
                       data_type=int, format='%03d', width=80),
                SearchColumn('status_str', title=_('Status'),
                             data_type=str, width=100,
                             valid_values=self._get_status_values(),
                             search_attribute='status'),
                Column('branch.person.name', title=_('Branch'),
                       data_type=str, expand=True),
                SearchColumn('open_date', title=_('Opened'),
                       long_title='Date Opened',
                       data_type=datetime.date, width=120),
                SearchColumn('close_date', title=_(u'Closed'),
                       long_title='Date Closed',
                       data_type=datetime.date, width=120)]

    #
    # Private API
    #

    def _get_status_values(self):
        values = [(v, k) for k, v in Inventory.statuses.items()]
        values.insert(0, (_("Any"), None))
        return values

    def _get_branches(self):
        return Person.iselect(IBranch, connection=self.conn)

    def _get_branches_for_filter(self):
        items = [(b.person.name, b.id) for b in self._get_branches()]
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        items.insert(0, [_('All branches'), None])
        return items

    def _update_widgets(self):
        has_open = False
        all_counted = False
        has_adjusted = False
        selected = self.results.get_selected()
        if selected:
            all_counted = selected.all_items_counted()
            has_open = selected.is_open()
            has_adjusted = selected.has_adjusted_items()

        self.print_button.set_sensitive(has_open)
        self.cancel_button.set_sensitive(has_open and not has_adjusted)
        self.new_inventory.set_sensitive(self._can_open())
        self.counting_action.set_sensitive(has_open)
        self.adjust_action.set_sensitive(has_open and all_counted)

    def _get_available_branches_to_inventory(self):
        """Returns a list of branches where we can open an inventory.
        Note that we can open a inventory if:
            - There's no inventory opened yet (in the same branch)
            - The branch must have some stock
        """
        available_branches = []
        for branch in self._get_branches():
            has_open_inventory = Inventory.has_open(self.conn, branch)
            if not has_open_inventory:
                stock = ProductStockItem.selectBy(branch=branch,
                                                  connection=self.conn)
                if stock.count() > 0:
                    available_branches.append(branch)

        return available_branches

    def _can_open(self):
        # we can open an inventory if we have at least one branch
        # available
        return bool(self._get_available_branches_to_inventory())

    def _open_inventory(self):
        trans = new_transaction()
        branches = self._get_available_branches_to_inventory()
        model = self.run_dialog(OpenInventoryDialog, trans, branches)
        finish_transaction(trans, model)
        trans.close()
        self.refresh()
        self._update_widgets()

    def _cancel_inventory(self):
        if yesno(_('Are you sure you want to cancel this inventory ?'),
                 gtk.RESPONSE_YES, _("Don't cancel"), _("Cancel inventory")):
            return

        trans = new_transaction()
        inventory = trans.get(self.results.get_selected())
        inventory.cancel()
        trans.commit()
        self.refresh()
        self._update_widgets()

    def _register_product_counting(self):
        trans = new_transaction()
        inventory = trans.get(self.results.get_selected())
        model = self.run_dialog(ProductCountingDialog, inventory, trans)
        finish_transaction(trans, model)
        trans.close()
        self.refresh()
        self._update_widgets()

    def _adjust_product_quantities(self):
        trans = new_transaction()
        inventory = trans.get(self.results.get_selected())
        model = self.run_dialog(ProductsAdjustmentDialog, inventory, trans)
        finish_transaction(trans, model)
        trans.close()
        self.refresh()
        self._update_widgets()

    def _update_filter_slave(self, slave):
        self.refresh()

    def _get_sellables_by_inventory(self, inventory):
        for item in inventory.get_items():
            yield item.product.sellable

    #
    # Callbacks
    #

    def on_new_inventory__activate(self, action):
        self._open_inventory()

    def on_counting_action__activate(self, action):
        self._register_product_counting()

    def on_adjust_action__activate(self, action):
        self._adjust_product_quantities()

    def on_results__selection_changed(self, results, product):
        self._update_widgets()

    def on_cancel_button__clicked(self, widget):
        self._cancel_inventory()

    def on_print_button__clicked(self, button):
        selected = self.results.get_selected()
        sellables = list(self._get_sellables_by_inventory(selected))
        if sellables:
            self.print_report(ProductCountingReport, sellables)
