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
from kiwi.component import remove_utility, get_utility, provide_utility
from kiwi.ui.widgets.label import ProxyLabel
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.settings import get_settings

import stoq
from stoq.main import main
from stoq.gui.shell.bootstrap import ShellBootstrap


class TestMain(unittest.TestCase):
    def setUp(self):
        self._mocks = []

        self._iappinfo = get_utility(IAppInfo)
        # Shell will provide this utility
        remove_utility(IAppInfo)

        # If the locale is changed here, gui tests will break
        mocked = mock.patch.dict(get_settings()._root, clear=True)
        self._mocks.append(mocked)

        # Do not show the splash screen during the tests
        mocked = mock.patch('stoqlib.gui.widgets.splash.show_splash',
                            new=lambda: None)
        self._mocks.append(mocked)

        # If a dependency is missing, avoid showing an error message
        # or else jenkins will hang
        mocked = mock.patch('stoq.lib.dependencies.DependencyChecker._error',
                            new=lambda *args: None)
        self._mocks.append(mocked)

        for mocked in self._mocks:
            mocked.start()

    def tearDown(self):
        provide_utility(IAppInfo, self._iappinfo, replace=True)
        # Shell.bootstrap calls
        # ProxyLabel.replace('$CURRENCY', get_localeconv()['currency_symbol'])
        # and that will break uitests
        if '$CURRENCY' in ProxyLabel._label_replacements:
            del ProxyLabel._label_replacements['$CURRENCY']

        for mocked in self._mocks:
            mocked.stop()

    def test_shell_bootstrap(self):
        options = mock.Mock()
        bootstrap = ShellBootstrap(options=options, initial=True)
        mocks = []
        for func in [
                # Those two fail as testsuit already setup them
                '_setup_gobject',
                '_setup_twisted']:
            mocked = mock.patch.object(bootstrap, func, new=lambda: None)
            mocks.append(mocked)
            mocked.start()

        try:
            bootstrap.bootstrap()
        finally:
            for mocked in mocks:
                mocked.stop()

    @mock.patch('stoq.gui.shell.bootstrap.boot_shell')
    def test_main(self, boot_shell):
        main(['stoq'])
        boot_shell().main.assert_called_once_with(None, None)
        boot_shell.reset_mock()

        main(['stoq', 'payable'])
        boot_shell().main.assert_called_once_with('payable', None)
        boot_shell.reset_mock()

        main(['stoq', 'payable/'])
        boot_shell().main.assert_called_once_with('payable', None)
        boot_shell.reset_mock()

        main(['stoq', 'payable', 'AddPayment'])
        boot_shell().main.assert_called_once_with('payable', 'AddPayment')
        boot_shell.reset_mock()

        with self.assertRaisesRegexp(SystemExit,
                                     stoq.version):
            main(['stoq', '--version'])

        with self.assertRaisesRegexp(
            SystemExit,
            r"'no-such-app' is not an application. "
            r"Valid applications are: \[[a-z,\' ]+\]"):
            main(['stoq', 'no-such-app'])
