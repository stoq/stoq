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

from kiwi.ui.objectlist import Column

from stoqlib.domain.taxes import ProductTaxTemplate
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searcheditor import SearchEditor
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
    search_label = _('Class Matching:')
    search_spec = ProductTaxTemplate
    editor_class = ProductTaxTemplateEditor
    text_field_columns = [ProductTaxTemplate.name]

    def get_columns(self):
        return [
            SearchColumn("name", _("Class name"), data_type=str,
                         sorted=True, expand=True),
            Column("tax_type_str", _("Type"), data_type=str, width=80),
        ]
