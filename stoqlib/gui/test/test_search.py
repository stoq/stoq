# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

import datetime
import locale
import mock
import os
import unittest

from dateutil import relativedelta
from dateutil.relativedelta import SU, MO, SA, relativedelta as delta

from stoqlib.api import api
from stoqlib.domain.product import Product
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.events import SearchDialogSetupSearchEvent
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.searchextension import SearchExtension
from stoqlib.gui.search.searchcolumns import SearchColumn, QuantityColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import (StringSearchFilter, DateSearchFilter,
                                              ComboSearchFilter, NumberSearchFilter)
from stoqlib.gui.search.searchoptions import (ThisWeek, LastWeek, NextWeek, ThisMonth,
                                              LastMonth, NextMonth)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.defaults import get_weekday_start
from stoqlib.lib.introspection import get_all_classes


class TestDateOptions(unittest.TestCase):
    def setUp(self):
        self._original_locale = locale.getlocale(locale.LC_ALL)

    def tearDown(self):
        self._set_locale(self._original_locale)

    def _get_week_interval(self, today):
        weekday = get_weekday_start()
        start = today + delta(weekday=weekday(-1))
        end = start + delta(days=+6)
        return start, end

    def _get_month_interval(self, today):
        start = today + delta(day=1)
        end = start + delta(day=31)
        return start, end

    def _get_locales(self):
        # en_US: week starts on sunday
        # es_ES: week starts on monday
        return ["en_US.UTF-8", "es_ES.UTF-8"]

    def _starts_on_sunday(self, loc):
        return loc.startswith("en_US")

    def _set_locale(self, loc):
        try:
            loc = locale.setlocale(locale.LC_ALL, loc)
        except locale.Error:
            # Some locales could not be available on user's machine, leading
            # him to a false positive broke test, so skip it, informing the
            # problem.
            raise unittest.SkipTest("Locale %s not available" % (loc, ))
        else:
            os.environ['LC_ALL'] = loc

    def _testWeekday(self, loc, interval):
        if self._starts_on_sunday(loc):
            self.assertEqual(
                relativedelta.weekday(interval[0].weekday()), SU)
            self.assertEqual(
                relativedelta.weekday(interval[1].weekday()), SA)
        else:
            self.assertEqual(
                relativedelta.weekday(interval[0].weekday()), MO)
            self.assertEqual(
                relativedelta.weekday(interval[1].weekday()), SU)

    def test_this_week(self):
        option = ThisWeek()
        for loc in self._get_locales():
            self._set_locale(loc)
            # starting in 2008/01/01, wednesday
            for i in range(1, 8):
                get_today_date = lambda: datetime.date(2008, 1, i)
                option.get_today_date = get_today_date
                self.assertEqual(option.get_interval(),
                                 self._get_week_interval(get_today_date()))
                self._testWeekday(loc, option.get_interval())

    def test_last_week(self):
        option = LastWeek()
        for loc in self._get_locales():
            self._set_locale(loc)
            # starting in 2008/01/01, wednesday
            for i in range(1, 8):
                get_today_date = lambda: datetime.date(2008, 1, i)
                option.get_today_date = get_today_date

                last_week_day = get_today_date() + delta(weeks=-1)
                self.assertEqual(option.get_interval(),
                                 self._get_week_interval(last_week_day))
                self._testWeekday(loc, option.get_interval())

    def test_next_week(self):
        option = NextWeek()
        for loc in self._get_locales():
            self._set_locale(loc)
            # starting in 2008/01/01, wednesday
            for i in range(1, 8):
                get_today_date = lambda: datetime.date(2008, 1, i)
                option.get_today_date = get_today_date

                next_week_day = get_today_date() + delta(weeks=+1)
                self.assertEqual(option.get_interval(),
                                 self._get_week_interval(next_week_day))
                self._testWeekday(loc, option.get_interval())

    def test_this_month(self):
        option = ThisMonth()
        for loc in self._get_locales():
            self._set_locale(loc)
            for month_day in [datetime.date(2007, 1, 1),
                              datetime.date(2007, 1, 15),
                              datetime.date(2007, 1, 31)]:
                option.get_today_date = lambda: month_day

                self.assertEqual(option.get_interval(),
                                 self._get_month_interval(month_day))

    def test_last_month(self):
        option = LastMonth()
        for loc in self._get_locales():
            self._set_locale(loc)
            for month_day in [datetime.date(2007, 1, 1),
                              datetime.date(2007, 1, 15),
                              datetime.date(2007, 1, 31)]:
                option.get_today_date = lambda: month_day

                last_month_day = month_day + delta(months=-1)
                self.assertEqual(option.get_interval(),
                                 self._get_month_interval(last_month_day))

    def test_next_month(self):
        option = NextMonth()
        for loc in self._get_locales():
            self._set_locale(loc)
            for month_day in [datetime.date(2007, 1, 1),
                              datetime.date(2007, 1, 15),
                              datetime.date(2007, 1, 31)]:
                option.get_today_date = lambda: month_day

                next_month_day = month_day + delta(months=+1)
                self.assertEqual(option.get_interval(),
                                 self._get_month_interval(next_month_day))


