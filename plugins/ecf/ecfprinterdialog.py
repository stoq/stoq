# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s): Johan Dahlin    <jdahlin@async.com.br>
##
##

from kiwi.enums import ListType
from kiwi.ui.widgets.list import Column
from stoqdrivers.devices.interfaces import ICouponPrinter
from stoqdrivers.devices.printers.base import get_supported_printers_by_iface
from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.dialogs.progressdialog import ProgressDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.devicemanager import DeviceManager
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext

from ecfprinterstatus import ECFAsyncPrinterStatus
from ecfdomain import ECFPrinter, DeviceConstant
from deviceconstanteditor import DeviceConstantsDialog

_ = stoqlib_gettext


class _PrinterModel(object):
    def __init__(self, brand, printer_class):
        self.brand = brand
        self.model = printer_class.__name__
        self.model_name = printer_class.model_name
        self.printer_class = printer_class

    def get_description(self):
        return '%s %s' % (self.brand.capitalize(), self.model)


class ECFEditor(BaseEditor):
    gladefile = 'FiscalPrinterDialog'
    model_type = ECFPrinter
    model_name = _('Fiscal Printer')
    proxy_widgets = ['device_name',
                     'device_serial',
                     'is_active']

    def __init__(self, conn, model=None):
        self._device_manager = DeviceManager()
        BaseEditor.__init__(self, conn, model)
        self.progress_dialog = ProgressDialog()
        self.progress_dialog.connect('cancel',
                                     self._on_progress_dialog__cancel)
        self.progress_dialog.set_transient_for(self.main_dialog)

        if self.edit_mode:
            self.printer.set_sensitive(False)
            self.main_dialog.ok_button.grab_focus()
        else:
            self.edit_constants.hide()
            self.device_serial.hide()
            self.device_serial_label.hide()
            self.is_active.hide()

    #
    # BaseEditor
    #

    def create_model(self, conn):
        model = ECFPrinter(brand='daruma',
                           model='FS345',
                           device_name='/dev/ttyS0',
                           device_serial='',
                           station=get_current_station(conn),
                           is_active=True,
                           connection=conn)
        model.model_name = None
        return model

    def setup_proxies(self):
        self._populate_printers()
        self._populate_serial_ports()
        self.proxy = self.add_proxy(self.model,
                                    ECFEditor.proxy_widgets)
        self.printer.select_item_by_label(self.model.get_description())

    def validate_confirm(self):
        if self.edit_mode:
            return True
        status = ECFAsyncPrinterStatus(self.model.device_name,
                                       self.model.printer_class)
        status.connect('reply', self._printer_status__reply)
        status.connect('timeout', self._printer_status__timeout)
        self.progress_dialog.set_label(_("Probing for a %s printer on %s" % (
            self.model.model_name, status.get_device_name())))
        self.progress_dialog.start()
        return False

    #
    # Callbacks
    #

    def _on_progress_dialog__cancel(self, progress):
        # FIXME:
        #status.stop()
        pass

    def on_printer__content_changed(self, combo):
        printer = combo.get_selected()
        self.model.model = printer.model
        self.model.brand = printer.brand

        # These are not persistent
        self.model.model_name = printer.model_name
        self.model.printer_class = printer.printer_class

    def on_edit_constants__clicked(self, button):
        run_dialog(DeviceConstantsDialog, self, self.conn, self.model)

    def _printer_status__reply(self, status, reply):
        self.progress_dialog.stop()
        if not self._populate_ecf_printer(status):
            return

        # FIXME: move to base dialogs or base editor
        self.main_dialog.retval = self.model
        self.main_dialog.close()

    def _printer_status__timeout(self, status):
        self.progress_dialog.stop()
        info(_("Could not find a %s printer connected to %s") % (
            self.model.model_name, status.get_device_name()))

    #
    # Private
    #

    def _populate_printers(self):
        supported_ifaces = get_supported_printers_by_iface(ICouponPrinter).items()
        printers = []
        for brand, printer_classes in supported_ifaces:
            for printer_class in printer_classes:
                printer = _PrinterModel(brand, printer_class)
                printers.append((printer.get_description(), printer))
        self.printer.prefill(sorted(printers))

    def _populate_serial_ports(self):
        values = []
        for device in self._device_manager.get_serial_devices():
            values.append(device.device_name)
        self.device_name.prefill(values)

    def _populate_ecf_printer(self, status):
        serial = status.printer.get_serial()
        if ECFPrinter.selectBy(device_serial=serial, connection=self.conn):
            status.stop()
            status.get_port().close()
            info(_("This printer is already known to the system"))
            return False
        self.model.device_serial = serial
        self._populate_constants(self.model, status)
        return True

    def _populate_constants(self, model, status):
        driver = status.get_driver()
        for tax_enum, device_value, value in driver.get_tax_constants():
            if tax_enum == TaxType.CUSTOM:
                constant = SellableTaxConstant.selectOneBy(
                    tax_value=value, connection=self.conn)
                # Do not import constants which are not defined by the system
                if not constant:
                    continue

            if value:
                constant_name = '%d %%' % (value,)
            else:
                constant_name = None
            DeviceConstant(constant_enum=int(tax_enum),
                           constant_name=constant_name,
                           constant_type=DeviceConstant.TYPE_TAX,
                           constant_value=value,
                           device_value=device_value,
                           printer=model,
                           connection=self.conn)

class ECFListDialog(ModelListDialog):
    title = _('Fiscal Printers')
    size = (600, 250)
    editor_class = ECFEditor

    columns =  [
        Column('description', title=_('Model'), data_type=str, expand=True),
        Column('device_serial', title=_('Serial'), data_type=str, width=100),
        Column('station.name', title=_('Station'), data_type=str, width=100),
        Column('is_active', title=_('Active'), data_type=bool, width=60),
        ]

    model_type = ECFPrinter

    def __init__(self):
        ModelListDialog.__init__(self)
        self.set_list_type(ListType.UNREMOVABLE)

    def populate(self):
        return ECFPrinter.selectBy(
            station=get_current_station(self.conn),
            connection=self.conn)
