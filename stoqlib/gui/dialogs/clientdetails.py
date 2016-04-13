# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
""" Classes for client details """

import datetime

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ColoredColumn, SummaryLabel, ObjectTree
from kiwi.ui.gadgets import render_pixbuf

from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.person import Client
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.utils.workorderutils import get_workorder_state_icon
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class DetailsTab(gtk.VBox):
    details_dialog_class = None

    def __init__(self, model, parent):
        super(DetailsTab, self).__init__()

        self.model = model
        self._parent = parent

        self.set_spacing(6)
        self.set_border_width(6)

        self.klist = ObjectTree(self.get_columns())
        self.populate()

        self.pack_start(self.klist)
        self.klist.show()

        if len(self.klist) and self.get_details_dialog_class():
            self.button_box = gtk.HButtonBox()
            self.button_box.set_layout(gtk.BUTTONBOX_START)

            details_button = gtk.Button(self.details_lbl)
            self.button_box.pack_start(details_button)
            details_button.set_sensitive(bool(self.klist.get_selected()))
            details_button.show()

            self.pack_end(self.button_box, False, False)
            self.button_box.show()

            self.button_box.details_button = details_button
            details_button.connect('clicked', self._on_details_button__clicked)

            self.klist.connect('row-activated', self._on_klist__row_activated)
            self.klist.connect('selection-changed',
                               self._on_klist__selection_changed)

        self.setup_widgets()

    def refresh(self):
        """Refreshes the list of respective tab."""
        self.klist.clear()
        self.klist.add_list(self.populate())

    def get_columns(self):
        """Returns a list of columns this tab should show."""
        raise NotImplementedError

    def show_details(self):
        """Called when the details button is clicked. Displays the details of
        the selected object in the list."""
        model = self.get_details_model(self.klist.get_selected())
        run_dialog(self.get_details_dialog_class(),
                   parent=self._parent,
                   store=self._parent.store,
                   model=model,
                   visual_mode=True)

    def get_label(self):
        """Returns the name of the tab."""
        label = gtk.Label(self.labels[1])
        return label

    def get_details_model(self, model):
        """Subclassses can overwrite this method if the details dialog class
        needs a model different than the one on the list."""
        return model

    def get_details_dialog_class(self):
        """Subclasses must return the dialog that should be displayed for more
        information about the item on the list"""
        return self.details_dialog_class

    def setup_widgets(self):
        """Override this if tab needs to do some custom widget setup."""

    #
    # Callbacks
    #

    def _on_details_button__clicked(self, button):
        self.show_details()

    def _on_klist__row_activated(self, klist, item):
        self.show_details()

    def _on_klist__selection_changed(self, klist, data):
        self.button_box.details_button.set_sensitive(bool(data))


class SalesTab(DetailsTab):
    labels = _('Sale'), _('Sales')
    details_lbl = _('Sale details')

    def setup_widgets(self):
        value_format = '<b>%s</b>'
        total_label = "<b>%s</b>" % api.escape(_("Total:"))
        sales_summary_label = SummaryLabel(klist=self.klist,
                                           column='total',
                                           label=total_label,
                                           value_format=value_format)
        sales_summary_label.show()
        self.pack_start(sales_summary_label, False)

        self.has_open_inventory = self._has_open_inventory()

        if len(self.klist):
            return_button = gtk.Button(_('Return sale'))
            self.button_box.pack_start(return_button)
            return_button.set_sensitive(bool(self.klist.get_selected()))
            return_button.show()

            self.button_box.return_button = return_button
            return_button.connect('clicked', self._on_return_button__clicked)

    def _has_open_inventory(self):
        store = self._parent.store
        has_open = Inventory.has_open(store, api.get_current_branch(store))
        return bool(has_open)

    def _return_sale(self):
        from stoqlib.gui.slaves.saleslave import return_sale
        sale_view = self.klist.get_selected()
        with api.new_store() as store:
            retval = return_sale(self.get_toplevel(),
                                 store.fetch(sale_view.sale), store)
        if retval:
            self.refresh()

    def _can_return_sale(self, sale_view):
        if sale_view:
            return sale_view.can_return() and not self.has_open_inventory
        return False

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Sale #'), sorted=True),
                Column("invoice_number", title=_("Invoice #"),
                       data_type=int, width=90),
                Column("open_date", title=_("Date"), data_type=datetime.date,
                       justify=gtk.JUSTIFY_RIGHT, width=80),
                Column("salesperson_name", title=_("Salesperson"),
                       searchable=True, expand=True, data_type=str),
                Column("status_name", title=_("Status"), width=80,
                       data_type=str),
                Column("total", title=_("Total"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100)]

    def populate(self):
        for obj in self.model.get_client_sales():
            self.klist.append(None, obj)

    def get_details_dialog_class(self):
        from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
        return SaleDetailsDialog

    def _on_return_button__clicked(self, button):
        self._return_sale()

    def _on_klist__selection_changed(self, klist, data):
        can_return = self._can_return_sale(data)
        self.button_box.details_button.set_sensitive(bool(data))
        self.button_box.return_button.set_sensitive(bool(can_return))


