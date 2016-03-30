# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
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
""" Base editor for items that can use a tax template"""

import gtk

from stoqlib.domain.taxes import (InvoiceItemCofins,
                                  InvoiceItemIcms,
                                  InvoiceItemPis,
                                  InvoiceItemIpi)
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.taxslave import (InvoiceItemCofinsSlave,
                                         InvoiceItemIcmsSlave,
                                         InvoiceItemIpiSlave,
                                         InvoiceItemPisSlave)
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class InvoiceItemEditor(BaseEditor):
    gladefile = 'InvoiceItemEditor'

    def __init__(self, store, model):
        manager = get_plugin_manager()
        self.nfe_is_active = manager.is_active('nfe')
        self.proxy = None
        self.icms_slave = None
        self.ipi_slave = None
        self.pis_slave = None
        self.cofins_slave = None

        BaseEditor.__init__(self, store, model)

    def setup_widgets(self):
        first_page = self.tabs.get_nth_page(0)
        self.tabs.set_tab_label_text(first_page, _(u"Basic"))
        self._setup_taxes()

    def setup_proxies(self):
        self.setup_widgets()

    def _setup_taxes(self):
        if self.nfe_is_active:
            # FIXME: This is needed due to a lack of migration when pis/cofins
            # taxes were added. Probably icms/ipi shouldn't need to be here
            # but, well, better safe than sorry. Maybe we should consider
            # migrating the missing taxes in the future.
            if self.model.icms_info is None:
                self.model.icms_info = InvoiceItemIcms(store=self.store)
                self.model.icms_info.set_item_tax(self.model)
            if self.model.ipi_info is None:
                self.model.ipi_info = InvoiceItemIpi(store=self.store)
                self.model.ipi_info.set_item_tax(self.model)
            if self.model.pis_info is None:
                self.model.pis_info = InvoiceItemPis(store=self.store)
                self.model.pis_info.set_item_tax(self.model)
            if self.model.cofins_info is None:
                self.model.cofins_info = InvoiceItemCofins(store=self.store)
                self.model.cofins_info.set_item_tax(self.model)

            self.icms_slave = InvoiceItemIcmsSlave(self.store,
                                                   self.model.icms_info,
                                                   self.model)
            self.add_tab(_('ICMS'), self.icms_slave)

            self.ipi_slave = InvoiceItemIpiSlave(self.store,
                                                 self.model.ipi_info,
                                                 self.model)
            self.add_tab(_('IPI'), self.ipi_slave)

            self.pis_slave = InvoiceItemPisSlave(self.store,
                                                 self.model.pis_info,
                                                 self.model)
            self.add_tab(_('PIS'), self.pis_slave)

            self.cofins_slave = InvoiceItemCofinsSlave(self.store,
                                                       self.model.cofins_info,
                                                       self.model)
            self.add_tab(_('COFINS'), self.cofins_slave)

    def add_tab(self, name, slave):
        event_box = gtk.EventBox()
        event_box.set_border_width(6)
        event_box.show()
        self.tabs.append_page(event_box, gtk.Label(name))
        self.attach_slave(name, slave, event_box)
