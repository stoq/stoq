# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Production details dialogs """

from decimal import Decimal

import pango
import gtk
from kiwi.ui.widgets.list import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.printing import print_report
from stoqlib.domain.production import ProductionOrder
from stoqlib.reporting.production import ProductionOrderReport

_ = stoqlib_gettext


class ProductionDetailsDialog(BaseEditor):
    gladefile = "ProductionDetailsDialog"
    model_type = ProductionOrder
    title = _("Production Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('branch',
                     'order_number',
                     'open_date',
                     'close_date',
                     'responsible_name',
                     'status_string',)

    def _setup_widgets(self):
        self.production_items.set_columns(self._get_production_items_columns())
        self.materials.set_columns(self._get_material_columns())
        self.services.set_columns(self._get_service_columns())

        self.production_items.add_list(self.model.get_items())
        self.materials.add_list(self.model.get_material_items())
        self.services.add_list(self.model.get_service_items())

    def _get_production_items_columns(self):
        return [Column('description',
                       title=_('Description'),
                       data_type=str, expand=True, searchable=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('quantity', title=_('Quantity'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('produced', title=_('Produced'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('lost', title=_('Lost'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),]

    def _get_material_columns(self):
        return [Column('description',
                       title=_('Description'),
                       data_type=str, expand=True, searchable=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('needed', title=_('Needed'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('lost', title=_('Lost'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('to_purchase', title=_('To Purchase'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('to_make', title=_('To Make'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),]

    def _get_service_columns(self):
        return [Column('description', _("Description"), data_type=str,
                       expand=True, ellipsize=pango.ELLIPSIZE_END),
                Column('quantity', _("Quantity"),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),]

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, ProductionDetailsDialog.proxy_widgets)

    #
    # Kiwi Callbacks
    #

    def on_print_button__clicked(self, widget):
        print_report(ProductionOrderReport, self.model)
