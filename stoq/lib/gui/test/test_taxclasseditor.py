# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2017 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#  Author(s): Stoq Team <stoq-devel@async.com.br>
#
#

import datetime

from stoqlib.domain.taxes import ProductTaxTemplate
from stoq.lib.gui.editors.taxclasseditor import ProductTaxTemplateEditor
from stoq.lib.gui.test.uitestutils import GUITest


class TestProductTaxTemplateEditor(GUITest):
    def test_create(self):
        editor = ProductTaxTemplateEditor(self.store, None)
        self.assertEquals(editor.model.tax_type, ProductTaxTemplate.TYPE_ICMS)

    def test_update_csosn(self):
        # Creating a new tax
        editor = ProductTaxTemplateEditor(self.store, None)
        slave = editor.get_slave('tax_template_holder')
        # Setting some values
        # CSOSN 202
        slave.csosn.select_item_by_position(5)
        # Orig 0
        slave.orig.select_item_by_position(1)
        slave.p_icms_st.update(3)
        slave.p_red_bc_st.update(3)

        # Changing the CSOSN 500
        slave.csosn.select_item_by_position(8)
        self.assertEquals(slave.p_icms_st.read(), 0)
        self.assertEquals(slave.p_red_bc_st.read(), 0)

        # CSOSN 201
        slave.csosn.select_item_by_position(4)
        slave.p_cred_sn.update(4)
        slave.p_cred_sn_valid_until.update(datetime.date(2099, 12, 30))

        # Updating CSOSN to 202
        slave.csosn.select_item_by_position(5)
        self.assertEquals(slave.p_cred_sn.read(), 0)
        self.assertEquals(slave.p_cred_sn_valid_until.read(), None)

    def test_mot_des_icms_with_invalid_csts(self):
        editor = ProductTaxTemplateEditor(self.store, None)
        slave = editor.get_slave('tax_template_holder')

        invalid_csts = [0, 10, 60]

        for cst in invalid_csts:
            slave.cst.update(cst)
            self.assertFalse(slave.mot_des_icms.get_sensitive())

    def test_mot_des_icms(self):
        editor = ProductTaxTemplateEditor(self.store, None)
        slave = editor.get_slave('tax_template_holder')

        csts = [20, 30, 40, 41, 50, 70, 90]

        for cst in csts:
            slave.cst.update(cst)
            self.assertTrue(slave.mot_des_icms.get_sensitive())
