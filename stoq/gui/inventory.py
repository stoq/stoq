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

from stoqlib.api import api
from stoqlib.domain.interfaces import IBranch
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.person import Person
from stoqlib.domain.product import ProductStockItem
from stoqlib.exceptions import DatabaseInconsistency
from stoq.gui.application import SearchableAppWindow
from stoqlib.gui.dialogs.openinventorydialog import OpenInventoryDialog
from stoqlib.gui.dialogs.productadjustmentdialog import ProductsAdjustmentDialog
from stoqlib.gui.dialogs.productcountingdialog import ProductCountingDialog
from stoqlib.lib.message import warning, yesno
from stoqlib.reporting.product import ProductCountingReport

_ = gettext.gettext


class InventoryApp(SearchableAppWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_name = _('Inventory')
    app_icon_name = 'stoq-inventory-app'
    gladefile = "inventory"
    search_table = Inventory
    search_labels = _('Matching:')
    launcher_embedded = True

    #
    # Application
    #

    def create_actions(self):
        actions = [
            ('menubar', None, ''),
            # Inventory
            ('NewInventory', None, _('Open I_nventry'), '<Control>i',
             _('Create a new inventory for product counting')),
            ('CountingAction', gtk.STOCK_INDEX, _('_Count inventory...'),
             '<Control>c',
             _('Register the actual stock of products in the selected '
               'inventory')),
            ('AdjustAction', gtk.STOCK_CONVERT, _('_Adjust inventory...'),
             '<Control>a',
             _('Adjust the stock accordingly to the counting in the selected '
               'inventory')),
            ('Cancel', gtk.STOCK_CANCEL, _('Cancel inventory'), '',
             _('Cancel the selected inventory')),
            ('Print', gtk.STOCK_PRINT, _('Print inventory'), '',
             _('Print the product listing for the selected inventory '
               'to be used for counting')),
            ('ExportCSV', gtk.STOCK_SAVE_AS, _('Export CSV...')),
        ]
        self.inventory_ui = self.add_ui_actions('', actions,
                                                filename='inventory.xml')
        self.set_help_section(_("Inventory help"),
                              'inventario-inicio')

        self.AdjustAction.set_short_label(_("Adjust"))
        self.CountingAction.set_short_label(_("Count"))
        self.Cancel.set_short_label(_("Cancel"))
        self.AdjustAction.props.is_important = True
        self.CountingAction.props.is_important = True
        self.Cancel.props.is_important = True

    def create_ui(self):
        self.app.launcher.add_new_items([self.NewInventory])

    def activate(self):
        self.search.refresh()
        self._update_widgets()

    def deactivate(self):
        self.uimanager.remove_ui(self.inventory_ui)

    def new_activate(self):
        if not self.NewInventory.get_sensitive():
            warning(_("You cannot open an inventory without having a "
                      "branch with stock in it."))
            return
        self._open_inventory()

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

        self.set_sensitive([self.Print], has_open)
        self.set_sensitive([self.Cancel], has_open and not has_adjusted)
        self.set_sensitive([self.NewInventory], self._can_open())
        self.set_sensitive([self.CountingAction], has_open)
        self.set_sensitive([self.AdjustAction], has_open and all_counted)
        self.app.launcher.set_new_menu_sensitive(self._can_open())

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
        trans = api.new_transaction()
        branches = self._get_available_branches_to_inventory()
        model = self.run_dialog(OpenInventoryDialog, trans, branches)
        api.finish_transaction(trans, model)
        trans.close()
        self.refresh()
        self._update_widgets()

    def _cancel_inventory(self):
        if yesno(_('Are you sure you want to cancel this inventory ?'),
                 gtk.RESPONSE_YES, _("Don't cancel"), _("Cancel inventory")):
            return

        trans = api.new_transaction()
        inventory = trans.get(self.results.get_selected())
        inventory.cancel()
        trans.commit()
        self.refresh()
        self._update_widgets()

    def _register_product_counting(self):
        trans = api.new_transaction()
        inventory = trans.get(self.results.get_selected())
        model = self.run_dialog(ProductCountingDialog, inventory, trans)
        api.finish_transaction(trans, model)
        trans.close()
        self.refresh()
        self._update_widgets()

    def _adjust_product_quantities(self):
        trans = api.new_transaction()
        inventory = trans.get(self.results.get_selected())
        model = self.run_dialog(ProductsAdjustmentDialog, inventory, trans)
        api.finish_transaction(trans, model)
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

    def on_NewInventory__activate(self, action):
        self._open_inventory()

    def on_CountingAction__activate(self, action):
        self._register_product_counting()

    def on_AdjustAction__activate(self, action):
        self._adjust_product_quantities()

    def on_results__selection_changed(self, results, product):
        self._update_widgets()

    def on_Cancel__activate(self, widget):
        self._cancel_inventory()

    def on_Print__activate(self, button):
        selected = self.results.get_selected()
        sellables = list(self._get_sellables_by_inventory(selected))
        if not sellables:
            warning(_("No products found in the inventory."))
            return
        self.print_report(ProductCountingReport, sellables)
