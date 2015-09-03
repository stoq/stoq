# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
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

import mock

from stoqlib.domain.taxes import (ProductIcmsTemplate,
                                  ProductIpiTemplate,
                                  ProductTaxTemplate)
from stoqlib.gui.editors.transfereditor import TransferItemEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestTransferItemEditor(GUITest):
    def test_show_item_editor(self):
        sellable = self.create_sellable()
        sellable.cost = 100
        transfer_item = self.create_transfer_order_item(sellable=sellable,
                                                        quantity=10,
                                                        stock_cost=150)
        editor = TransferItemEditor(self.store, transfer_item)
        self.check_editor(editor, 'editor-transfer-item-edit')

        with mock.patch('stoqlib.lib.pluginmanager.PluginManager.is_active') as patch:
            patch.return_value = True
            editor = TransferItemEditor(self.store, transfer_item)
            self.check_editor(editor, 'editor-transfer-item-with-nfe')


class TestTransferItemSlave(GUITest):
    def test_show(self):
        sellable = self.create_sellable()
        sellable.cost = 100
        transfer_item = self.create_transfer_order_item(sellable=sellable,
                                                        quantity=10,
                                                        stock_cost=150)
        editor = TransferItemEditor(self.store, transfer_item)
        slave = editor.item_slave
        self.assertEquals(slave.original_cost.read(), 100)
        self.assertEquals(slave.stock_cost.read(), 150)
        self.assertEquals(slave.quantity.get_value(), 10)
        self.check_slave(slave, 'slave-transfer-item-show')

    def test_on_quantity__validate(self):
        transfer_item = self.create_transfer_order_item(quantity=10)
        editor = TransferItemEditor(self.store, transfer_item)
        slave = editor.item_slave
        self.assertEquals(slave.quantity.get_value(), 10)
        slave.quantity.update(0)
        self.assertInvalid(slave, ['quantity'])
        slave.quantity.update(1)
        self.assertValid(slave, ['quantity'])

    def test_on_stock_cost__validate(self):
        transfer_item = self.create_transfer_order_item(stock_cost=150)
        editor = TransferItemEditor(self.store, transfer_item)
        slave = editor.item_slave
        self.assertEquals(slave.stock_cost.get_value(), 150)
        slave.stock_cost.update(0)
        self.assertInvalid(slave, ['stock_cost'])
        slave.stock_cost.update(100)
        self.assertValid(slave, ['stock_cost'])

    def test_update_taxes(self):
        tax_template = ProductTaxTemplate(store=self.store,
                                          tax_type=ProductTaxTemplate.TYPE_ICMS)
        icms_template = ProductIcmsTemplate(store=self.store,
                                            product_tax_template=tax_template)
        icms_template.csosn = 201

        tax_template = ProductTaxTemplate(store=self.store,
                                          tax_type=ProductTaxTemplate.TYPE_IPI)
        ipi_template = ProductIpiTemplate(store=self.store,
                                          product_tax_template=tax_template)
        ipi_template.cst = 00

        tax_template = self.create_product_tax_template(tax_type=ProductTaxTemplate.TYPE_PIS)
        pis_template = self.create_product_pis_template(cst=49)
        self.assertEquals(pis_template.cst, 49)

        tax_template = self.create_product_tax_template(tax_type=ProductTaxTemplate.TYPE_COFINS)
        cofins_template = self.create_product_cofins_template(cst=49)
        self.assertEquals(cofins_template.cst, 49)

        product = self.create_product()
        product.icms_template = icms_template
        product.ipi_template = ipi_template
        product.pis_template = pis_template
        product.cofins_template = cofins_template
        transfer_item = self.create_transfer_order_item(sellable=product.sellable,
                                                        stock_cost=100,
                                                        quantity=1)
        with mock.patch('stoqlib.lib.pluginmanager.PluginManager.is_active') as patch:
            patch.return_value = True
            editor = TransferItemEditor(self.store, transfer_item)
            slave = editor.item_slave
            icms_slave = editor.icms_slave
            ipi_slave = editor.ipi_slave
            self.assertEquals(icms_slave.v_bc_st.read(), 100)
            self.assertEquals(ipi_slave.v_bc.read(), 100)
            slave.stock_cost.update(150)
            self.assertEquals(icms_slave.v_bc_st.read(), 150)
            self.assertEquals(ipi_slave.v_bc.read(), 150)
            slave.quantity.update(2)
            self.assertEquals(icms_slave.v_bc_st.read(), 300)
            self.assertEquals(ipi_slave.v_bc.read(), 300)
