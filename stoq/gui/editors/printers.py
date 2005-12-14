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
## Author(s): Henrique Romano <henrique@async.com.br>
##
"""
stoq/gui/editors/printers.py:

    Editors implementation for fiscal and cheque printers.
"""

import gettext

from kiwi.ui.widgets.list import Column
from stoqdrivers.devices.printers.base import get_supported_printers
from stoqlib.gui.editors import BaseEditor
from stoqlib.gui.lists import AdditionListDialog

from stoq.domain.drivers import PrinterSettings

_ = gettext.gettext

class PrinterSettingsEditor(BaseEditor):
    gladefile = 'PrinterSettingsEditor'
    model_name = 'Printer'
    model_type = PrinterSettings
    widgets = ('brand_combo',
               'device_combo',
               'model_combo',
               'host')

    def __init__(self, conn, model=None):
        self.printers_dict = get_supported_printers()
        BaseEditor.__init__(self, conn, model)

    def setup_brand_combo(self):
        self.brands = [(brand.capitalize(), brand)
                           for brand in self.printers_dict.keys()]
        self.brand_combo.prefill(self.brands)

    def update_model_combo(self):
        self.model_combo.clear()
        if self.model.brand is not None:
            brand = self.model.brand
        else:
            items = self.brand_combo.get_model_items()
            if not items:
                raise ValueError('Brand combo must have items at this point')
            brand = items.values()[0]
        model_list = self.printers_dict[brand.lower()]
        models = [(model.printer_name, model.__name__)
                      for model in model_list]
        self.model_combo.prefill(models)

    def setup_device_combo(self):
        device_types = (PrinterSettings.DEVICE_SERIAL1,
                        PrinterSettings.DEVICE_SERIAL2,
                        PrinterSettings.DEVICE_PARALLEL)
        items = [(self.model.get_device_description(device), device)
                     for device in device_types]
        self.device_combo.prefill(items)

    def setup_widgets(self):
        self.setup_brand_combo()
        self.setup_device_combo()
        self.update_model_combo()

    #
    # BaseEditor hooks
    #
    
    def setup_proxies(self):
        self.setup_widgets()
        self.proxy = self.add_proxy(model=self.model, widgets=self.widgets)

    def create_model(self, conn):
        return PrinterSettings(connection=conn)

    def get_title(self, *args):
        if self.edit_mode:
            return _("Edit Printer Settings")
        else:
            return _("Add Printer Settings")

    # FIXME: this part will improved when bug #2334 is fixed.
    def on_confirm(self):
        self.conn.commit()
        return self.model

    #
    # Kiwi callbacks
    #

    def on_brand_combo__changed(self, *args):
        self.update_model_combo()


class PrinterSettingsDialog(AdditionListDialog):
    size = (600, 500)
    def __init__(self, conn):
        AdditionListDialog.__init__(self, conn, PrinterSettingsEditor,
                                    self.get_columns(), self.get_items(conn),
                                    title=_("Printer Settings"))
        self.set_before_delete_items(self.before_delete_items)

    #
    # Helper methods
    #

    def get_columns(self):
        return [Column('printer_description', _('Printer'), data_type=str,
                       sorted=True, expand=True),
                Column('device_description', _('Device'), data_type=str,
                       width=150),
                Column('host', _('Host'), data_type=str, width=150)]

    def get_items(self, conn):
        return PrinterSettings.select(connection=conn)

    #
    # Callbacks
    #

    def before_delete_items(self, list_slave, items):
        table = PrinterSettings
        for item in items:
            table.delete(item.id, connection=self.conn)
        self.conn.commit()
