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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Evandro Vale Miquelito    <evandro@async.com.br>
##            Rudá Porto Filgueiras     <rudazz@gmail.com>
##
""" Run all the domain test suite """

import optparse
import os
import sys

import gobject
gobject.threads_init()
from kiwi import environ

from stoq.main import setup_stoqlib_settings
setup_stoqlib_settings()

from stoqlib.lib.runtime import (print_immediately, get_connection,
                                 set_test_mode, set_verbose,
                                 register_configparser_settings)

DEFAULT_SEPARATORS = 79

def setup(options):
    # This must be called *before* anything else since it will switch to test
    # database and also change the runtime module behaviour
    set_test_mode(True)
    from stoqlib.domain.examples.createall import create
    from stoqlib.lib.admin import initialize_system
    from stoqlib.database import setup_tables

    set_verbose(False)
    setup_tables(delete_only=True, list_tables=True, verbose=True)
    set_verbose(options.verbose)
    initialize_system("Superuser", "administrator", "", verbose=True)
    create()

def test_gui(options, tests=None):
    from kiwi.ui.test.player import TimeOutError
    from stoqlib.lib.runtime import new_transaction

    if options.verbose:
        print_immediately('Performing gui module tests... ')

    root = os.path.abspath(os.path.join(sys.argv[0], '..', '..', '..'))
    oldpwd = os.getcwd()
    os.chdir(root)

    # Running kiwi-ui tests
    if not tests:
        test_dir = os.path.abspath(os.path.join(root, 'stoq', 'tests', 'gui'))
        tests = [os.path.join(test_dir, filename)
                 for filename in os.listdir(test_dir)
                     if filename.endswith('.py') and filename[0] != '_']
    else:
        tests = [os.path.join(oldpwd, test) for test in tests]

    # Sort the tests so they're run in a predictible order
    # useful for tests which depend on others being ran before
    tests.sort()

    conn = get_connection()
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
            try:
                execfile(filename, globs)
            except TimeOutError, e:
                print 'TIMEOUT ERROR: %s' % e
                os._exit(1)
            raise SystemExit

        pid, status = os.waitpid(pid, 0)
        if status != 0:
            print '%s failed' % test_name
            return 1
        else:
            post_hook = globs.get('post_hook')
            if post_hook:
                post_hook(new_transaction())

        if options.verbose:
            print '=' * DEFAULT_SEPARATORS

    os.chdir(oldpwd)

    if options.verbose:
        print_immediately('gui tests ok')

    return 0

def main(args):
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbose',
                      action="store_true",
                      dest="verbose")
    parser.add_option('-f', '--filename',
                      action="store",
                      type="string",
                      dest="filename",
                      default="stoq.conf",
                      help='Use this file name for config file')

    if '--g-fatal-warnings' in args:
        args.remove('--g-fatal-warnings')
    options, args = parser.parse_args(args)
    register_configparser_settings('stoq', options.filename)
    setup(options)

    return test_gui(options, args[1:])

if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))
