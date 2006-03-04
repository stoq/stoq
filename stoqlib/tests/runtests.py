#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
##            Johan Dahlin              <jdahlin@async.com.br>
##
""" Infrastructure for running test suites """

import doctest
import optparse
import os
import sys

import gobject
gobject.threads_init()
import py

from stoqlib.lib.runtime import (print_immediately, set_verbose,
                                 register_application_names)

DEFAULT_SEPARATORS = 79


def setup(options):
    from stoqlib.domain.examples.createall import create
    from stoqlib.lib.admin import initialize_system, setup_tables

    set_verbose(False)
    setup_tables(delete_only=True, list_tables=True, verbose=True)
    set_verbose(options.verbose)
    initialize_system("", verbose=True)
    create()


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
    if options.nocapture:
        sys.argv.append('--nocapture')
    py.test.cmdline.main()

    if options.verbose:
        print_immediately('Domain tests are ok')


def get_parser():
    parser = optparse.OptionParser()

    # Database connection settings
    parser.add_option('-a', '--address',
                      action="store",
                      dest="address",
                      default='localhost',
                      help='Database address to connect to')
    parser.add_option('-p', '--port',
                      action="store",
                      dest="port",
                      default='5432',
                      help='Database port')
    parser.add_option('-d', '--dbname',
                      action="store",
                      dest="dbname",
                      default='%s_test' % os.getlogin(),
                      help='Database name to use')
    parser.add_option('-u', '--username',
                      action="store",
                      dest="username",
                      default=os.getlogin(),
                      help='Database username')
    parser.add_option('-w', '--password',
                      action="store",
                      dest="password",
                      default='',
                      help='user password')

    # Additional options
    parser.add_option('-v', '--verbose',
                      action="store_true",
                      dest="verbose")
    parser.add_option('-c', '--nocapture',
                      action="store_true",
                      dest="nocapture",
                      help='Get print outputs on tests')
    parser.add_option('-f', '--filename',
                      action="store",
                      type="string",
                      dest="filename",
                      default="stoq.conf",
                      help='Use this file name for config file')
    return parser


def main(args):
    parser = get_parser()

    if '--g-fatal-warnings' in args:
        args.remove('--g-fatal-warnings')
    options, args = parser.parse_args(args)

    from stoqlib.database import register_db_settings, DatabaseSettings

    db_settings = DatabaseSettings(address=options.address,
                                   port=options.port,
                                   dbname=options.dbname,
                                   username=options.username,
                                   password=options.password)

    register_db_settings(db_settings)
    register_application_names(["stoqlib_app"])

    setup(options)
    test_domain(options)


if __name__ == '__main__':
    sys.exit(main(sys.argv[:]))
