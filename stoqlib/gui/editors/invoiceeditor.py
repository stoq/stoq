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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""User interfaces for configuring, editing and printing invoices."""

import operator

import gtk
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.objectlist import ObjectList, Column

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.invoice import InvoiceLayout, InvoiceField, InvoicePrinter
from stoqlib.domain.sale import Sale
from stoqlib.domain.station import BranchStation
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.fieldgrid import FieldGrid
from stoqlib.lib.invoice import (get_invoice_fields, SaleInvoice,
                                 print_sale_invoice, validate_invoice_number)
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext as _


class InvoiceGrid(FieldGrid):
    def objectlist_dnd_handler(self, item, x, y):
        child = self.add_field(item.name, item.description, x, y)
        child.show()
        self.select_field(child)

        return True


class InvoiceLayoutEditor(BaseEditor):
    model_name = _(u'Invoice Layouts')
    model_type = InvoiceLayout
    gladefile = 'InvoiceLayoutEditor'
    size = (780, 540)
    proxy_widgets = ['description', 'width', 'height']

    # BaseEditor
    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)
        self.enable_normal_window()
        button = self.add_button(stock=gtk.STOCK_PRINT_PREVIEW)
        button.connect('clicked', self._on_preview_button__clicked)

    def create_model(self, conn):
        return InvoiceLayout(description='Untitled',
                             width=80,
                             height=40,
                             connection=conn)

    def setup_proxies(self):
        self._create_grid()
        self._create_field_list()
        self.proxy = self.add_proxy(self.model,
                                    InvoiceLayoutEditor.proxy_widgets)

        for field in self.model.fields:
            description = self._field_descriptions[field.field_name]
            grid_field = self.grid.add_field(field.field_name, description,
                                             field.x, field.y,
                                             field.width, field.height)
            grid_field.model = field
            grid_field.widget.show()

        if self.model.description == 'Untitled':
            self.description.grab_focus()
        else:
            self.grid.grab_focus()

    # Callbacks

    def on_width__validate(self, widget, value):
        if not value > 0:
            return ValidationError(_(u'width value must greater than zero.'))

    def on_height__validate(self, widget, value):
        if not value > 0:
            return ValidationError(_(u'height value must greater than zero.'))

    def after_width__content_changed(self, widget):
        self.grid.resize(self.model.width, self.model.height)

    def after_height__content_changed(self, widget):
        self.grid.resize(self.model.width, self.model.height)

    def _on_grid__field_added(self, grid, grid_field):
        self._field_added(grid_field)

    def _on_grid__field_removed(self, grid, grid_field):
        self._field_removed(grid_field)

    def _on_grid__selection_changed(self, grid, grid_field):
        self._field_changed(grid_field)

    def _on_preview_button__clicked(self, button):
        self._print_preview()

    # Private

    def _create_grid(self):
        self.grid = InvoiceGrid('Monospace 8',
                                self.model.width,
                                self.model.height)
        self.grid.connect('field-added', self._on_grid__field_added)
        self.grid.connect('field-removed', self._on_grid__field_removed)
        self.grid.connect('selection-changed',
                          self._on_grid__selection_changed)
        self.sw.add_with_viewport(self.grid)
        self.grid.show()

    def _create_field_list(self):
        items = ObjectList([Column('description', width=200),
                            Column('len', data_type=int, editable=True)])
        items.enable_dnd()
        items.set_size_request(200, -1)
        descriptions = {}
        invoice_fields = get_invoice_fields()
        for invoice_field in sorted(invoice_fields,
                                    key=operator.attrgetter('name')):
            items.append(
                Settable(description=invoice_field.get_description(),
                         name=invoice_field.name,
                         len=invoice_field.length))
            descriptions[invoice_field.name] = invoice_field.description
        self._field_descriptions = descriptions
        self.left_vbox.pack_end(items, True, True)
        items.show()

    def _field_changed(self, grid_field):
        if grid_field:
            pos = 'x=%d, y=%d' % (grid_field.x + 1, grid_field.y + 1)
            size = '%dx%d' % (grid_field.width, grid_field.height)
            name = grid_field.text

            # This is needed because we might get a selection-changed signal
            # before child-added, model is only assigned to the field info
            # when adding it.
            field = getattr(grid_field, 'model', None)
            if field is not None:
                field.x = grid_field.x
                field.y = grid_field.y
                field.width = grid_field.width
                field.height = grid_field.height
        else:
            pos = ''
            size = ''
            name = ''
        self.field_name.set_text(name)
        self.field_pos.set_text(pos)
        self.field_size.set_text(size)

    def _field_added(self, grid_field):
        field = self.model.get_field_by_name(grid_field.text)
        if field is not None:
            field.x = grid_field.x
            field.y = grid_field.y
            field.width = grid_field.width
            field.height = grid_field.height
        else:
            field = InvoiceField(layout=self.model,
                                 field_name=grid_field.text,
                                 x=grid_field.x,
                                 y=grid_field.y,
                                 width=grid_field.width,
                                 height=grid_field.height,
                                 connection=self.conn)
        grid_field.model = field

    def _field_removed(self, grid_field):
        invoice_field = grid_field.model
        InvoiceField.delete(invoice_field.id, self.conn)

    def _print_preview(self):
        # Get the last opened date
        sales = Sale.select(orderBy='-open_date').limit(1)
        if not sales:
            info(_("You need at least one sale to be able to preview "
                   "invoice layouts"))
            return

        invoice = SaleInvoice(sales[0], self.model)
        invoice_pages = invoice.generate_pages()
        if not invoice_pages:
            info(_(u'Not enough fields or data to create an invoice preview.'))
            return

        for page in invoice_pages:
            for line in page:
                print repr(line.tostring())


class InvoiceLayoutDialog(ModelListDialog):

    # ModelListDialog
    model_type = InvoiceLayout
    editor_class = InvoiceLayoutEditor
    size = (500, 300)
    title = _("Invoice Layouts")

    # ListDialog
    columns = [
        Column('description', _('Description'), data_type=str,
               expand=True, sorted=True),
        Column('size', _('Size'), data_type=str, width=90,
               format_func=lambda (w, h): '%dx%d' % (w, h)),
    ]

    def delete_model(self, model, trans):
        for field in model.fields:
            InvoiceField.delete(field.id, trans)
        ModelListDialog.delete_model(self, model, trans)


class InvoicePrinterEditor(BaseEditor):
    model_name = _(u'Invoice Printers')
    model_type = InvoicePrinter
    gladefile = 'InvoicePrinterEditor'

    proxy_widgets = ['device_name',
                     'description',
                     'layout',
                     'station']

    def create_model(self, conn):
        return InvoicePrinter(description=_('Untitled Printer'),
                              device_name='/dev/lp0',
                              station=get_current_station(conn),
                              layout=None,
                              connection=conn)

    def setup_proxies(self):
        self.station.prefill(
            [(station.name, station)
             for station in BranchStation.select(connection=self.conn,
                                                 orderBy='name')])
        self.layout.prefill(
            [(layout.get_description(), layout)
             for layout in InvoiceLayout.select(connection=self.conn,
                                                orderBy='description')])

        self.proxy = self.add_proxy(self.model,
                                    InvoicePrinterEditor.proxy_widgets)

    def on_confirm(self):
        # Bug!
        self.model.layout = self.layout.get_selected()
        return self.model


class InvoicePrinterDialog(ModelListDialog):

    # ModelListDialog
    model_type = InvoicePrinter
    editor_class = InvoicePrinterEditor
    size = (700, 300)
    title = _("Invoice Printers")

    # ListDialog
    columns = [
        Column('description', _('Description'), data_type=str,
               expand=True, sorted=True),
        Column('device_name', _('Device name'), data_type=str, width=150),
        Column('station.name', _('Station'), data_type=str, width=80),
        Column('layout.description', _('Layout'), data_type=str, width=120),
    ]


class SaleInvoicePrinterDialog(BaseEditor):
    model_type = Sale
    model_name = _(u'Sale Invoice')
    gladefile = 'SaleInvoicePrinterDialog'
    proxy_widgets = ('invoice_number', )
    title = _(u'Sale Invoice Dialog')
    size = (250, 100)

    def __init__(self, conn, model, printer):
        self._printer = printer
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.main_dialog.ok_button.set_label(gtk.STOCK_PRINT)

        if self.model.invoice_number is not None:
            self.invoice_number.set_sensitive(False)
        else:
            last_invoice_number = Sale.get_last_invoice_number(self.conn) or 0
            self.invoice_number.update(last_invoice_number + 1)

    def setup_proxies(self):
        self.add_proxy(self.model, SaleInvoicePrinterDialog.proxy_widgets)

    def on_confirm(self):
        invoice = SaleInvoice(self.model, self._printer.layout)
        print_sale_invoice(invoice, self._printer)
        return self.model

    def on_invoice_number__validate(self, widget, value):
        return validate_invoice_number(value, self.conn)
