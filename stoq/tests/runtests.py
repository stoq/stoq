#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
""" Run all the domain test suite """

import os
import sys

from kiwi import environ
from kiwi.log import set_log_level
from stoqlib.lib.configparser import StoqConfig

from stoq.lib.options import get_option_parser
from stoq.lib.startup import (setup,
                              create_examples,
                              clean_database)

DEFAULT_SEPARATORS = 79


def test_gui(config, options, tests=None):
    from stoqlib.database.runtime import new_transaction

    if options.verbose:
        set_log_level('uitest', 5)
        print 'Performing gui module tests... '

    root = os.path.abspath(os.path.join(sys.argv[0], '..', '..', '..'))
    oldpwd = os.getcwd()
    os.chdir(root)

    # Running kiwi-ui tests
    if not tests:
        test_dir = os.path.abspath(
            os.path.join(root, 'stoq', 'tests', 'gui'))
        tests = [os.path.join(test_dir, filename)
                 for filename in os.listdir(test_dir)
                     if filename.endswith('.py') and filename[0] != '_']
    else:
        tests = [os.path.join(oldpwd, test) for test in tests]

    # Sort the tests so they're run in a predictible order
    # useful for tests which depend on others being ran before
    tests.sort()

    if 'gtk' in sys.modules:
        raise AssertionError("Gtk cannot be loaded at this point")

    create_examples(config)
    from stoqlib.doman.station import create_station
    from stoqlib.exceptions import StoqlibError
    from stoqlib.database.database import get_connection
    conn = get_connection()
    try:
        create_station(conn)
    except StoqlibError:
        pass
    conn.commit()

    os.environ['STOQ_TEST_MODE'] = '1'

    for filename in tests:
        test_name = os.path.basename(filename)
        if options.verbose:
            print 'RUNNING', test_name
            print '=' * DEFAULT_SEPARATORS
        globs = {}
        environ.app = None

        # Run each tests in a child process, since kiwis ui test framework
        # is not completely capable of cleaning up all it's state
        # seems to be highly threads related.
        pid = os.fork()
        if not pid:
            # Do thread initialization here, in the child process
            # avoids strange X errors
            from kiwi.ui.test.player import play_file, TimeOutError

            try:
                play_file(filename, globs)
            except TimeOutError, e:
                print '*' * 50
                print '* TIMEOUT ERROR: %s' % e
                print '*' * 50
                os._exit(1)
            raise SystemExit

        pid, status = os.waitpid(pid, 0)
        if status != 0:
            print '%s failed' % test_name
            return 1

        post_hook = globs.get('post_hook')
        if post_hook:
            post_hook(new_transaction())

        if options.verbose:
            print '=' * DEFAULT_SEPARATORS

    os.chdir(oldpwd)
    if options.verbose:
        print 'gui tests ok'
    return 0


def main(args):
    parser = get_option_parser()
    options, args = parser.parse_args(args)

    # If a filename is specified on the commandline,
    # send it to all the tests, so we won't end up
    # using different configuration files
    filename = None
    if options.filename:
        filename = options.filename
        if not os.path.exists(filename):
            raise SystemExit("No such a file or directory: %s" % filename)

    config = StoqConfig()
    config.load(filename)
    if not options.dbname:
        config.use_test_database()

    setup(config, options)
    clean_database(config, options)

    return test_gui(config, options, args[1:])

if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))
