# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.taxes import ProductTaxTemplate
from stoqlib.gui.slaves.taxslave import (COFINSTemplateSlave, ICMSTemplateSlave,
                                         IPITemplateSlave, PISTemplateSlave)

_ = stoqlib_gettext

TYPE_SLAVES = {
    ProductTaxTemplate.TYPE_COFINS: COFINSTemplateSlave,
    ProductTaxTemplate.TYPE_ICMS: ICMSTemplateSlave,
    ProductTaxTemplate.TYPE_IPI: IPITemplateSlave,
    ProductTaxTemplate.TYPE_PIS: PISTemplateSlave,
}


class ProductTaxTemplateEditor(BaseEditor):
    gladefile = 'ProductTaxTemplateEditor'
    model_type = ProductTaxTemplate
    model_name = _('Base Category')
    proxy_widgets = ('name', 'tax_type')
    size = (-1, -1)
    help_section = 'tax-class'

    def __init__(self, store, model, visual_mode=False):
        self.slave_model = None
        self.edit_mode = bool(model)
        if model:
            self.slave_model = model.get_tax_model()

        BaseEditor.__init__(self, store, model, visual_mode)

    def create_model(self, store):
        model = ProductTaxTemplate(name=u"",
                                   tax_type=ProductTaxTemplate.TYPE_ICMS,
                                   store=store)
        self._create_slave_model(model)
        return model

    def _create_slave_model(self, model):
        self.slave_model = ProductTaxTemplate.type_map[model.tax_type](
            product_tax_template=model,
            store=self.store)

    def setup_combo(self):
        self.tax_type.prefill([(key, value)
                               for value, key in ProductTaxTemplate.types.items()])

    def setup_proxies(self):
        self.setup_combo()
        if self.edit_mode:
            self.tax_type.set_sensitive(False)
        self.add_proxy(model=self.model, widgets=self.proxy_widgets)

    def _change_slave(self):
        # Remove old slave
        if self.get_slave('tax_template_holder'):
            self.detach_slave('tax_template_holder')

        # When creating a new template, after changing the class, we need to
        # delete the old object. When editing, we cant delete, since the
        # user cant change the class.
        if not self.edit_mode:
            self.slave_model.delete(self.slave_model.id, self.store)
            self._create_slave_model(self.model)

        # Attach new slave.
        slave_class = TYPE_SLAVES[self.model.tax_type]
        slave = slave_class(self.store, self.slave_model, self.visual_mode)
        self.attach_slave('tax_template_holder', slave)

    def on_tax_type__changed(self, widget):
        self._change_slave()
