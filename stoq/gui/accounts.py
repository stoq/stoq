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

import gettext
import urllib

import gtk
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
import pango
from stoqlib.api import api
from stoqlib.database.orm import AND, const
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.dialogs.paymentflowhistorydialog import PaymentFlowHistoryDialog

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class FilterItem(object):
    def __init__(self, name, value, color=None, item_id=None):
        self.name = name
        self.value = value
        self.color = color
        self.id = item_id or name

    def __repr__(self):
        return '<FilterItem "%s">' % (self.name, )


class BaseAccountWindow(SearchableAppWindow):
    embedded = True

    #
    # Application
    #

    def create_ui(self):
        self.results.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self.search.set_summary_label(column='value',
                                      label='<b>Total:</b>',
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
                _("create a new payment"))
            new_payment = _("Would you like to %s") % (payment_url, )
            msg = "%s\n\n%s" % (not_found, new_payment)
        else:
            v = state.value.value
            if v == 'status:late':
                msg = _("No late payments found.")
            elif v == 'status:paid':
                msg = _("No paid payments found.")
            elif v == 'status:not-paid':
                if self.search_table == InPaymentView:
                    msg = _("No payments to receive found.")
                else:
                    msg = _("No payments to pay found.")
            elif v.startswith('category:'):
                category = v.split(':')[1].encode('utf-8')

                not_found = _("No payments in the <b>%s</b> category were found." % (
                    category, ))
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
        raise NotImplementedError("Must be implemented in base class")

    def create_main_filter(self):
        self.main_filter = ComboSearchFilter(_('Show'), [])

        combo = self.main_filter.combo
        combo.color_attribute = 'color'
        combo.set_row_separator_func(self._on_main_filter__row_separator_func)
        self._update_filter_items()
        self.executer.add_filter_query_callback(
            self.main_filter,
            self._on_main_filter__query_callback)
        self.add_filter(self.main_filter, SearchFilterPosition.TOP)

    def add_filter_items(self, category_type, options):
        categories = PaymentCategory.selectBy(
            connection=self.conn,
            category_type=category_type).orderBy('name')
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
        payment_view = self.search_table
        if kind == 'status':
            if value == 'paid':
                return payment_view.q.status == Payment.STATUS_PAID
            elif value == 'not-paid':
                return payment_view.q.status == Payment.STATUS_PENDING
            elif value == 'late':
                return AND(
                    payment_view.q.status != Payment.STATUS_PAID,
                    payment_view.q.status != Payment.STATUS_CANCELLED,
                    payment_view.q.due_date < const.NOW())
        elif kind == 'category':
            return payment_view.q.category == value

        raise AssertionError(kind, value)

    def _show_payment_categories(self):
        trans = api.new_transaction()
        self.run_dialog(PaymentCategoryDialog, trans, self.payment_category_type)
        self._update_filter_items()
        trans.close()

    #
    # Callbacks
    #

    def _on_main_filter__row_separator_func(self, model, titer):
        if model[titer][0] == 'sep':
            return True
        return False

    def _on_main_filter__query_callback(self, state):
        return self._create_main_query(state)

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
        self.run_dialog(PaymentFlowHistoryDialog, self.conn)

    def on_PaymentCategories__activate(self, action):
        self._show_payment_categories()
