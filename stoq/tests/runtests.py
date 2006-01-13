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

import os
import sys
import doctest
import py 

from kiwi import environ
from stoq.lib.runtime import print_immediately, set_test_mode, set_verbose
# This must be called *before* anything else since it will switch to test
# database and also change the runtime module behaviour
set_test_mode(True)

from stoq.examples.createall import create
from stoq.lib.admin import setup_tables, ensure_admin_user
from stoq.lib.parameters import ensure_system_parameters

VERBOSE = '-v' in sys.argv


def setup():
    set_verbose(False)
    setup_tables(delete_only=True, list_tables=True, verbose=True)
    set_verbose(VERBOSE)
    setup_tables(verbose=True)
    ensure_system_parameters()
    ensure_admin_user("Superuser", "administrator", "")

    create()
    
def test_gui():
    if VERBOSE:
        print_immediately('Performing gui module tests... ')
        
    root = os.path.abspath(os.path.join(sys.argv[0], '..', '..', '..'))
    oldpwd = os.getcwd()
    os.chdir(root)
    
    # Running kiwi-ui tests
    gui_tests_dir = os.path.abspath(os.path.join(root, 'stoq', 'tests', 'gui'))
    gui_tests = [filename
                 for filename in os.listdir(gui_tests_dir)
                     if filename.endswith('.py') and filename[0] != '_']
    for test_file in gui_tests:
        if VERBOSE:
            print 'RUNNING', test_file
            print '='*79
        environ.app = None
        execfile(os.path.join(gui_tests_dir, test_file))
        if VERBOSE:
            print '='*79
    os.chdir(oldpwd)

    if VERBOSE:
        print_immediately('gui tests ok')

def test_domain():
    if VERBOSE:
        print_immediately('Performing domain tests... ')

    # Running doctests
    domain_tests_dir = os.path.abspath(os.path.join(
        os.path.dirname(sys.argv[0]),
        '..', '..', 'docs', 'domain'))
    doc_files = [filename for filename in os.listdir(domain_tests_dir)
                              if filename.endswith('.txt')]

    for doc_file in doc_files:
        doc_file = os.path.join(domain_tests_dir, doc_file)
        doctest.testfile(doc_file, verbose=VERBOSE, module_relative=False)

    if '-v' in sys.argv:
        sys.argv.remove('-v')
    py.test.cmdline.main()

    if VERBOSE:
        print_immediately('domain tests ok')

setup()

test_domain()
test_gui()

