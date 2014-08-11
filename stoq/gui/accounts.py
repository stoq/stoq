# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
"""
Base class for sharing code between accounts payable and receivable."""

import urllib

from dateutil.relativedelta import relativedelta

import gtk
import pango
from stoqlib.enums import SearchFilterPosition
from stoqlib.api import api
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.dialogs.paymentchangedialog import (PaymentDueDateChangeDialog,
                                                     PaymentStatusChangeDialog)
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.dialogs.paymentflowhistorydialog import PaymentFlowHistoryDialog
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.translation import stoqlib_gettext as _
from storm.expr import And

from stoq.gui.shell.shellapp import ShellApp


class FilterItem(object):
    def __init__(self, name, value, color=None, item_id=None):
        self.name = name
        self.value = value
        self.color = color
        self.id = item_id or name

    def __repr__(self):
        return '<FilterItem "%s">' % (self.name, )


class BaseAccountWindow(ShellApp):

    #
    # Application
    #

    def create_ui(self):
        if api.sysparam.get_bool('SMART_LIST_LOADING'):
            self.search.enable_lazy_search()
        self.results.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self.search.set_summary_label(column='value',
                                      label='<b>%s</b>' % (_('Total'), ),
                                      format='<b>%s</b>',
                                      parent=self.get_statusbar_message_area())
        self.results.set_cell_data_func(self._on_results__cell_data_func)

    def search_completed(self, results, states):
        if len(results):
            return

        state = states[1]
        if state and state.value is None:
            not_found = _("No payments found.")
            payment_url = '<a href="new_payment">%s</a>?' % (
                api.escape(_("create a new payment")))
            new_payment = _("Would you like to %s") % (payment_url, )
            msg = "%s\n\n%s" % (not_found, new_payment)
        else:
            v = state.value.value
            if v == 'status:late':
                msg = _("No late payments found.")
            elif v == 'status:paid':
                msg = _("No paid payments found.")
            elif v == 'status:not-paid':
                if self.search_spec == InPaymentView:
                    msg = _("No payments to receive found.")
                else:
                    msg = _("No payments to pay found.")
            elif v.startswith('category:'):
                category = v.split(':')[1].encode('utf-8')

                not_found = _("No payments in the <b>%s</b> category were found.") % (
                    api.escape(category), )
                payment_url = '<a href="new_payment?%s">%s</a>?' % (
                    urllib.quote(category),
                    _("create a new payment"))
                msg = "%s\n\n%s" % (
                    not_found,
                    _("Would you like to %s") % (payment_url, ))
            else:
                return

        self.search.set_message(msg)

    #
    # Public API
    #

    def add_payment(self, category=None):
        with api.new_store() as store:
            self.run_dialog(self.editor_class, store, category=category)

        if store.committed:
            self._update_filter_items()
            self.refresh()
            self.select_result(self.store.find(self.search_spec,
                                               id=store.retval.id).one())

    def show_details(self, payment_view):
        """Shows some details about the payment, allowing to edit a few
        properties
        """
        with api.new_store() as store:
            payment = store.fetch(payment_view.payment)
            run_dialog(self.editor_class, self, store, payment)

        if store.committed:
            payment_view.sync()
            self.results.update(payment_view)

        return payment

    def show_comments(self, payment_view):
        """Shows a dialog with comments saved on the payment
        @param payment_view: an OutPaymentView or InPaymentView instance
        """
        with api.new_store() as store:
            run_dialog(PaymentCommentsDialog, self, store,
                       payment_view.payment)

        if store.committed:
            payment_view.sync()
            self.results.update(payment_view)

    def change_due_date(self, payment_view, order):
        """ Receives a payment_view and change the payment due date
        related to the view.

        :param payment_view: an OutPaymentView or InPaymentView instance
        :param order: a Sale or Purchase instance related to this payment.
          This will be used to show the identifier of the order
        """
        assert payment_view.can_change_due_date()

        with api.new_store() as store:
            payment = store.fetch(payment_view.payment)
            order = store.fetch(order)
            run_dialog(PaymentDueDateChangeDialog, self, store,
                       payment, order)

        if store.committed:
            # We need to refresh the whole list as the payment(s) can possibly
            # disappear for the selected view
            self.refresh()

    def change_status(self, payment_view, order, status):
        """Show a dialog do enter a reason for status change

        :param payment_view: an OutPaymentView or InPaymentView instance
        :param order: a Sale or Purchase instance related to this payment.
          This will be used to show the identifier of the order
        :param status: The new status to set the payment to
        """
        with api.new_store() as store:
            payment = store.fetch(payment_view.payment)
            order = store.fetch(payment_view.sale)

            if order is None:
                order = store.fetch(payment_view.purchase)

            run_dialog(PaymentStatusChangeDialog, self, store,
                       payment, status, order)

        if store.committed:
            # We need to refresh the whole list as the payment(s) can possibly
            # disappear for the selected view
            self.refresh()

    def create_main_filter(self):
        self.main_filter = ComboSearchFilter(_('Show'), [])

        combo = self.main_filter.combo
        combo.color_attribute = 'color'
        combo.set_row_separator_func(self._on_main_filter__row_separator_func)
        self._update_filter_items()
        executer = self.search.get_query_executer()
        executer.add_filter_query_callback(
            self.main_filter,
            self._create_main_query)
        self.add_filter(self.main_filter, SearchFilterPosition.TOP)

        self.create_branch_filter(column=self.search_spec.branch_id)

    def add_filter_items(self, category_type, options):
        categories = PaymentCategory.get_by_type(self.store, category_type)
        items = [(_('All payments'), None)]

        if categories.count() > 0:
            options.append(FilterItem('sep', 'sep'))

        items.extend([(item.name, item) for item in options])
        for c in categories:
            item = FilterItem(c.name, 'category:%s' % (c.name, ),
                              color=c.color,
                              item_id=c.id)
            items.append((item.name, item))

        self.main_filter.update_values(items)

    #
    # Private
    #

    def _create_main_query(self, state):
        item = state.value
        if item is None:
            return None
        kind, value = item.value.split(':')
        payment_view = self.search_spec
        if kind == 'status':
            if value == 'paid':
                return payment_view.status == Payment.STATUS_PAID
            elif value == 'not-paid':
                return payment_view.status == Payment.STATUS_PENDING
            elif value == 'late':
                tolerance = api.sysparam.get_int('TOLERANCE_FOR_LATE_PAYMENTS')
                return And(
                    payment_view.status == Payment.STATUS_PENDING,
                    payment_view.due_date < localtoday() -
                    relativedelta(days=tolerance))
        elif kind == 'category':
            return payment_view.category == value

        raise AssertionError(kind, value)

    def _show_payment_categories(self):
        store = api.new_store()
        self.run_dialog(PaymentCategoryDialog, store, self.payment_category_type)
        self._update_filter_items()
        store.close()

    #
    # Callbacks
    #

    def _on_main_filter__row_separator_func(self, model, titer):
        if model[titer][0] == 'sep':
            return True
        return False

    def _on_results__cell_data_func(self, column, renderer, pv, text):
        if not isinstance(renderer, gtk.CellRendererText):
            return text

        state = self.main_filter.get_state()

        def show_strikethrough():
            if state.value is None:
                return True
            if state.value.value.startswith('category:'):
                return True
            return False

        is_pending = (pv.status == Payment.STATUS_PENDING)
        show_strikethrough = not is_pending and show_strikethrough()
        is_late = pv.is_late()

        renderer.set_property('strikethrough-set', show_strikethrough)
        renderer.set_property('weight-set', is_late)

        if show_strikethrough:
            renderer.set_property('strikethrough', True)
        if is_late:
            renderer.set_property('weight', pango.WEIGHT_BOLD)

        return text

    def on_results__activate_link(self, results, uri):
        if uri.startswith('new_payment'):
            if '?' in uri:
                category = urllib.unquote(uri.split('?', 1)[1])
            else:
                category = None
            self.add_payment(category=category)

    def on_PaymentFlowHistory__activate(self, action):
        self.run_dialog(PaymentFlowHistoryDialog, self.store)

    def on_PaymentCategories__activate(self, action):
        self._show_payment_categories()