class ReturnedSalesTab(DetailsTab):
    labels = _('Returned Sale'), _('Returned Sales')
    details_lbl = _('Returned sale details')

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Returned #'), sorted=True),
                Column("invoice_number", title=_("Invoice #"),
                       data_type=int, width=90),
                Column("return_date", title=_("Return Date"),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT,
                       width=80),
                Column("product_name", title=_("Product"),
                       searchable=True, data_type=str),
                Column("salesperson_name", title=_("Salesperson"),
                       searchable=True, visible=False, data_type=str),
                Column("responsible_name", title=_("Responsible"),
                       searchable=True, data_type=str),
                Column("reason", title=_("Reason"), searchable=False,
                       expand=True, data_type=str),
                Column("price", title=_("Price"), data_type=currency),
                Column("quantity", title=_("Qty"), data_type=str),
                Column("total", title=_("Total"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100)]

    def populate(self):
        for item in self.model.get_client_returned_sales():
            self.klist.append(None, item)
            sellable = item.returned_item.sellable
            if (sellable.service or
                    (sellable.product and not sellable.product.is_package)):
                continue
            for child in item.get_children_items():
                self.klist.append(item, child)

    def get_details_model(self, model):
        from stoqlib.domain.sale import Sale, SaleView
        return self._parent.store.find(SaleView, Sale.id == model.sale_id).one()

    def get_details_dialog_class(self):
        from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
        return SaleDetailsDialog


