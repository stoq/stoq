# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.utils import get_logo_data


class TestUtils(DomainTest):
    def test_get_logo_data(self):
        image = self.create_image()
        image.image = 'foobar'
        sysparam().set_object(self.store,
                              'CUSTOM_LOGO_FOR_REPORTS',
                              image)
        data = get_logo_data(self.store)
        self.assertEquals(data, 'data:image/png;base64,Zm9vYmFy')
