# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import collections
import datetime

import gtk
from kiwi.currency import currency
from kiwi.python import Settable
from kiwi.ui.objectlist import Column, SummaryLabel
from storm.expr import And, Eq

from stoqlib.api import api
from stoqlib.database.expr import Date
from stoqlib.domain.payment.card import CreditCardData
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.dailymovement import (DailyInPaymentView,
                                                  DailyOutPaymentView)
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import TillEntry
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.searchoptions import (Today, Yesterday, LastWeek,
                                              LastMonth)
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.formatters import get_formatted_price
from stoqlib.reporting.till import TillDailyMovementReport


class DailyMovementSale(Settable):
    def __eq__(self, other):
        return self.identifier == other.identifier

    def __hash__(self):
        return hash(self.identifier)


class TillDailyMovementDialog(BaseEditor):
    """Shows informations related to till operations over a daterange.
    It can also be filtered by branch.
    """

    title = _("Daily Movement")
    hide_footer = True
    size = (950, 450)
    model_type = Settable
    gladefile = "TillDailyMovementDialog"
    proxy_widgets = ['branch', 'in_subtotal', 'in_credit', 'in_total',
                     'out_subtotal', 'out_credit', 'out_total']

    #
    #  Private
    #

    def _setup_widgets(self):
        # Branches combo
        items = api.get_branches_for_filter(self.store)
        self.branch.prefill(items)

        # Daterange filter
        self.date_filter = DateSearchFilter(_(u'Date:'))
        self.date_filter.clear_options()
        self.date_filter.add_custom_options()
        for option in [Today, Yesterday, LastWeek, LastMonth]:
            self.date_filter.add_option(option)
        self.date_filter.select(position=0)
        self.daterange_hbox.pack_start(self.date_filter, False, False)
        self.date_filter.show_all()

        # Setting report lists' columns
        self.sales_list.set_columns(self._get_sales_columns())
        self.inpayments_list.set_columns(self._get_lonely_payments_columns())
        self.purchases_list.set_columns(self._get_purchases_columns())
        self.outpayments_list.set_columns(self._get_lonely_payments_columns())
        self.return_sales_list.set_columns(self._get_return_sales_columns())
        self.supplies_list.set_columns(self._get_till_columns())
        self.removals_list.set_columns(self._get_till_columns())
        self.permethod_list.set_columns(self._get_permethod_columns())
        self.percard_list.set_columns(self._get_percard_columns())

        # Print button is insensitive, until the first report is generated
        self.print_button.set_sensitive(False)

        self._setup_summary_labels()

    def _get_sales_columns(self):
        return [IdentifierColumn('identifier', title=_('Sale #'), sorted=True),
                Column('salesperson', title=_('Sales Person'), data_type=str),
                Column('client', title=_('Client'), data_type=str, expand=True),
                Column('branch', title=_('Branch'), data_type=str, visible=False),
                Column('value', title=_('Value'), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT)]

    def _get_lonely_payments_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
                Column('method', title=_('Method'), data_type=str),
                Column('description', title=_('Description'), expand=True,
                       data_type=str),
                Column('branch', title=_('Branch'), data_type=str, visible=False),
                Column('value', title=_('Payment Value'), data_type=currency)]

    def _get_purchases_columns(self):
        return [IdentifierColumn('identifier', title=_('Code #'), sorted=True),
                Column('status_str', title=_('Status'), data_type=str),
                Column('responsible_name', title=_('Responsible'), expand=True,
                       data_type=str),
                Column('branch_name', title=_('Branch'), data_type=str),
                Column('notes', title=_('Notes'), data_type=str),
                Column('supplier_name', title=_('Supplier'), data_type=str),
                Column('purchase_total', title=_('Value'), data_type=currency)]

    def _get_return_sales_columns(self):
        return [IdentifierColumn('identifier', title=_('Code #'), sorted=True),
                Column('salesperson', title=_('Sales Person'), data_type=str),
                Column('client', title=_('Client'), expand=True, data_type=str),
                Column('return_date', title=_('Return Date'),
                       data_type=datetime.date),
                Column('branch', title=_('Branch'), data_type=str, visible=False),
                Column('value', title=_('Sale Value'), data_type=currency)]

    def _get_till_columns(self):
        return [IdentifierColumn('identifier', title=_('Entry #'), sorted=True),
                Column('description', title=_('Description'), data_type=str,
                       expand=True),
                Column('branch_name', title=_('Branch'), data_type=str, visible=False),
                Column('value', title=_('Value'), data_type=currency)]

    def _get_permethod_columns(self):
        return [Column('method', title=_('Payment Method'), sorted=True,
                       expand=True),
                Column('in_value', title=_('Income Total'), data_type=currency),
                Column('out_value', title=_('Outgoing Total'),
                       data_type=currency)]

    def _get_percard_columns(self):
        return [Column('provider', title=_('Provider Name'), data_type=str,
                       expand=True),
                Column('income', title=_('Income Total'), data_type=currency)]

    def _create_summary_label(self, report, column='value', label=None):
        # Setting tha data
        obj_list = getattr(self, report + '_list')
        box = getattr(self, report + '_vbox')
        if label is None:
            label = _('Total:')
        label = '<b>%s</b>' % api.escape(label)
        value_format = '<b>%s</b>'

        # Creating the label
        label = SummaryLabel(klist=obj_list, column=column, label=label,
                             value_format=value_format)

        # Displaying the label
        box.pack_start(label, False, False, 0)
        label.show()
        return label

    def _setup_summary_labels(self):
        # Supplies
        self.supplies_label = self._create_summary_label('supplies')
        # Removals
        self.removals_label = self._create_summary_label('removals')
        # Percard
        self.percard_label = self._create_summary_label('percard',
                                                        column='income')

    def _update_summary_labels(self):
        self.supplies_label.update_total()
        self.removals_label.update_total()
        self.percard_label.update_total()
        self.proxy.update_many(('in_subtotal', 'in_credit', 'in_total',
                                'out_subtotal', 'out_credit', 'out_total'))

    def _generate_dailymovement_data(self, store):
        query = And(Payment.status.is_in([Payment.STATUS_PENDING,
                                          Payment.STATUS_PAID]),
                    self._get_query(Payment.open_date, Payment.branch))

        # Keys are the sale objects, and values are lists with all payments
        self.sales = collections.OrderedDict()

        # Keys are the returned sale objects, and values are lists with all payments
        self.return_sales = collections.OrderedDict()
        self.purchases = collections.OrderedDict()

        # lonely input and output payments
        self.lonely_in_payments = []
        self.lonely_out_payments = []

        # values are lists with the first element the summary of the input, and
        # the second the summary of the output
        method_summary = {}
        self.card_summary = {}

        result = store.find(DailyInPaymentView, query)
        for p in result.order_by(Sale.identifier, Payment.identifier):
            if p.sale:
                subtotal = p.sale_subtotal
                total = p.sale.get_total_sale_amount(subtotal)
                salesperson = p.salesperson_name or _('Not Specified')
                client = p.client_name or _('Not Specified')
                sale = DailyMovementSale(identifier=p.sale.identifier,
                                         salesperson=salesperson,
                                         client=client,
                                         branch=p.branch_name,
                                         value=get_formatted_price(total))
                sale_payments = self.sales.setdefault(sale, {})
                details = ''
                method_desc = p.method.get_description()
                if p.check_data:
                    account = p.check_data.bank_account
                    numbers = [payment.payment_number for payment in p.sale.payments
                               if bool(payment.payment_number)]
                    # Ensure that the check numbers are ordered
                    numbers.sort()
                    parts = []
                    if account.bank_number:
                        parts.append(_(u'Bank: %s') % account.bank_number)
                    if account.bank_branch:
                        parts.append(_(u'Agency: %s') % account.bank_branch)
                    if account.bank_account:
                        parts.append(_(u'Account: %s') % account.bank_account)
                    if numbers:
                        parts.append(_(u'Numbers: %s') % ', '.join(numbers))
                    details = ' / '.join(parts)

                if p.card_data:
                    if p.card_data.card_type == CreditCardData.TYPE_DEBIT:
                        method_desc += ' ' + _('Debit')
                    else:
                        method_desc += ' ' + _(u'Credit')
                    details = '%s - %s - %s' % (p.card_data.auth,
                                                p.card_data.provider.short_name or '',
                                                p.card_data.device.description or '')

                key = (method_desc, details)
                item = sale_payments.setdefault(key, [0, 0])
                item[0] += p.value
                item[1] += 1

            else:
                self.lonely_in_payments.append(p)

            method_summary.setdefault(p.method, [0, 0])
            method_summary[p.method][0] += p.value
            if p.card_data:
                type_desc = p.card_data.short_desc[p.card_data.card_type]
                key = (p.card_data.provider.short_name, type_desc)
                self.card_summary.setdefault(key, 0)
                self.card_summary[key] += p.value

        result = store.find(DailyOutPaymentView, query)
        for p in result.order_by(Payment.identifier):
            if p.purchase:
                purchase_payments = self.purchases.setdefault(p.purchase, [])
                purchase_payments.append(p)
            elif p.sale:
                subtotal = p.sale_subtotal
                value = p.sale.get_total_sale_amount(subtotal)
                salesperson = p.salesperson_name or _('Not Specified')
                client = p.client_name or _('Not Specified')
                sale = DailyMovementSale(identifier=p.sale.identifier,
                                         salesperson=salesperson,
                                         client=client,
                                         return_date=p.sale.return_date,
                                         branch=p.branch_name,
                                         value=value)
                return_sales_payment = self.return_sales.setdefault(sale, [])
                return_sales_payment.append(p)
            else:
                self.lonely_out_payments.append(p)

            method_summary.setdefault(p.method, [0, 0])
            method_summary[p.method][1] += p.value

        self.method_summary = []
        for method, (in_value, out_value) in method_summary.items():
            self.method_summary.append((method,
                                        in_value,
                                        out_value))
        self.method_summary.sort(key=lambda m: _(m[0].description))

        # Till removals
        query = And(Eq(TillEntry.payment_id, None),
                    self._get_query(TillEntry.date, TillEntry.branch),
                    TillEntry.value < 0)
        self.till_removals = store.find(TillEntry, query)

        # Till supply
        query = And(Eq(TillEntry.payment_id, None),
                    self._get_query(TillEntry.date, TillEntry.branch),
                    TillEntry.value > 0)
        self.till_supplies = store.find(TillEntry, query)

    def _show_lonely_payments(self, payments, widget):
        widget.clear()
        for payment in payments:
            payment_data = Settable(identifier=payment.identifier,
                                    method=payment.method.get_description(),
                                    description=payment.description,
                                    branch=payment.branch_name,
                                    value=payment.value)
            widget.append(payment_data)

    def _show_report(self):
        self._generate_dailymovement_data(self.store)

        # Sale data
        self.sales_list.clear()
        for sale, payments in self.sales.items():
            self.sales_list.append(None, sale)
            for details, values in payments.items():
                value = '%s (%sx)' % (get_formatted_price(values[0]), values[1])
                payment_data = Settable(identifier=None,
                                        salesperson=details[0],
                                        client=details[1],
                                        value=value)
                self.sales_list.append(sale, payment_data)

        # Lonely in payments
        self._show_lonely_payments(self.lonely_in_payments,
                                   self.inpayments_list)

        # Purchase data
        self.purchases_list.clear()
        for purchase, payments in self.purchases.items():
            self.purchases_list.append(None, purchase)
            for payment in payments:
                # TODO Add details refering to Bank, Agency later
                payment_data = Settable(identifier=payment.identifier,
                                        notes=payment.method.get_description())
                self.purchases_list.append(purchase, payment_data)

        # Lonely out payments
        self._show_lonely_payments(self.lonely_out_payments,
                                   self.outpayments_list)

        # Return sales
        self.return_sales_list.clear()
        for sale, payments in self.return_sales.items():
            self.return_sales_list.append(None, sale)
            for payment in payments:
                payment_data = Settable(identifier=payment.identifier,
                                        salesperson=payment.method.get_description(),
                                        client=payment.description,
                                        value=get_formatted_price(payment.value))
                self.return_sales_list.append(sale, payment_data)

        # Supplies
        self.supplies_list.clear()
        self.supplies_list.add_list(self.till_supplies)

        # Removals
        self.removals_list.clear()
        self.removals_list.add_list(self.till_removals)

        # Summary's per payment method data
        self.permethod_list.clear()
        self.model.in_subtotal = self.model.out_subtotal = 0
        self.model.in_credit = self.model.out_credit = currency(0)
        for method in self.method_summary:
            method_data = Settable(method=_(method[0].description),
                                   in_value=method[1],
                                   out_value=method[2])
            self.permethod_list.append(method_data)
            self.model.in_subtotal += method[1]
            self.model.out_subtotal += method[2]
            if method[0].method_name == 'credit':
                self.model.in_credit = currency(method[1])
                self.model.out_credit = currency(method[2])

        self.model.in_subtotal = currency(self.model.in_subtotal)
        self.model.out_subtotal = currency(self.model.out_subtotal)
        self.model.in_total = currency(self.model.in_subtotal -
                                       self.model.in_credit)
        self.model.out_total = currency(self.model.out_subtotal -
                                        self.model.out_credit)

        # Summary's per card provider data
        self.percard_list.clear()
        keys = self.card_summary.keys()
        for key in sorted(keys):
            card_summary_data = Settable(provider=key[0] + ' ' + key[1],
                                         income=self.card_summary[key])
            self.percard_list.append(card_summary_data)

        self._update_summary_labels()

    def _get_query(self, date_attr, branch_attr):
        daterange = self.get_daterange()
        query = [Date(date_attr) >= Date(daterange[0]),
                 Date(date_attr) <= Date(daterange[1])]

        branch = self.model.branch
        if branch is not None:
            query.append(branch_attr == branch)
        return And(*query)

    #
    # Public API
    #

    def get_daterange(self):
        start = self.date_filter.get_start_date()
        end = self.date_filter.get_end_date()
        return (start, end)

    def set_daterange(self, start, end=None):
        self.date_filter.set_state(start, end)

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return Settable(branch=api.get_current_branch(store),
                        in_total=currency(0), in_credit=currency(0),
                        in_subtotal=currency(0), out_total=currency(0),
                        out_credit=currency(0), out_subtotal=currency(0))

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, TillDailyMovementDialog.proxy_widgets)

    #
    # Callbacks
    #

    def on_search_button__clicked(self, widget):
        self._show_report()
        self.print_button.set_sensitive(True)

    def on_print_button__clicked(self, widget):
        branch = self.model.branch
        daterange = self.get_daterange()
        print_report(TillDailyMovementReport, self.store, branch, daterange, self)
