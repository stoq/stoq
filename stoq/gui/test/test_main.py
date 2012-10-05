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

import unittest

import mock
from nose.exc import SkipTest
from kiwi.component import remove_utility, get_utility, provide_utility
from kiwi.ui.widgets.label import ProxyLabel
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.settings import get_settings

from stoq.main import get_shell


class TestMain(unittest.TestCase):
    def setUp(self):
        self._iappinfo = get_utility(IAppInfo)
        # Shell will provide this utility
        remove_utility(IAppInfo)

    def tearDown(self):
        provide_utility(IAppInfo, self._iappinfo, replace=True)
        # Shell.bootstrap calls
        # ProxyLabel.replace('$CURRENCY', get_localeconv()['currency_symbol'])
        # and that will break uitests
        if '$CURRENCY' in ProxyLabel._label_replacements:
            del ProxyLabel._label_replacements['$CURRENCY']

    def testShellBootstrap(self):
        raise SkipTest("Missing dependencies on jenkins. Will fix soon!")

        shell = get_shell([])
        for func in [
            # Those two fail as testsuit already setup them
            '_setup_gobject',
            '_setup_twisted',
            # Do not setup database, as it may want to do a migration,
            # activate plugins, check db version, etc.
            # We may want to test this in the future
            '_setup_database',
            ]:
            mocked = mock.patch.object(shell, func, new=lambda: None)
            mocked.start()

        settings = get_settings()
        original_get = settings.get

        def get(name, default=None):
            if name == 'user-locale':
                return None
            return original_get(name, default=default)

        # Do not show the splash screen during the tests
        with mock.patch('stoqlib.gui.splash.show_splash', new=lambda: None):
            # If the locale is changed here, gui tests will break
            with mock.patch.object(settings, 'get', get):
                shell.bootstrap()
