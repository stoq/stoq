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

from stoqlib.gui.search.parametersearch import ParameterSearch
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.parameters import sysparam, ParameterDetails


class TestParameterSearch(GUITest):
    def test_search(self):
        sysparam.clear_cache()
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

        parameter = sysparam.get_detail_by_name(u'TILLS_ACCOUNT')
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, 'Tills')

    def test_get_parameter_data_options(self):
        search = ParameterSearch(self.store)

        parameter = sysparam.get_detail_by_name(u'SCALE_BARCODE_FORMAT')
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'4 Digits Code with Price')

    def test_get_parameter_data_path_parameter(self):
        parameter = ParameterDetails(u'FOO', 'section', 'short_desc',
                                     'long_desc', unicode,
                                     initial=u'~/.stoq/cat52',
                                     editor='directory-chooser')
        sysparam.register_param(parameter)
        search = ParameterSearch(self.store)

        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'~/.stoq/cat52')
        sysparam._details.pop('FOO')

    def test_get_parameter_data_bool(self):
        search = ParameterSearch(self.store)

        parameter = sysparam.get_detail_by_name(u'DISABLE_COOKIES')
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, 'No')

    def test_get_parameter_data_country_suggested(self):
        search = ParameterSearch(self.store)

        parameter = sysparam.get_detail_by_name(u'COUNTRY_SUGGESTED')
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'Brazil')

    def test_get_parameter_data_unicode(self):
        search = ParameterSearch(self.store)

        parameter = sysparam.get_detail_by_name(u'STATE_SUGGESTED')
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'SP')

    def test_get_parameter_data_else(self):
        search = ParameterSearch(self.store)

        parameter = sysparam.get_detail_by_name(u'DEFAULT_AREA_CODE')
        value = search._get_parameter_value(parameter)
        self.assertEquals(value, u'16')
