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

from stoq.lib.runtime import print_immediately, set_test_mode
from stoq.environ import get_sbin_file_path, get_docs_dir


VERBOSE = '-v' in sys.argv
IGNORE_EXAMPLES = '-i' in sys.argv

print_immediately('Initializing test database... ')
initdb_file = get_sbin_file_path('init-database')
initdb_args = [initdb_file, '-t', '-v']
if not IGNORE_EXAMPLES:
    initdb_args.append('-e')
subprocess.call(initdb_args)

print_immediately('Performing domain module tests... ')
domain_tests_dir = os.path.join(get_docs_dir(), 'domain')
doc_files = [filename for filename in os.listdir(domain_tests_dir)
                    if filename.endswith('.txt')]
                        
set_test_mode(True)
for doc_file in doc_files:
    doc_file = os.path.join(domain_tests_dir, doc_file)
    doctest.testfile(doc_file, verbose=VERBOSE, module_relative=False)
print_immediately('done')
