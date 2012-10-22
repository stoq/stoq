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
from stoqlib.domain.taxes import ProductTaxTemplate
from stoqlib.gui.slaves.taxslave import ICMSTemplateSlave, IPITemplateSlave
from stoqlib.gui.editors.taxclasseditor import ProductTaxTemplateEditor

_ = stoqlib_gettext

TYPE_SLAVES = {
    ProductTaxTemplate.TYPE_ICMS: ICMSTemplateSlave,
    ProductTaxTemplate.TYPE_IPI: IPITemplateSlave,
}


class TaxTemplatesSearch(SearchEditor):
    size = (500, 350)
    title = _('Tax Classes Search')

    searchbar_label = _('Class Matching:')
    result_strings = _('class'), _('classes')
    search_table = ProductTaxTemplate
    editor_class = ProductTaxTemplateEditor

    def __init__(self, conn):
        SearchEditor.__init__(self, conn)
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
        #return SellableCategory.q.category_id != None
        return None
