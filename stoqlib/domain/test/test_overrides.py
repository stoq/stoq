# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#

__tests__ = 'stoqlib/domain/overrides.py'

from stoqlib.domain.overrides import ProductBranchOverride
from stoqlib.domain.test.domaintest import DomainTest


class TestProductOverride(DomainTest):

    def test_overide_icms(self):
        product = self.create_product()
        product.set_icms_template(self.create_product_icms_template(crt=3, code=3))

        # Default value should be the one created above
        self.assertEqual(product.get_icms_template(self.current_branch).cst, 3)

        # Now create an override
        override = ProductBranchOverride(store=self.store, product=product,
                                         branch=self.current_branch)

        # The override object does not define an icms template
        self.assertEqual(product.get_icms_template(self.current_branch).cst, 3)

        # Setting a template on the override should take effect
        override.icms_template = self.create_product_icms_template(crt=3, code=6)
        self.assertEqual(product.get_icms_template(self.current_branch).cst, 6)

    def test_overide_ipi(self):
        product = self.create_product()
        product.set_ipi_template(self.create_product_ipi_template(cst=3))

        # Default value should be the one created above
        self.assertEqual(product.get_ipi_template(self.current_branch).cst, 3)

        # Now create an override
        override = ProductBranchOverride(store=self.store, product=product,
                                         branch=self.current_branch)

        # The override object does not define an ipi template
        self.assertEqual(product.get_ipi_template(self.current_branch).cst, 3)

        # Setting a template on the override should take effect
        override.ipi_template = self.create_product_ipi_template(cst=6)
        self.assertEqual(product.get_ipi_template(self.current_branch).cst, 6)

    def test_overide_pis(self):
        product = self.create_product()
        product.set_pis_template(self.create_product_pis_template(cst=3))

        # Default value should be the one created above
        self.assertEqual(product.get_pis_template(self.current_branch).cst, 3)

        # Now create an override
        override = ProductBranchOverride(store=self.store, product=product,
                                         branch=self.current_branch)

        # The override object does not define an pis template
        self.assertEqual(product.get_pis_template(self.current_branch).cst, 3)

        # Setting a template on the override should take effect
        override.pis_template = self.create_product_pis_template(cst=6)
        self.assertEqual(product.get_pis_template(self.current_branch).cst, 6)

    def test_overide_cofins(self):
        product = self.create_product()
        product.set_cofins_template(self.create_product_cofins_template(cst=3))

        # Default value should be the one created above
        self.assertEqual(product.get_cofins_template(self.current_branch).cst, 3)

        # Now create an override
        override = ProductBranchOverride(store=self.store, product=product,
                                         branch=self.current_branch)

        # The override object does not define an cofins template
        self.assertEqual(product.get_cofins_template(self.current_branch).cst, 3)

        # Setting a template on the override should take effect
        override.cofins_template = self.create_product_cofins_template(cst=6)
        self.assertEqual(product.get_cofins_template(self.current_branch).cst, 6)

    def test_c_benef(self):
        product = self.create_product()
        override = ProductBranchOverride(store=self.store, product=product,
                                         branch=self.current_branch)
        override.c_benef = 'RJ111111'
        self.assertEqual(override.c_benef, 'RJ111111')
