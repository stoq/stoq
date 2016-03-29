# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import gtk

from stoqlib.api import api
from stoqlib.domain.product import Product
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import BaseWizard, BaseWizardStep
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.slaves.productslave import ProductAttributeSlave
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.translation import stoqlib_gettext as _


class ProductTypeStep(BaseWizardStep):
    gladefile = 'ProductTypeStep'

    #
    #  WizardEditorStep
    #

    def next_step(self):
        if self.wizard.product_type == Product.TYPE_GRID:
            return ProductAttributeEditorStep(self.wizard.store, self.wizard, previous=self)
        else:
            return ProductEditorStep(store=self.wizard.store, wizard=self.wizard, previous=self)

    #
    #  Callbacks
    #

    def on_common__toggled(self, radio):
        if radio.get_active():
            self.wizard.product_type = Product.TYPE_COMMON

    def on_batch__toggled(self, radio):
        if radio.get_active():
            self.wizard.product_type = Product.TYPE_BATCH

    def on_without_stock__toggled(self, radio):
        if radio.get_active():
            self.wizard.product_type = Product.TYPE_WITHOUT_STOCK

    def on_consigned__toggled(self, radio):
        if radio.get_active():
            self.wizard.product_type = Product.TYPE_CONSIGNED

    def on_grid__toggled(self, radio):
        if radio.get_active():
            self.wizard.product_type = Product.TYPE_GRID

    def on_package__toggled(self, radio):
        if radio.get_active():
            self.wizard.product_type = Product.TYPE_PACKAGE


class ProductAttributeEditorStep(BaseWizardStep):
    gladefile = 'HolderTemplate'

    def __init__(self, store, wizard, previous):
        BaseWizardStep.__init__(self, store, wizard, previous)

        self.slave = ProductAttributeSlave(self.wizard.store, object())
        self.attach_slave('product_attribute_holder', self.slave, self.place_holder)

    def validate_step(self):
        if len(self.slave.get_selected_attributes()) == 0:
            warning(_("You should select an attribute first"))
            return False
        return True

    def next_step(self):
        self.wizard.attr_list = self.slave.get_selected_attributes()
        return ProductEditorStep(self.wizard.store, self.wizard, previous=self)


class ProductEditorStep(BaseWizardStep):
    gladefile = 'HolderTemplate'

    #
    #  BaseWizardStep
    #

    def post_init(self):
        # self.wizard.model will return something if it is coming back from
        self.slave = ProductEditor(self.store, wizard=self.wizard,
                                   product_type=self.wizard.product_type)
        self.slave.get_toplevel().reparent(self.place_holder)
        self.wizard.model = self.slave.model

        self.slave.register_validate_function(self.wizard.refresh_next)
        self.slave.force_validation()

    def previous_step(self):
        # Avoid creating duplicated products when going back
        self.store.rollback(close=False)

        return super(ProductEditorStep, self).previous_step()

    def has_next_step(self):
        return False


class ProductCreateWizard(BaseWizard):
    size = (800, 450)
    title = _('Product creation wizard')
    help_section = 'product-new'
    need_cancel_confirmation = True

    # args and kwargs are here to get extra parameters sent by SearchEditor's
    # run_dialog. We will just ignore them since they are not useful here
    def __init__(self, store, *args, **kwargs):
        self.product_type = Product.TYPE_COMMON
        first_step = ProductTypeStep(store, self)
        BaseWizard.__init__(self, store, first_step)

    #
    #  BaseWizard
    #

    def finish(self):
        last_step = self.get_current_step()
        # Forcing the wizard to confirm all slaves
        if not last_step.slave.confirm():
            return
        self.retval = self.model
        self.close()
        self.model.update_children_info()

    def cancel(self):
        last_step = self.get_current_step()
        if isinstance(last_step, ProductEditorStep):
            last_step.slave.cancel()

        return super(ProductCreateWizard, self).cancel()

    #
    #  Classmethods
    #

    @classmethod
    def run_wizard(cls, parent):
        """Run the wizard to create a product

        This will run the wizard and after finishing, ask if the user
        wants to create another product alike. The product will be
        cloned and `stoqlib.gui.editors.producteditor.ProductEditor`
        will run as long as the user chooses to create one alike
        """
        with api.new_store() as store:
            rv = run_dialog(cls, parent, store)

        if rv:
            inner_rv = rv

            while yesno(_("Would you like to register another product alike?"),
                        gtk.RESPONSE_NO, _("Yes"), _("No")):
                with api.new_store() as store:
                    template = store.fetch(rv)
                    inner_rv = run_dialog(ProductEditor, parent, store,
                                          product_type=template.product_type,
                                          template=template)

                if not inner_rv:
                    break

        # We are insterested in the first rv that means that at least one
        # obj was created.
        return rv
