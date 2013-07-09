# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import unittest

import gtk
import mock

from stoqlib.domain.address import Address, CityLocation
from stoqlib.gui.editors.addresseditor import AddressEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestAddressEditor(GUITest):
    def test_create(self):
        person = self.create_person()
        editor = AddressEditor(self.store, person)

        self.assertTrue(isinstance(editor.model, Address))

        self.check_editor(editor, 'editor-address-create')

    def test_show(self):
        person = self.create_person()
        address = self.create_address()
        address.person = person
        editor = AddressEditor(self.store, person, address)

        self.check_editor(editor, 'editor-address-show')

    @mock.patch('stoqlib.gui.slaves.addressslave.info')
    def test_confirm(self, info):
        city_location = CityLocation.get_or_create(
            self.store, u"São Carlos", u"SP", u"Brazil")
        person = self.create_person()
        address = self.create_address(person=person,
                                      city_location=city_location)
        editor = AddressEditor(self.store, person, address)
        address_slave = editor.address_slave
        self.assertSensitive(editor.main_dialog, ['ok_button'])
        valid_city = address_slave.city.read()

        # Trying to confirm the editor without leaving the entry.
        # Can be reproduced by pressing ALT+O
        address_slave.city.grab_focus()
        address_slave.city.update("INVALID CITY")
        self.assertValid(address_slave, ['city'])
        self.assertSensitive(editor.main_dialog, ['ok_button'])
        self.assertFalse(editor.confirm())
        self.assertInvalid(address_slave, ['city'])
        info.assert_called_once_with("The city is not valid")

        # When city looses focus, validation should be done
        address_slave.city.update(valid_city)
        self.assertSensitive(editor.main_dialog, ['ok_button'])
        address_slave.city.grab_focus()
        address_slave.city.update("INVALID CITY")
        # FIXME: For some reason, this only works here when grabbing the focus
        # on another widget and emitting the focus-out event. On the real
        # editor, pressing TAB or even trying to click on Ok is enough
        address_slave.state.grab_focus()
        address_slave.city.emit('focus-out-event',
                                gtk.gdk.Event(gtk.gdk.FOCUS_CHANGE))
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        self.assertInvalid(address_slave, ['city'])

        address_slave.city.update(valid_city)
        self.assertValid(address_slave, ['city'])
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        path = 'stoqlib.domain.address.CityLocation.is_valid_model'
        with mock.patch(path) as is_valid_model:
            is_valid_model.return_value = False
            self.assertFalse(editor.validate_confirm())
            self.assertFalse(editor.confirm())

        self.assertTrue(editor.validate_confirm())
        self.assertTrue(editor.confirm())


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
