# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Search extentions add columns and tables to search dialogs"""


class SearchExtension(object):
    """A SearchExtension is intended to add extra columns to a SearchDialog.

    Suppose you have the following dialog:

    #>>> class ProductSearch(SearchDialog):
    #...     search_spec = ProductsView
    #...
    #...     def get_columns(self):
    #...         return [Column('name')]

    This is the default search, and it has only one column. The use has the
    optical plugin installed, and this plugin adds a few more properties to a
    product, like the color of the product.

    A search extention for this dialog would be defined as:

    #>>> class OpticalProductSearchExtention(SearchExtension):
    #...     spec_joins = [
    #...         LeftJoin(OpticalProduct, OpticalProduct.product_id == Product.id)
    #...     ]
    #...
    #...     spec_attributes = dict(
    #...         color=OpticalProduct.color
    #...     )
    #...
    #...     def get_columns(self):
    #...         return [Column('color')]

    Then, the plugin should also connect to the event
    :class:`stoqlib.gui.events.SearchDialogSetupSearchEvent` and when the
    desired dialog is being set up, he should attach the extention:

    #>>> dialog = ProductSearch()
    #>>> dialog.add_extention(OpticalProductSearchExtention())

    """

    #: A list of table joins that will be added to the query of the search
    spec_joins = []

    #: A dictionary of the columns that should be queried. Normally columns from
    #: the tables specified in the spec_joins above
    spec_attributes = {}

    def attach(self, search):
        """Attaches this extension to the given search dialog

        This will replace the viewable of the dialog by another one that is a
        subclass of the original, extended with the desired tables and columns,
        defined in the spec_joins and spec_attributes.
        """
        search.search_spec = search.search_spec.extend_viewable(self.spec_attributes,
                                                                self.spec_joins)
        search.add_columns(self.get_columns())

    def get_columns(self):  # pragma no cover
        """Returns the extra columns that should be added in the search dialog.

        If the column is not already present in the original viewable of the
        search dialog, it should be specified in the spec_attributes above
        """
        raise NotImplementedError
