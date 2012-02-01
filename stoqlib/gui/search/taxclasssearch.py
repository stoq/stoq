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
""" A dialog for sellable categories selection, offering buttons for
creation and edition.
"""

from kiwi.ui.objectlist import SearchColumn, Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.taxes import ProductTaxTemplate
from stoqlib.gui.slaves.taxslave import ICMSTemplateSlave, IPITemplateSlave

_ = stoqlib_gettext

TYPE_SLAVES = {
    ProductTaxTemplate.TYPE_ICMS: ICMSTemplateSlave,
    ProductTaxTemplate.TYPE_IPI: IPITemplateSlave,
}


class ProductTaxTemplateEditor(BaseEditor):
    gladefile = 'ProductTaxTemplateEditor'
    model_type = ProductTaxTemplate
    model_name = _('Base Category')
    proxy_widgets = ('name', 'tax_type')
    size = (-1, -1)
    help_section = 'tax-class'

    def __init__(self, conn, model):
        self.slave_model = None
        self.edit_mode = bool(model)
        if model:
            self.slave_model = model.get_tax_model()

        BaseEditor.__init__(self, conn, model)

    def create_model(self, conn):
        model = ProductTaxTemplate(name=u"",
                                   tax_type=ProductTaxTemplate.TYPE_ICMS,
                                   connection=conn)
        self._create_slave_model(model)
        return model

    def _create_slave_model(self, model):
        self.slave_model = ProductTaxTemplate.type_map[model.tax_type](
                                        product_tax_template=model,
                                        connection=self.conn)

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
            self.slave_model.delete(self.slave_model.id, self.conn)
            self._create_slave_model(self.model)

        # Attach new slave.
        slave_class = TYPE_SLAVES[self.model.tax_type]
        slave = slave_class(self.conn, self.slave_model)
        self.attach_slave('tax_template_holder', slave)

    def on_tax_type__changed(self, widget):
        self._change_slave()


class TaxTemplatesSearch(SearchEditor):
    size = (500, 350)
    title = _('Tax Classes Search')

    searchbar_label = _('Class Matching:')
    result_strings = _('class'), _('classes')
    table = search_table = ProductTaxTemplate
    editor = ProductTaxTemplateEditor

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, self.table, self.editor)
        self.set_searchbar_labels(self.searchbar_label)
        self.set_result_strings(*self.result_strings)

    def create_filters(self):
        self.set_text_field_columns(['name'])
        self.executer.add_query_callback(self._get_query)

    def get_columns(self):
        return [
            SearchColumn("name", _("Class name"), data_type=str,
                         sorted=True, expand=True),
            Column("tax_type_str", _("Type"), data_type=str, width=80),
            ]

    def get_editor_model(self, view_item):
        return view_item

    #
    # Private
    #

    def _get_query(self, states):
        #return SellableCategory.q.categoryID != None
        return None
