# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin  <jdahlin@async.com.br>
##
""" Base module to be used by all domain test modules"""

import os

from bootstrap import bootstrap_testsuite

hostname = os.environ.get('STOQLIB_TEST_HOSTNAME')
dbname =  os.environ.get('STOQLIB_TEST_DBNAME')
username = os.environ.get('STOQLIB_TEST_USERNAME')
password = os.environ.get('STOQLIB_TEST_PASSWORD')
port = int(os.environ.get('STOQLIB_TEST_PORT') or 0)
quick = os.environ.get('STOQLIB_TEST_QUICK', None) is not None

config = os.path.join(os.path.dirname(__file__), 'config.py')
if os.path.exists(config):
    execfile(config, globals(), locals())

bootstrap_testsuite(address=hostname,
                    dbname=dbname,
                    port=port,
                    username=username,
                    password=password,
                    quick=quick)
