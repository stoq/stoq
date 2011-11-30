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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import platform

import gtk
from kiwi.enums import ListType
from kiwi.ui.widgets.list import Column
from stoqdrivers.interfaces import ICouponPrinter
from stoqdrivers.printers.base import get_supported_printers_by_iface
from stoqdrivers.enum import PaymentMethodType, TaxType

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.domain.till import Till
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.dialogs.progressdialog import ProgressDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.devicemanager import DeviceManager
from stoqlib.lib.message import info, yesno, warning
from stoqlib.lib.parameters import sysparam
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
    proxy_widgets = ['device_name', 'device_serial', 'is_active',
                     'user_number', 'register_date', 'register_cro']

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
        if platform.system() == 'Windows':
            model.device_name = 'COM1'
        model.model_name = None
        return model

    def setup_proxies(self):
        self._populate_printers()
        self._populate_serial_ports()
        self.proxy = self.add_proxy(self.model,
                                    ECFEditor.proxy_widgets)
        self.printer.select_item_by_label(self.model.get_description())

    def validate_confirm(self):
        if not self.can_activate_printer():
            return False

        if self.edit_mode:
            return True
        self._status = ECFAsyncPrinterStatus(self.model.device_name,
                                       self.model.printer_class)
        self._status.connect('reply', self._printer_status__reply)
        self._status.connect('timeout', self._printer_status__timeout)
        self.progress_dialog.set_label(_("Probing for a %s printer on %s") % (
            self.model.model_name, self._status.get_device_name()))
        self.progress_dialog.start()
        return False

    def can_activate_printer(self):
        serial = self.model.device_serial
        printers = ECFPrinter.selectBy(is_active=True,
                                       station=get_current_station(self.conn))
        till = Till.selectOneBy(status=Till.STATUS_OPEN,
                             station=get_current_station(self.conn))
        if till and printers:
            warning(_("You need to close the till opened at %s before "
                      "changing this printer.") % till.opening_date.date())
            return False
        for p in printers:
            if p.device_serial != serial and self.model.is_active:
                warning(_(u'The ECF %s is already active for this '
                          'station. Deactivate that printer before '
                          'activating this one.') % p.model)
                return False
        return True

    #
    # Callbacks
    #

    def _on_progress_dialog__cancel(self, progress):
        # FIXME:
        #status.stop()
        pass

    def on_printer__content_changed(self, combo):
        # Cannot change the model in edit mode!
        if self.edit_mode:
            return
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

        if not yesno(_("An ECF Printer was added. You need to restart Stoq "
                       "before using it. Would you like to restart it now?"),
                     gtk.RESPONSE_NO, _("Restart later"), _("Restart now")):
            self.conn.commit()
            raise SystemExit

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

        if sysparam(self.conn).DEMO_MODE:
            from stoqdrivers.printers.virtual.Simple import Simple
            printer = _PrinterModel('virtual', Simple)
            printers.append((printer.get_description(), printer))

        self.printer.prefill(sorted(printers))

    def _populate_serial_ports(self):
        values = []
        for device in self._device_manager.get_serial_devices():
            values.append(device.device_name)
        if not self.model.device_name in values:
            values.append(self.model.device_name)
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
                # If the constant is not defined in the system, create it
                if not constant:
                    constant = SellableTaxConstant(tax_value=value,
                                           tax_type=int(TaxType.CUSTOM),
                                           description='%d %%' % value,
                                           connection=self.conn)
            elif tax_enum == TaxType.SERVICE:
                constant = DeviceConstant.selectOneBy(
                    constant_enum=int(tax_enum),
                    printer=model,
                    connection=self.conn)
                # Skip, If we have a service tax defined for this printer
                # This needs to be improved when we support more than one
                # service tax
                if constant is not None:
                    continue
            else:
                constant = SellableTaxConstant.selectOneBy(
                    tax_type=int(tax_enum), connection=self.conn)
                # Ignore if its unkown tax
                if not constant:
                    continue

            if value:
                constant_name = '%d %%' % (value, )
            elif constant:
                constant_name = constant.description
            else:
                constant_name = None
            DeviceConstant(constant_enum=int(tax_enum),
                           constant_name=constant_name,
                           constant_type=DeviceConstant.TYPE_TAX,
                           constant_value=value,
                           device_value=device_value,
                           printer=model,
                           connection=self.conn)

        # This is going to be ugly, most printers don't support
        # a real constant for the payment methods, so we have to look
        # at the description and guess
        payment_enums = {'dinheiro': PaymentMethodType.MONEY,
                         'cheque': PaymentMethodType.CHECK,
                         'boleto': PaymentMethodType.BILL,
                         'cartao credito': PaymentMethodType.CREDIT_CARD,
                         'cartao debito': PaymentMethodType.DEBIT_CARD,
                         'financeira': PaymentMethodType.FINANCIAL,
                         'vale compra': PaymentMethodType.GIFT_CERTIFICATE
                          }

        for device_value, constant_name in driver.get_payment_constants():
            lower = constant_name.lower()
            lower = lower.replace('é', 'e') # Workaround method names with
            lower = lower.replace('ã', 'a') # accents
            payment_enum = payment_enums.get(lower)
            if payment_enum is None:
                continue

            DeviceConstant(constant_enum=int(payment_enum),
                           constant_name=constant_name,
                           constant_type=DeviceConstant.TYPE_PAYMENT,
                           constant_value=value,
                           device_value=device_value,
                           printer=model,
                           connection=self.conn)


class ECFListDialog(ModelListDialog):
    title = _('Fiscal Printers')
    size = (600, 250)
    editor_class = ECFEditor

    columns = [
        Column('description', title=_('Model'), data_type=str, expand=True),
        Column('device_serial', title=_('Serial'), data_type=str, width=100),
        Column('station.name', title=_('Computer'), data_type=str, width=100),
        Column('is_active', title=_('Active'), data_type=bool, width=60),
        ]

    model_type = ECFPrinter

    def __init__(self):
        ModelListDialog.__init__(self)
        self.set_list_type(ListType.UNREMOVABLE)

    # ModelListDialog

    def populate(self):
        return ECFPrinter.selectBy(
            station=get_current_station(self.conn),
            connection=self.conn)

    def edit_item(self, item):
        if item.brand == 'virtual':
            info(_("Cant edit a virtual printer"))
            return False
        return ModelListDialog.edit_item(self, item)
