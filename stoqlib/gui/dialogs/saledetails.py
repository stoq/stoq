# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
""" Classes for sale details """

import datetime
import decimal

import pango
import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ColoredColumn

from stoqlib.api import api
from stoqlib.domain.payment.views import PaymentChangeHistoryView
from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.domain.sale import (SaleView, Sale, ReturnedSaleItemsView,
                                 SaleComment, SaleCommentsView)
from stoqlib.domain.views import SaleItemsView
from stoqlib.exceptions import StoqlibError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn, QuantityColumn
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.formatters import format_quantity, get_full_date
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.boleto import BillReport
from stoqlib.reporting.booklet import BookletReport
from stoqlib.reporting.sale import SaleOrderReport
from stoqlib.reporting.salereturn import SaleReturnReport

_ = stoqlib_gettext


class _TemporaryOutPayment(object):

    class method:
        description = None

    def __init__(self, payment):
        self.id = payment.id
        self.identifier = payment.identifier
        self.description = payment.description
        self.method.description = payment.method.description
        self.method.method_name = payment.method.method_name
        self.due_date = payment.due_date
        self.paid_date = payment.paid_date
        self.status_str = payment.status_str
        self.value = -payment.base_value
        self.paid_value = -(payment.paid_value or 0)


class SaleDetailsDialog(BaseEditor):
    gladefile = "SaleDetailsDialog"
    model_type = SaleView
    title = _(u"Sale Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('status_lbl',
                     'client_lbl',
                     'salesperson_lbl',
                     'open_date_lbl',
                     'total_lbl',
                     'return_total_lbl',
                     'identifier',
                     'subtotal_lbl',
                     'surcharge_lbl',
                     'discount_lbl',
                     'invoice_number', )
    payment_widgets = ('total_discount',
                       'total_interest',
                       'total_penalty',
                       'total_paid',
                       'total_value', )

    def __init__(self, store, model=None, visual_mode=False):
        """ Creates a new SaleDetailsDialog object

        :param store: a store
        :param model: a :class:`stoqlib.domain.sale.SaleView` object
        """
        BaseEditor.__init__(self, store, model,
                            visual_mode=visual_mode)

    def _setup_columns(self):
        self.items_list.set_columns(self._get_items_columns())
        self.returned_items_list.set_columns(self._get_returned_items_columns())
        self.payments_list.set_columns(self._get_payments_columns())
        self.payments_info_list.set_columns(self._get_payments_info_columns())
        self.comments_list.set_columns(self._get_comments_columns())

    def _get_payments(self, sale):
        for payment in sale.group.payments:
            if payment.is_outpayment():
                yield _TemporaryOutPayment(payment)
            else:
                yield payment

    def _refresh_comments(self):
        self.comments_list.add_list(
            SaleCommentsView.find_by_sale(self.store, self.sale_order))

    def _format_comments(self, comments):
        return comments.split('\n')[0]

    def _run_comments_editor(self, item=None):
        if item is not None:
            run_dialog(NoteEditor, self, self.store, item, 'comment',
                       title=_('Sale Comment'), visual_mode=True)
            return

        with api.new_store() as store:
            item = SaleComment(store=store, sale=store.fetch(self.model.sale),
                               author=api.get_current_user(store))
            run_dialog(NoteEditor, self, store, item, 'comment',
                       title=_('New Sale Comment'))

        if store.committed:
            self._refresh_comments()

    def _setup_widgets(self):
        if not self.model.client_id:
            self.details_button.set_sensitive(False)
        self._setup_columns()

        self.sale_order = self.model.sale
        if self.sale_order.status == Sale.STATUS_RENEGOTIATED:
            self.status_details_button.show()
        else:
            self.status_details_button.hide()

        parent_items = SaleItemsView.find_parent_items(self.store, self.sale_order)
        for parent_item in parent_items:
            self.items_list.append(None, parent_item)
            if parent_item.product and not parent_item.product.is_package:
                # Prevent Production components to be shown
                continue
            for children in parent_item.get_children():
                self.items_list.append(parent_item, children)

        notes = []
        details = self.sale_order.get_details_str()
        if details:
            notes.append(details)

        # Information about the original sale (in this case, this sale was
        # created as a trade for some items)
        returned_sale = self.store.find(ReturnedSale,
                                        new_sale=self.model.id).one()
        if returned_sale:
            if returned_sale.sale:
                traded_sale = returned_sale.sale.identifier
            else:
                traded_sale = _("Unknown")
            trade_notes = [
                '* %s' % _("Items traded for this sale"),
                _("Date: %s") % get_full_date(returned_sale.return_date),
                _("Traded sale: %s") % traded_sale,
                _("Invoice number: %s") % returned_sale.invoice_number,
                _("Reason: %s") % returned_sale.reason,
            ]
            notes.append('\n'.join(trade_notes))

        returned_items = ReturnedSaleItemsView.find_parent_items(self.store,
                                                                 self.sale_order)
        seen_set = set()
        for item in returned_items:
            self.returned_items_list.append(None, item)
            if not item.is_package():
                continue
            for child in item.get_children():
                self.returned_items_list.append(item, child)
            if item.invoice_number in seen_set:
                continue

            fmt = _("Itens returned on %s")
            return_notes = ['* %s' % (
                fmt % (get_full_date(item.return_date)))]
            if item.new_sale:
                fmt = _("Traded for sale: %s")
                return_notes.append(fmt % (item.new_sale.identifier))

            return_notes.extend([
                _("Invoice number: %s") % item.invoice_number,
                _("Reason: %s") % item.reason,
            ])

            notes.append('\n'.join(return_notes))
            seen_set.add(item.invoice_number)
        if len(list(self.returned_items_list)) == 0:
            page_no = self.details_notebook.page_num(self.returned_items_vbox)
            self.details_notebook.remove_page(page_no)

        buffer = gtk.TextBuffer()
        buffer.set_text('\n\n'.join(notes))
        self.notes.set_buffer(buffer)

        self.payments_list.add_list(self._get_payments(self.sale_order))
        changes = PaymentChangeHistoryView.find_by_group(self.store,
                                                         self.sale_order.group)
        self.payments_info_list.add_list(changes)

        for widget, method_name in [(self.print_bills, u'bill'),
                                    (self.print_booklets, u'store_credit')]:
            widget.set_visible(any(
                [p.method.method_name == method_name and not p.is_cancelled()
                 for p in self.payments_list]))

        self._refresh_comments()
        self.comment_info.set_sensitive(False)

    def _get_payments_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #')),
                Column('method.description', _("Type"),
                       data_type=str, width=60),
                Column('description', _("Description"), data_type=str,
                       width=150, expand=True),
                Column('due_date', _("Due date"), sorted=True,
                       data_type=datetime.date, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('paid_date', _("Paid date"),
                       data_type=datetime.date, width=90),
                Column('status_str', _("Status"), data_type=str, width=80),
                ColoredColumn('value', _("Value"), data_type=currency,
                              width=90, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize),
                ColoredColumn('paid_value', _("Paid value"), data_type=currency,
                              width=92, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize)]

    def _get_items_columns(self):
        return [Column('code', _("Code"), sorted=True, data_type=str, width=130),
                Column('description', _("Description"), data_type=str,
                       expand=True, width=200),
                Column('category', _("Category"), data_type=str, visible=False),
                Column('manufacturer', _("Manufacturer"), data_type=str,
                       visible=False),
                QuantityColumn('quantity', title=_("Qty"),
                               visible=True),
                Column('base_price', _("Base price"), data_type=currency,
                       visible=False),
                Column('price', _("Sale price"), data_type=currency),
                Column('item_discount', _("Discount"), data_type=currency,
                       visible=False),
                Column('total', _("Total"), data_type=currency)]

    def _get_payments_info_columns(self):
        return [Column('change_date', _(u"When"),
                       data_type=datetime.date, sorted=True, ),
                Column('description', _(u"Payment"),
                       data_type=str, expand=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('changed_field', _(u"Changed"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('from_value', _(u"From"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('to_value', _(u"To"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('reason', _(u"Reason"),
                       data_type=str, expand=True,
                       ellipsize=pango.ELLIPSIZE_END)]

    def _get_returned_items_columns(self):
        return [
            Column('return_date', _("Date"), data_type=datetime.date,
                   sorted=True),
            Column('invoice_number', _("Invoice #"), data_type=int),
            Column('code', _("Code"), data_type=str,
                   visible=False),
            Column('description', _("Description"), data_type=str,
                   expand=True),
            Column('quantity', _("Quantity"), data_type=decimal.Decimal,
                   format_func=format_quantity),
            Column('price', _("Sale price"), data_type=currency),
            Column('total', _("Total"), data_type=currency),
        ]

    def _get_comments_columns(self):
        return [
            Column('date', _(u"Date"), data_type=datetime.datetime, sorted=True),
            Column('author_name', _(u"Who"), data_type=str, expand=True,
                   ellipsize=pango.ELLIPSIZE_END),
            Column('comment', _(u"Notes"), data_type=str, expand=True,
                   format_func=self._format_comments,
                   ellipsize=pango.ELLIPSIZE_END)]

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, SaleDetailsDialog.proxy_widgets)
        self.add_proxy(self.model.sale.group,
                       SaleDetailsDialog.payment_widgets)

    #
    # Kiwi handlers
    #

    def on_comments_list__row_activated(self, details_list, item):
        if self.comment_info.get_sensitive():
            self._run_comments_editor(item)

    def on_comments_list__selection_changed(self, details_list, item):
        self.comment_info.set_sensitive(bool(item))

    def on_comment_add__clicked(self, button):
        self._run_comments_editor()

    def on_comment_info__clicked(self, button):
        self._run_comments_editor(item=self.comments_list.get_selected())

    def on_print_button__clicked(self, button):
        print_report(SaleOrderReport, self.model.sale)

    def on_print_bills__clicked(self, button):
        # Remove cancelled and not bill payments
        payments = [p for p in self.payments_list if
                    p.method.method_name == u'bill' and
                    not p.is_cancelled()]

        if not BillReport.check_printable(payments):
            return False

        print_report(BillReport, payments)

    def on_print_booklets__clicked(self, button):
        # Remove cancelled and not store_credit payments
        payments = [p for p in self.payments_list if
                    p.method.method_name == u'store_credit' and
                    not p.is_cancelled()]

        print_report(BookletReport, payments)

    def on_details_button__clicked(self, button):
        if not self.model.client_id:
            raise StoqlibError("You should never call ClientDetailsDialog "
                               "for sales which clients were not specified")
        run_dialog(ClientDetailsDialog, self, self.store, self.model.client)

    def on_status_details_button__clicked(self, button):
        if self.sale_order.status == Sale.STATUS_RENEGOTIATED:
            # XXX: Rename to renegotiated
            run_dialog(RenegotiationDetailsDialog, self, self.store,
                       self.sale_order.group.renegotiation)

    def on_print_return_report__clicked(self, button):
        print_report(SaleReturnReport, self.store, self.model.client,
                     self.model, self.returned_items_list)