class ProductsTab(DetailsTab):
    labels = _('Product'), _('Products')
    details_lbl = _('Product details')

    def get_columns(self):
        return [Column("code", title=_("Code"), data_type=str,
                       width=120, sorted=True),
                Column("description", title=_("Description"), data_type=str,
                       expand=True, searchable=True),
                Column("quantity", title=_("Total quantity"),
                       data_type=str, width=120, justify=gtk.JUSTIFY_RIGHT),
                Column("sale_date", title=_("Sale date"),
                       data_type=datetime.date, width=150),
                Column("value", title=_("Value"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT),
                Column("total_value", title=_("Total value"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT, )]

    def populate(self):
        for item in self.model.get_client_products(with_children=False):
            self.klist.append(None, item)
            if item.sale_item.sellable.product.is_composed:
                continue
            for child in item.get_children_items():
                self.klist.append(item, child)


class ServicesTab(DetailsTab):
    labels = _('Service'), _('Services')
    details_lbl = _('Service details')

    def get_columns(self):
        return [Column("code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=120, sorted=True),
                Column("description",
                       title=_("Description"), data_type=str, expand=True,
                       searchable=True),
                Column("estimated_fix_date", title=_("Estimated fix date"),
                       width=150, data_type=datetime.date)]

    def populate(self):
        for obj in self.model.get_client_services():
            self.klist.append(None, obj)


class WorkOrdersTab(DetailsTab):
    labels = _('Work Order'), _('Work Orders')
    details_lbl = _('Work order details')

    def get_columns(self):
        return [IdentifierColumn("identifier", title=_('WO #'), sorted=True),
                Column("equipment", title=_("Equipment"),
                       data_type=str, expand=True, pack_end=True),
                Column('category_color', title=_(u'Equipment'),
                       column='equipment', data_type=gtk.gdk.Pixbuf,
                       format_func=render_pixbuf),
                Column('flag_icon', title=_(u'Equipment'), column='equipment',
                       data_type=gtk.gdk.Pixbuf, format_func_data=True,
                       format_func=self._format_state_icon),
                Column("open_date", title=_("Open date"),
                       data_type=datetime.date, width=120),
                Column("approve_date", title=_("Approve date"),
                       data_type=datetime.date, width=120),
                Column("finish_date", title=_("Finish date"),
                       data_type=datetime.date, width=120),
                Column("total", title=_("Total"),
                       data_type=currency, width=100)]

    def populate(self):
        for obj in self.model.get_client_work_orders():
            self.klist.append(None, obj)

    def get_details_model(self, model):
        return model.work_order

    def get_details_dialog_class(self):
        from stoqlib.gui.editors.workordereditor import WorkOrderEditor
        return WorkOrderEditor

    def _format_state_icon(self, item, data):
        stock_id, tooltip = get_workorder_state_icon(item.work_order)
        if stock_id is not None:
            # We are using self because render_icon is a gtk.Widget's # method.
            # It has nothing to do with results tough.
            return self.render_icon(stock_id, gtk.ICON_SIZE_MENU)


class PaymentsTab(DetailsTab):
    labels = _('Payment'), _('Payments')
    details_lbl = _('Payment details')

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #')),
                Column("method_description", title=_("Type"),
                       data_type=str, width=90),
                Column("description", title=_("Description"),
                       data_type=str, searchable=True, width=190,
                       expand=True),
                Column("due_date", title=_("Due date"), width=110,
                       data_type=datetime.date, sorted=True),
                Column("paid_date", title=_("Paid date"), width=110,
                       data_type=datetime.date),
                Column("status_str", title=_("Status"), width=80,
                       data_type=str),
                ColoredColumn("value", title=_("Value"),
                              justify=gtk.JUSTIFY_RIGHT, data_type=currency,
                              color='red', width=100,
                              data_func=payment_value_colorize),
                Column("days_late", title=_("Days Late"), width=110,
                       format_func=(lambda days_late: days_late and
                                    str(days_late) or u""),
                       justify=gtk.JUSTIFY_RIGHT, data_type=str)]

    def populate(self):
        for obj in self.model.get_client_payments():
            self.klist.append(None, obj)

    def get_details_model(self, model):
        return model.payment

    def get_details_dialog_class(self):
        from stoqlib.gui.editors.paymenteditor import InPaymentEditor
        return InPaymentEditor

    def show_details(self):
        model = self.get_details_model(self.klist.get_selected())
        run_dialog(self.get_details_dialog_class(),
                   store=self._parent.store,
                   model=model)


class CreditAccountsTab(DetailsTab):
    labels = _('Credit Account'), _('Credit Accounts')
    details_lbl = _('Credit details')

    def setup_widgets(self):
        value_format = '<b>%s</b>'
        balance_label = "<b>%s</b>" % api.escape(_("Balance:"))

        account_summary_label = SummaryLabel(klist=self.klist,
                                             column='paid_value',
                                             label=balance_label,
                                             value_format=value_format,
                                             data_func=lambda p: p.is_outpayment())

        account_summary_label.show()
        self.pack_start(account_summary_label, False)

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
                Column('paid_date', title=_(u'Date'), data_type=datetime.date,
                       width=150),
                Column('description', title=_(u'Description'),
                       data_type=str, width=150, expand=True),
                ColoredColumn('paid_value', title=_(u'Value'), color='red',
                              data_type=currency, width=100,
                              use_data_model=True,
                              data_func=lambda p: not p.is_outpayment())]

    def populate(self):
        for obj in self.model.get_credit_transactions():
            self.klist.append(None, obj)


class CallsTab(DetailsTab):
    labels = _('Call'), _('Calls')
    details_lbl = _('Call details')

    def get_columns(self):
        return [Column("date", title=_("Date"),
                       data_type=datetime.date, width=150, sorted=True),
                Column("description", title=_("Description"),
                       data_type=str, width=150, expand=True),
                Column("attendant.person.name", title=_("Attendant"),
                       data_type=str, width=100, expand=True)]

    def populate(self):
        for obj in self.model.person.calls:
            self.klist.append(None, obj)


class ClientDetailsDialog(BaseEditor):
    """This dialog shows some important details about clients like:
        - history of sales
        - all products tied with sales
        - all services tied with sales
        - all payments already created
    """
    title = _(u"Client Details")
    hide_footer = True
    size = (-1, 400)
    model_type = Client
    gladefile = "ClientDetailsDialog"
    proxy_widgets = ('client',
                     'last_purchase_date',
                     'status')

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        for tab_class in [SalesTab,
                          ReturnedSalesTab,
                          ProductsTab,
                          ServicesTab,
                          WorkOrdersTab,
                          PaymentsTab,
                          CreditAccountsTab,
                          CallsTab]:
            tab = tab_class(self.model, self)
            label = tab.get_label()
            label.set_sensitive(len(tab.klist))
            self.details_notebook.append_page(tab, label)
            label.show()
            tab.show()

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)

    #
    # Callbacks
    #

    def on_further_details_button__clicked(self, *args):
        store = api.new_store()
        model = store.fetch(self.model)
        run_person_role_dialog(ClientEditor, self, store,
                               model, visual_mode=True)
        store.confirm(False)
        store.close()
