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

from stoqlib.gui.dialogs.addressdialog import AddressAdditionDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestAddressAdditionDialog(GUITest):
    def test_show(self):
        p = self.create_person()
        for city, state, country, main in [
                (u'São Carlos', u'SP', u'Brazil', True),
                (u'Ribeirão Preto', u'SP', u'Brazil', False),
                (u'Patos de Minas', u'MG', u'Brazil', False)]:
            cl = self.create_city_location(city=city, state=state, country=country)
            address = self.create_address(person=p, city_location=cl)
            address.is_main_address = main

        dialog = AddressAdditionDialog(self.store, person=p)
        self.check_dialog(dialog, 'dialog-address-addition')
