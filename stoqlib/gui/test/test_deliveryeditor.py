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
from stoqlib.gui.editors.deliveryeditor import (DeliveryEditor,
                                                CreateDeliveryEditor)
from stoqlib.gui.test.uitestutils import GUITest


class TestDeliveryEditor(GUITest):
    def _create_delivery(self):
        client = self.create_client()
        delivery = self.create_delivery()
        delivery.transporter = self.create_transporter()

        sale = self.create_sale(client=client)
        self.add_product(sale)
        self.add_product(sale)

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
                              'was_received_check', 'was_delivered_check'])
        self.assertNotSensitive(editor,
                                ['deliver_date', 'tracking_code',
                                 'receive_date'])
        self.assertFalse(editor.was_delivered_check.get_active())
        self.assertFalse(editor.was_received_check.get_active())

        # Sent state. Should not be possible to change
        # transporter and address anymore
        editor.was_delivered_check.set_active(True)
        self.assertEqual(delivery.status, Delivery.STATUS_SENT)
        self.assertSensitive(editor,
                             ['was_received_check', 'deliver_date', 'tracking_code',
                              'was_received_check', 'was_delivered_check'])
        self.assertNotSensitive(editor,
                                ['transporter_id', 'address', 'receive_date'])

        # Received state. Like sent above, but in addition, should
        # not be possible to unmark was_delivered_check
        editor.was_received_check.set_active(True)
        self.assertEqual(delivery.status, Delivery.STATUS_RECEIVED)
        self.assertSensitive(editor,
                             ['was_received_check', 'deliver_date',
                              'receive_date', 'tracking_code',
                              'was_received_check'])
        self.assertNotSensitive(editor,
                                ['transporter_id', 'address',
                                 'was_delivered_check'])


class TestCreateDeliveryEditor(GUITest):
    def _create_sale_items(self):
        sale = self.create_sale()
        sale_items = []
        for i in range(5):
            sale_item = self.create_sale_item(sale=sale)
            sale_item.sellable.description = u"Delivery item %s" % (i + 1)
            sale_items.append(sale_item)
        return sale_items

    def test_create(self):
        sale_items = self._create_sale_items()
        editor = CreateDeliveryEditor(self.store, sale_items=sale_items)
        self.check_editor(editor, 'editor-createdelivery-create')

    def test_on_client_changed(self):
        client1 = self.create_client(name=u"Client01")
        address1 = self.create_address(person=client1.person)
        client2 = self.create_client(name=u"Client02")
        addres2 = self.create_address(person=client2.person)
        addres2.street = u"Mainstreet02"
        sale_items = self._create_sale_items()
        editor = CreateDeliveryEditor(self.store, sale_items=sale_items)

        # No client
        no_client = editor.client_id.get_selected_data()
        self.assertEqual(no_client, None)
        no_address = editor.address.get_selected_data()
        self.assertEqual(no_address, None)
        self.check_editor(editor, 'editor-createdelivery-noclient')

        # Select a client
        editor.client_id.select(client1.id)
        first_client = editor.client_id.get_selected_data()
        self.assertEqual(first_client, client1.id)
        first_address = editor.address.get_selected_data()
        self.assertEqual(first_address, address1)
        self.check_editor(editor, 'editor-createdelivery-client')

        # Change client
        editor.client_id.select(client2.id)
        new_client = editor.client_id.get_selected_data()
        self.assertNotEquals(first_client, new_client)
        new_address = editor.address.get_selected_data()
        self.assertNotEquals(first_address, new_address)
        self.check_editor(editor, 'editor-createdelivery-clientchanged')
