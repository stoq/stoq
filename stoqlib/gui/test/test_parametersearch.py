# -*- coding: utf-8 -*-
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

import mock

from stoqlib.domain.parameter import ParameterData
from stoqlib.gui.search.parametersearch import ParameterSearch
from stoqlib.gui.test.uitestutils import GUITest


class TestParameterSearch(GUITest):
    def test_search(self):
        with self.sysparam(USER_HASH=u'6f33a354e3104fcbae0f7b08087136d4'):
            search = ParameterSearch(self.store)

            self.check_search(search, 'parameter-no-filter')

            # clicking on search button
            search.entry.set_text('')
            self.click(search.search_button)
            self.check_search(search, 'parameter-no-filter')

            # multiple words in any order search
            search.entry.set_text('city default')
            search.entry.activate()
            self.check_search(search, 'parameter-string-multiple-words-filter')

            search.entry.set_text('account')
            search.entry.activate()
            self.check_search(search, 'parameter-string-filter')

            self.click(search.show_all_button)
            self.check_search(search, 'parameter-no-filter')

    @mock.patch('stoqlib.gui.search.parametersearch.run_dialog')
    def test_edit(self, run_dialog):
        search = ParameterSearch(self.store)

        self.assertNotSensitive(search, ['edit_button'])

        search.results.select(search.results[0])
        self.click(search.edit_button)
        self.assertEquals(run_dialog.call_count, 1)

        run_dialog.reset_mock()
        search.on_results__double_click(list(search.results),
                                        search.results[0])
        self.assertEquals(run_dialog.call_count, 1)

        run_dialog.reset_mock()
        search.on_results__row_activated(list(search.results),
                                         search.results[0])
        self.assertEquals(run_dialog.call_count, 1)

    def test_get_parameter_data_domain(self):
        search = ParameterSearch(self.store)

        parameter = self.store.find(ParameterData,
                                    field_name=u'TILLS_ACCOUNT').one()
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, 'Tills')

    def test_get_parameter_data_options(self):
        search = ParameterSearch(self.store)

        parameter = self.store.find(ParameterData,
                                    field_name=u'SCALE_BARCODE_FORMAT').one()
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'4 Digits Code with Price')

    def test_get_parameter_data_path_parameter(self):
        search = ParameterSearch(self.store)

        parameter = self.store.find(ParameterData,
                                    field_name=u'CAT52_DEST_DIR').one()
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'~/.stoq/cat52')

    def test_get_parameter_data_bool(self):
        search = ParameterSearch(self.store)

        parameter = self.store.find(ParameterData,
                                    field_name=u'DISABLE_COOKIES').one()
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, 'No')

    def test_get_parameter_data_country_suggested(self):
        search = ParameterSearch(self.store)

        parameter = self.store.find(ParameterData,
                                    field_name=u'COUNTRY_SUGGESTED').one()
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'Brazil')

    def test_get_parameter_data_unicode(self):
        search = ParameterSearch(self.store)

        parameter = self.store.find(ParameterData,
                                    field_name=u'STATE_SUGGESTED').one()
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'SP')

    def test_get_parameter_data_else(self):
        search = ParameterSearch(self.store)

        parameter = self.store.find(ParameterData,
                                    field_name=u'DEFAULT_AREA_CODE').one()
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'16')
