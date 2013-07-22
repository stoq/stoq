# -*- coding: utf-8 -*-
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

__tests__ = 'stoqlib/domain/image.py'

from stoqlib.domain.image import Image
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.events import (ImageCreateEvent, ImageEditEvent)


class TestImage(DomainTest):

    _call_count = 0

    def test_base64Encode(self):
        image = self.create_image()
        image.image = 'teste'

        # the second argument is the string 'teste' with base64 encoding
        self.assertEquals(image.get_base64_encoded(), 'dGVzdGU=')

    def test_get_description(self):
        image = self.create_image()
        image.description = u'Test test'

        self.assertEqual(image.get_description(), u'Test test')
        image.description = None

        self.assertEqual(image.get_description(), u'Stoq image')

    def test_delete(self):
        image = self.create_image()

        total = self.store.find(Image, id=image.id).count()
        self.assertEquals(total, 1)

        image.delete(image.id, self.store)

        total = self.store.find(Image, id=image.id).count()
        self.assertEquals(total, 0)

    def test_on_create(self):
        self._call_count = 0

        def _call_back(image):
            self._call_count += 1

        ImageCreateEvent.connect(_call_back)
        image = self.create_image()
        image.on_create()
        self.assertNotEquals(self._call_count, 0)

    def test_on_update(self):
        self._call_count = 0

        ImageEditEvent.connect(self._call_count_function)
        image = self.create_image()
        image.on_update()

        self.assertEquals(self._call_count, 1)

    def _call_count_function(self, image):
        self._call_count += 1
