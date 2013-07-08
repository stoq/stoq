# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
##

import gtk

from kiwi.ui.objectlist import Column

from stoqlib.domain.invoice import InvoiceLayout, InvoicePrinter
from stoqlib.domain.sale import Sale
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.invoiceeditor import (InvoiceLayoutEditor,
                                               InvoicePrinterEditor)
from stoqlib.lib.invoice import (SaleInvoice, print_sale_invoice,
                                 validate_invoice_number)

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _InvoiceLayoutListSlave(ModelListSlave):
    model_type = InvoiceLayout
    editor_class = InvoiceLayoutEditor
    columns = [
        Column('description', _('Description'), data_type=str,
               expand=True, sorted=True),
        Column('size', _('Size'), data_type=str, width=90,
               format_func=lambda (w, h): '%dx%d' % (w, h)),
    ]

    def delete_model(self, model, store):
        for field in model.fields:
            store.remove(field)
        ModelListSlave.delete_model(self, model, store)


class InvoiceLayoutDialog(ModelListDialog):
    list_slave_class = _InvoiceLayoutListSlave
    size = (500, 300)
    title = _("Invoice Layouts")


class _InvoicePrinterListSlave(ModelListSlave):
    model_type = InvoicePrinter
    editor_class = InvoicePrinterEditor
    columns = [
        Column('description', _('Description'), data_type=str,
               expand=True, sorted=True),
        Column('device_name', _('Device name'), data_type=str, width=150),
        Column('station.name', _('Station'), data_type=str, width=80),
        Column('layout.description', _('Layout'), data_type=str, width=120),
    ]


class InvoicePrinterDialog(ModelListDialog):
    list_slave_class = _InvoicePrinterListSlave
    size = (700, 300)
    title = _("Invoice Printers")


class SaleInvoicePrinterDialog(BaseEditor):
    model_type = Sale
    model_name = _(u'Sale Invoice')
    gladefile = 'SaleInvoicePrinterDialog'
    proxy_widgets = ('invoice_number', )
    title = _(u'Sale Invoice Dialog')
    size = (250, 100)

    def __init__(self, store, model, printer):
        self._printer = printer
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.main_dialog.ok_button.set_label(gtk.STOCK_PRINT)

        if self.model.invoice_number is not None:
            self.invoice_number.set_sensitive(False)
        else:
            last_invoice_number = Sale.get_last_invoice_number(self.store) or 0
            self.invoice_number.update(last_invoice_number + 1)

    def setup_proxies(self):
        self.add_proxy(self.model, SaleInvoicePrinterDialog.proxy_widgets)

    def on_confirm(self):
        invoice = SaleInvoice(self.model, self._printer.layout)
        print_sale_invoice(invoice, self._printer)

    def on_invoice_number__validate(self, widget, value):
        return validate_invoice_number(value, self.store)
