#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
"""
stoq/tests/domain/runtests.py:

   Run all the domain test suite
"""

import doctest
import optparse
import os
import sys

import gobject
gobject.threads_init()
from kiwi import environ
import py

from stoq.main import setup_stoqlib_settings
setup_stoqlib_settings()

from stoqlib.lib.runtime import (print_immediately, get_connection,
                                 set_test_mode, set_verbose)

DEFAULT_SEPARATORS = 79

def setup(options):
    # This must be called *before* anything else since it will switch to test
    # database and also change the runtime module behaviour
    set_test_mode(True)
    from stoq.examples.createall import create
    from stoqlib.lib.admin import initialize_system, setup_tables

    set_verbose(False)
    setup_tables(delete_only=True, list_tables=True, verbose=True)
    set_verbose(options.verbose)
    initialize_system("Superuser", "administrator", "", verbose=True)
    create()

def test_gui(options, tests=None):
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

    conn = get_connection()

    for test_name in tests:
        if options.verbose:
            print 'RUNNING', os.path.basename(test_name)
            print '=' * DEFAULT_SEPARATORS
        globs = {}
        environ.app = None

        execfile(test_name, globs)

        post_hook = globs.get('post_hook')
        if post_hook:
            post_hook(new_transaction())

        if options.verbose:
            print '=' * DEFAULT_SEPARATORS
    os.chdir(oldpwd)

    if options.verbose:
        print_immediately('gui tests ok')

def test_domain(options):
    if options.verbose:
        print_immediately('Running domain doctests... ')

    # Running doctests
    domain_tests_dir = os.path.abspath(os.path.join(
        os.path.dirname(sys.argv[0]), '..', '..', 'docs', 'domain'))
    doc_files = [filename for filename in os.listdir(domain_tests_dir)
                              if filename.endswith('.txt')]

    for doc_file in doc_files:
        doc_file = os.path.join(domain_tests_dir, doc_file)
        doctest.testfile(doc_file,
                         verbose=options.verbose,
                         module_relative=False)

    if options.verbose:
        print_immediately('Running domain unittests... ')

    sys.argv = sys.argv[:1]
    py.test.cmdline.main()

    if options.verbose:
        print_immediately('Domain tests are ok')

def main(args):
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbose',
                      action="store_true",
                      dest="verbose")
    parser.add_option('-g', '--gui',
                      action="store_true",
                      dest="only_gui",
                      help='Only run gui tests')
    parser.add_option('-d', '--domain',
                      action="store_true",
                      dest="only_domain",
                      help='Only run domain tests')

    if '--g-fatal-warnings' in args:
        args.remove('--g-fatal-warnings')
    options, args = parser.parse_args(args)
    setup(options)

    if options.only_domain:
        test_domain(options)
        return

    if options.only_gui:
        test_gui(options, args[1:])
        return

    test_domain(options)
    test_gui(options)

if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))
