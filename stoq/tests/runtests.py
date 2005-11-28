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
##
"""
stoq/tests/domain/runtests.py:

   Run all the domain test suite
"""

import os
import sys
import doctest
import subprocess

from stoq.examples.createall import create
from stoq.lib.admin import setup_tables, ensure_admin_user
from stoq.lib.parameters import ensure_system_parameters
from stoq.lib.runtime import print_immediately, set_test_mode, set_verbose

VERBOSE = '-v' in sys.argv
WITH_EXAMPLES = '-e' in sys.argv

set_verbose(False)
setup_tables(delete_only=True, list_tables=True, verbose=True)
set_verbose(VERBOSE)
setup_tables(verbose=True)
ensure_system_parameters()
ensure_admin_user("Superuser", "administrator", "")

if WITH_EXAMPLES:
    create()

if VERBOSE:
    print_immediately('Performing domain module tests... ')
domain_tests_dir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),
                                                '..', '..', 'docs', 'domain'))
doc_files = [filename for filename in os.listdir(domain_tests_dir)
                          if filename.endswith('.txt')]

set_test_mode(True)
for doc_file in doc_files:
    doc_file = os.path.join(domain_tests_dir, doc_file)
    doctest.testfile(doc_file, verbose=VERBOSE, module_relative=False)
if VERBOSE:
    print_immediately('done')

pytest_args = ['py.test']
if VERBOSE:
    pytest_args.append('-v')
subprocess.call(pytest_args) 
