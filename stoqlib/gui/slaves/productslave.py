# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano      <henrique@async.com.br>
##              Lincoln Molica       <lincoln@async.com.br>
##              Johan Dahlin         <jdahlin@async.com.br>
##
""" Slaves for products """

from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal
from stoqdrivers.constants import TAX_CUSTOM

from stoqlib.domain.person import PersonAdaptToBranch
from stoqlib.domain.product import ProductAdaptToSellable
from stoqlib.domain.sellable import ASellable, SellableTaxConstant
from stoqlib.lib.defaults import ALL_BRANCHES, ALL_ITEMS_INDEX
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.slaves.filterslave import FilterSlave


_ = stoqlib_gettext


class TributarySituationSlave(BaseEditorSlave):
    gladefile = "TributarySituationSlave"
    proxy_widgets = ("tax_constant",
                     "tax_value")
    model_type = ProductAdaptToSellable


    def __init__(self, conn, model=None):
        self.proxy = None
        BaseEditorSlave.__init__(self, conn, model)

    def _setup_combos(self):
        constants = SellableTaxConstant.select(connection=self.trans)
        self.tax_constant.prefill([(c.description, c)  for c in constants])

    def _update_percentage(self):
        constant = self.tax_constant.get_selected_data()
        self.model.tax_value = constant.tax_value
        if self.proxy:
            self.proxy.update('tax_value')

        if constant.tax_type == TAX_CUSTOM:
            label = '%'
        else:
            label = ''

        self.label_percent.set_label(label)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_combos()
        self.proxy = self.add_proxy(self.model,
                                    TributarySituationSlave.proxy_widgets)
        self._update_percentage()

    def on_tax_constant__changed(self, combo):
        self._update_percentage()

class ProductFilterSlave(GladeSlaveDelegate):
    """A slave which filter a colection of products by branch companies and
    product status.
    """

    gladefile = 'ProductFilterSlave'
    gsignal('status-changed')

    def __init__(self, conn):
        self.conn = conn
        GladeSlaveDelegate.__init__(self)
        self._setup_slaves()

    # the code bellow is duplicated and will be fixed on bug 2651
    # the duplicated code is in slaves/fiscal.py
    def _setup_slaves(self):
        items = ASellable.statuses.items()
        statuses = [(description, identifier)
                       for identifier, description in items]
        statuses.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        self._status_slave = FilterSlave(statuses, selected=ALL_ITEMS_INDEX)
        self._status_slave.set_filter_label(_('with status:'))
        self._status_slave.connect("status-changed",
                                   self._on_entry_status_changed)

        table = PersonAdaptToBranch
        items = [(item.get_description(), item)
                    for item in table.get_active_branches(self.conn)]
        items.insert(0, ALL_BRANCHES)
        self.branch_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.branch_slave.set_filter_label(_('Branch:'))
        self.branch_slave.connect("status-changed", self._on_branch_changed)

        self.attach_slave("status_holder", self._status_slave)
        self.attach_slave("branch_holder", self.branch_slave)

    def get_selected_branch(self):
        # this method name will be fixed on bug 2651
        return self.branch_slave.get_selected_status()

    def get_selected_status(self):
        return self._status_slave.get_selected_status()

    #
    # Callbacks
    #

    def _on_entry_status_changed(self, *args):
        self.emit("status-changed")

    def _on_branch_changed(self, *args):
        self.emit("status-changed")
