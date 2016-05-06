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

from stoqlib.domain.production import ProductionOrder
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.productionwizard import (OpenProductionOrderStep,
                                                  ProductionServiceStep,
                                                  ProductionItemStep,
                                                  FinishOpenProductionOrderStep,
                                                  ProductionWizard)


class TestProductionWizard(GUITest):
    def test_production_no_service(self):
        product_component = self.create_product_component()
        wizard = ProductionWizard(store=self.store)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, OpenProductionOrderStep))
        self.assertNotSensitive(wizard, ['next_button'])
        step.description.update('Testing production wizard.')
        step.identifier.update('9876')
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-production-no-service-open-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, ProductionServiceStep))
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-production-no-service-service-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, ProductionItemStep))
        self.assertNotSensitive(wizard, ['next_button'])
        step.barcode.set_text(product_component.product.sellable.barcode)
        step.sellable_selected(product_component.product.sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-production-no-service-item-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, FinishOpenProductionOrderStep))
        self.assertSensitive(wizard, ['next_button'])

        models = [wizard.model, product_component, product_component.product,
                  product_component.component]
        models.extend(wizard.model.get_items())
        models.extend(wizard.model.get_material_items())

        self.check_wizard(wizard, 'wizard-production-no-service-finish-step',
                          models=models)
        self.click(wizard.next_button)
        # Tests if wizard really created object in database when finish button
        # was clicked.
        self.assertEquals(wizard.model,
                          self.store.find(ProductionOrder,
                                          id=wizard.model.id).one())

    def test_production_with_service(self):
        service = self.create_service()
        service.sellable.barcode = u'66'
        product_component = self.create_product_component()
        wizard = ProductionWizard(store=self.store)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, OpenProductionOrderStep))
        self.assertNotSensitive(wizard, ['next_button'])
        step.description.update('Testing production wizard.')
        step.identifier.update('9876')
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-production-with-service-open-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, ProductionServiceStep))
        self.assertSensitive(wizard, ['next_button'])
        step.barcode.set_text(service.sellable.barcode)
        step.sellable_selected(service.sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-production-with-service-service-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, ProductionItemStep))
        self.assertNotSensitive(wizard, ['next_button'])
        step.barcode.set_text(product_component.product.sellable.barcode)
        step.sellable_selected(product_component.product.sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-production-with-service-item-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, FinishOpenProductionOrderStep))
        self.assertSensitive(wizard, ['next_button'])

        models = [wizard.model, service, product_component,
                  product_component.product, product_component.component]
        models.extend(wizard.model.get_items())
        models.extend(wizard.model.get_service_items())
        models.extend(wizard.model.get_material_items())

        self.check_wizard(wizard, 'wizard-production-with-service-finish-step',
                          models=models)
        self.click(wizard.next_button)

        # Tests if wizard really created object in database when finish button
        # was clicked.
        self.assertEquals(wizard.model,
                          self.store.find(ProductionOrder,
                                          id=wizard.model.id).one())
