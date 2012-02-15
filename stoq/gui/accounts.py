# -*- Mode: Python; coding: iso-8859-1 -*-
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

from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from stoqlib.database.orm import AND, const
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment

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

    # Callbacks

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

    def _on_main_filter__row_separator_func(self, model, titer):
        if model[titer][0] == 'sep':
            return True
        return False

    def _on_main_filter__query_callback(self, state):
        return self._create_main_query(state)