class TestSearchEditor(GUITest):
    """Tests for SearchEditor"""

    @mock.patch('stoqlib.gui.search.searcheditor.api.new_store')
    @mock.patch('stoqlib.gui.search.searcheditor.run_dialog')
    def test_run_editor(self, run_dialog, new_store):
        run_dialog.return_value = True
        new_store.return_value = self.store
        dialog = ProductSearch(store=self.store)
        dialog.search.refresh()
        dialog.results.select(dialog.results[0])
        product = dialog.results[0].product

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(dialog._toolbar.edit_button)
                run_dialog.assert_called_once_with(ProductEditor, dialog,
                                                   self.store, product,
                                                   visual_mode=False)


class TestSearchEvent(GUITest):
    def test_search_dialog_setup_search(self):
        class ProductSearchExtention(SearchExtension):
            spec_attributes = dict(ncm=Product.ncm)

            def get_columns(self):
                return [SearchColumn('ncm', title='NCM', data_type=str)]

        def _setup_search(dialog):
            return dialog.add_extension(ProductSearchExtention())

        # At leat one product should have a NCM value, so we can verify the
        # results.
        product = self.store.find(Product).order_by(Product.te_id).first()
        product.ncm = u'12345678'

        SearchDialogSetupSearchEvent.connect(_setup_search)
        dialog = ProductSearch(self.store)
        dialog.search.refresh()
        self.check_search(dialog, 'product-search-extended')


class TestQuantityColumn(GUITest):
    def test_format_func(self):
        class Fake(object):
            quantity = 0

        column = QuantityColumn('quantity')
        obj = Fake()

        obj.quantity = None
        self.assertEquals(column._format_func(obj, True), '0')

        obj.quantity = 0
        self.assertEquals(column._format_func(obj, True), '0')

        obj.quantity = 1
        self.assertEquals(column._format_func(obj, True), '1')

        obj.product = self.create_product()
        obj.sellable = obj.product.sellable

        # Without a unit, it should still return just the number
        obj.quantity = 1
        self.assertEquals(column._format_func(obj, True), '1')

        obj.sellable.unit = self.create_sellable_unit(u'Pc')
        self.assertEquals(column._format_func(obj, True), '1 Pc')

        obj.product.manage_stock = False
        self.assertEquals(column._format_func(obj, True), '1 Pc')

        obj.quantity = 0
        self.assertEquals(column._format_func(obj, True), u"\u221E")


class TestSearchGeneric(DomainTest):
    """Generic tests for searches"""

    # Those are base classes for other searches, and should not be instanciated
    ignored_classes = [
        '_BaseBillCheckSearch',
        'SearchEditor',
        'BasePersonSearch',
    ]

    @classmethod
    def _get_all_searches(cls):
        for klass in get_all_classes('stoqlib/gui'):
            try:
                if klass.__name__ in cls.ignored_classes:
                    continue
                # Exclude SearchDialog, since we just want to test it's subclasses
                if not issubclass(klass, SearchDialog) or klass is SearchDialog:
                    continue
            except TypeError:
                continue

            yield klass

    def _test_search(self, search_class):
        # XXX: If we use self.store, the all this tests passes, but the test
        # executed after this will break with
        # storm.exceptions.ClosedError('Connection is closed',)
        store = api.new_store()
        if search_class.__name__ == 'ProductBranchSearch':
            from stoqlib.domain.product import Storable
            # This dialog must have a storable to be able to search it in stock
            storable = store.find(Storable).any()
            dialog = search_class(store, storable)
        else:
            dialog = search_class(store)

        # There may be no results in the search, but we only want to check if
        # the query is executed properly
        dialog.search.refresh()

        # Testing SearchColumns only makes sense if advanced search is enabled
        if not dialog.search.menu:
            return

        columns = dialog.search.result_view.get_columns()
        for i in columns:
            if not isinstance(i, SearchColumn):
                continue

            filter = dialog.search.add_filter_by_attribute(
                i.search_attribute, i.get_search_label(),
                i.data_type, i.valid_values, i.search_func, i.use_having)

            # Set some value in the filter, so that it acctually is included in
            # the query
            if isinstance(filter, StringSearchFilter):
                filter.set_state('foo')
            elif isinstance(filter, DateSearchFilter):
                filter.set_state(datetime.date(2012, 1, 1),
                                 datetime.date(2012, 10, 10))
            elif isinstance(filter, NumberSearchFilter):
                filter.set_state(1, 3)
            elif isinstance(filter, ComboSearchFilter):
                for key, value in filter.combo.get_model_items().items():
                    if value:
                        filter.set_state(value)
                        break
            dialog.search.refresh()

            # Remove the filter so it wont affect other searches
            filter.emit('removed')

        store.close()


for search in TestSearchGeneric._get_all_searches():
    name = 'test' + search.__name__
    func = lambda s, v=search: TestSearchGeneric._test_search(s, v)
    func.__name__ = name
    setattr(TestSearchGeneric, name, func)
    del func
