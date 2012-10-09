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
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.editors.deliveryeditor import (DeliveryEditor,
                                                CreateDeliveryEditor)


class TestDeliveryEditor(GUITest):
    def _create_delivery(self):
        client = self.create_client()
        delivery = self.create_delivery()
        delivery.transporter = self.create_transporter()

        sale = self.create_sale(client=client)
        self.add_product(sale)
        self.add_product(sale)

        for i, item in enumerate(sale.get_items()):
            item.sellable.description = "Delivery item %d" % (i + 1)
            delivery.add_item(item)

        return delivery

    def testShow(self):
        delivery = self._create_delivery()
        editor = DeliveryEditor(self.trans, delivery)
        self.check_editor(editor, 'editor-delivery-show')

    def testStateChanging(self):
        delivery = self._create_delivery()
        editor = DeliveryEditor(self.trans, delivery)

        # Initial state. Should be possible to change the
        # transporter and address
        self.assertEqual(delivery.status, Delivery.STATUS_INITIAL)
        self.assertSensitive(editor,
                             ['transporter', 'address',
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
                                ['transporter', 'address', 'receive_date'])

        # Received state. Like sent above, but in addition, should
        # not be possible to unmark was_delivered_check
        editor.was_received_check.set_active(True)
        self.assertEqual(delivery.status, Delivery.STATUS_RECEIVED)
        self.assertSensitive(editor,
                             ['was_received_check', 'deliver_date',
                              'receive_date', 'tracking_code',
                              'was_received_check'])
        self.assertNotSensitive(editor,
                                ['transporter', 'address',
                                 'was_delivered_check'])


class TestCreateDeliveryEditor(GUITest):
    def testCreate(self):
        sale = self.create_sale()
        sale_items = []
        for i in range(5):
            sale_item = self.create_sale_item(sale=sale)
            sale_item.sellable.description = "Delivery item %s" % (i + 1)
            sale_items.append(sale_item)

        editor = CreateDeliveryEditor(self.trans, sale_items=sale_items)
        self.check_editor(editor, 'editor-createdelivery-create')
