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


from stoqlib.domain.sale import Delivery
from stoq.lib.gui.editors.deliveryeditor import DeliveryEditor, CreateDeliveryEditor
from stoq.lib.gui.test.uitestutils import GUITest


class TestDeliveryEditor(GUITest):
    def _create_delivery(self):
        client = self.create_client()
        delivery = self.create_delivery()
        delivery.transporter = self.create_transporter()

        sale = self.create_sale(client=client)
        self.add_product(sale)
        self.add_product(sale)
        delivery.invoice = sale.invoice

        for i, item in enumerate(sale.get_items()):
            item.sellable.description = u"Delivery item %d" % (i + 1)
            delivery.add_item(item)

        return delivery

    def test_show(self):
        delivery = self._create_delivery()
        editor = DeliveryEditor(self.store, delivery)
        self.check_editor(editor, 'editor-delivery-show')

    def test_state_changing(self):
        delivery = self._create_delivery()
        editor = DeliveryEditor(self.store, delivery)

        # Initial state. Should be possible to change the
        # transporter and address
        self.assertEqual(delivery.status, Delivery.STATUS_INITIAL)
        self.assertSensitive(editor,
                             ['transporter_id', 'address',
                              'is_received_check', 'is_sent_check'])
        self.assertNotSensitive(editor,
                                ['send_date', 'tracking_code',
                                 'receive_date'])
        self.assertFalse(editor.is_sent_check.get_active())
        self.assertFalse(editor.is_received_check.get_active())

        # Sent state. Should not be possible to change
        # transporter and address anymore
        editor.is_sent_check.set_active(True)
        self.assertEqual(delivery.status, Delivery.STATUS_SENT)
        self.assertSensitive(editor,
                             ['is_received_check', 'send_date', 'tracking_code',
                              'is_received_check', 'is_sent_check'])
        self.assertNotSensitive(editor,
                                ['transporter_id', 'address', 'receive_date'])

        # Received state. Like sent above, but in addition, should
        # not be possible to unmark is_sent_check
        editor.is_received_check.set_active(True)
        self.assertEqual(delivery.status, Delivery.STATUS_RECEIVED)
        self.assertSensitive(editor,
                             ['is_received_check', 'send_date',
                              'receive_date', 'tracking_code',
                              'is_received_check'])
        self.assertNotSensitive(editor,
                                ['transporter_id', 'address',
                                 'is_sent_check'])


class TestCreateDeliveryEditor(GUITest):
    def _create_sale_items(self):
        sale = self.create_sale()
        sale_items = []
        for i in range(5):
            sale_item = self.create_sale_item(sale=sale)
            sale_item.sellable.description = u"Delivery item %s" % (i + 1)
            sale_items.append(sale_item)
        return sale_items

    def test_create_recipient_client(self):
        sale_items = self._create_sale_items()
        editor = CreateDeliveryEditor(self.store, items=sale_items)
        self.check_editor(editor, 'editor-createdelivery-create')

    def test_on_client_changed(self):
        client1 = self.create_client(name=u"Client01")
        address1 = self.create_address(person=client1.person)
        client2 = self.create_client(name=u"Client02")
        addres2 = self.create_address(person=client2.person)
        addres2.street = u"Mainstreet02"
        sale_items = self._create_sale_items()
        editor = CreateDeliveryEditor(self.store, items=sale_items)

        # No client
        self.assertIsNone(editor.recipient.read())
        no_address = editor.address.get_selected_data()
        self.assertEqual(no_address, None)
        self.check_editor(editor, 'editor-createdelivery-noclient')

        # Select a client
        editor.fields['recipient'].set_value(client1)
        first_client = editor.recipient.read()
        self.assertEqual(first_client, client1)
        first_address = editor.address.get_selected_data()
        self.assertEqual(first_address, address1)
        self.check_editor(editor, 'editor-createdelivery-client')

        # Change client
        editor.fields['recipient'].set_value(client2)
        new_client = editor.recipient.read()
        self.assertNotEqual(first_client, new_client)
        new_address = editor.address.get_selected_data()
        self.assertNotEqual(first_address, new_address)
        self.check_editor(editor, 'editor-createdelivery-clientchanged')

    def test_vehicle_plate_validation(self):
        sale_items = self._create_sale_items()
        editor = CreateDeliveryEditor(self.store, items=sale_items)

        # Invalid cases
        # String with less than 6 characters
        editor.vehicle_license_plate.set_text('FOO21')
        self.assertInvalid(editor, ['vehicle_license_plate'])

        # String with more than 7 characters
        editor.vehicle_license_plate.set_text('FOO20000')
        self.assertInvalid(editor, ['vehicle_license_plate'])

        # String starting with number
        editor.vehicle_license_plate.set_text('2FOO20')
        self.assertInvalid(editor, ['vehicle_license_plate'])

        # String ending with a non-number
        editor.vehicle_license_plate.set_text('FOO200r')
        self.assertInvalid(editor, ['vehicle_license_plate'])

        # Valid cases
        # Uppercase
        editor.vehicle_license_plate.set_text('FOO201')
        self.assertValid(editor, ['vehicle_license_plate'])

        # Lowcase
        editor.vehicle_license_plate.set_text('foo201')
        self.assertValid(editor, ['vehicle_license_plate'])

        # Mixed Uppercase anda lowcase
        editor.vehicle_license_plate.set_text('Foo201')
        self.assertValid(editor, ['vehicle_license_plate'])

        # 2 a-zA-Z characters followed by 4 numeric characters
        editor.vehicle_license_plate.set_text('Fo2018')
        self.assertValid(editor, ['vehicle_license_plate'])

        # 4 a-zA-Z characters followed by 3 numeric characters
        editor.vehicle_license_plate.set_text('Fooo201')
        self.assertValid(editor, ['vehicle_license_plate'])

        editor.vehicle_license_plate.set_text('FOO201')
        self.assertValid(editor, ['vehicle_license_plate'])
