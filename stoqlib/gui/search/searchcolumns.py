# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source
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
""" Special columns definition for kiwi lists """

import decimal

import gobject
import gtk
from kiwi.ui.objectlist import Column

from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class AccessorColumn(Column):
    def __init__(self, attribute, accessor, *args, **kwargs):
        if not accessor:
            raise TypeError('AccessorColumn needs an accessor argument')

        self.accessor = accessor
        assert callable(self.accessor)
        Column.__init__(self, attribute=attribute, *args, **kwargs)

    def get_attribute(self, instance, name, default=None):
        return self.accessor(instance)


class SearchColumn(Column):
    """
    I am a column that should be used in conjunction with
    :class:`stoqlib.gui.search.searchslave.SearchSlave`

    :param long_title: The title to display in the combo for this field.
                       This is usefull if you need to display a small
                       description on the column header, but still want a full
                       description on the advanced search.
    :param valid_values: This should be a list of touples (display value, db
                         value). If provided, then a combo with only this
                         values will be shown, instead of a free text entry.
    :param search_attribute: Use this if the name of the db column that should
                             be searched is different than the attribute of
                             the model.
    """

    #: overrides the function that generates the query to process the search
    search_func = gobject.property(type=object, default=None)

    #: names the search interface differently from the column
    search_label = gobject.property(type=object, default=None)

    #: use the query on the *having* part instead of the *where*'s on
    use_having = gobject.property(type=bool, default=False)

    #: if we should allow filtering by multiple values
    multiple_selection = gobject.property(type=bool, default=False)

    #: the search attribute to use when filtering by this column
    search_attribute = gobject.property(type=str, default=None)

    #: valid values to select when filtering by this column
    valid_values = gobject.property(type=object, default=None)

    #: long title to use in this column
    long_title = gobject.property(type=str, default=None)

    def __init__(self, attribute, title=None, data_type=None, **kwargs):
        kwargs.setdefault('search_attribute', attribute)

        Column.__init__(self, attribute, title, data_type, **kwargs)

        search_func = kwargs.get('search_func')
        if search_func and not callable(search_func):
            raise TypeError("search_func must be callable")

    def get_search_label(self):
        """Get the search label for this column.
          This is normally used when constructing a search filter for this
          column.
          :returns: the search label
        """
        return self.search_label or self.long_title or self.title


class IdentifierColumn(SearchColumn):
    """A column for :class:`stoqlib.database.properties.IdentifierCol`

    This is :class:`stoqlib.gui.search.searchcolumns.SearchColumn`, but
    with some properties adjusted to properly display identifiers, avoiding
    lots of code duplication.

    One can still overwrite some of those properties, but do that
    only if necessary! We want identifier to look alike everywhere.
    """

    def __init__(self, attribute, title=None, data_type=int,
                 format_func=str, width=80, justify=None,
                 **kwargs):
        if title is None:
            title = _(u"#")
        if justify is None:
            justify = gtk.JUSTIFY_RIGHT

        super(IdentifierColumn, self).__init__(
            attribute=attribute, title=title, data_type=data_type,
            format_func=format_func, width=width, justify=justify, **kwargs)


class QuantityColumn(SearchColumn):
    """A column for product quantities

    This is :class:`stoqlib.gui.search.searchcolumns.SearchColumn`, but will
    also display the unit of the product if available in the object
    """

    def __init__(self, attribute, title=None, width=60, **kwargs):
        super(QuantityColumn, self).__init__(attribute=attribute, title=title,
                                             data_type=decimal.Decimal,
                                             format_func=self._format_func, format_func_data=True,
                                             width=width, justify=gtk.JUSTIFY_RIGHT, **kwargs)

    def _format_func(self, obj, data):
        quantity = getattr(obj, self.attribute) or 0
        quantity_str = format_quantity(quantity)

        # The object must have a sellable and a product for this to work
        # properly. If not, just return the quantity. Dont use
        # sellable.product here to avoid to many queries
        sellable = getattr(obj, 'sellable', None)
        product = getattr(obj, 'product', None)
        if not sellable or not product:
            return quantity_str

        # If the product does not manage stock and the quantity is 0, show an
        # infinite symbol istead
        if not product.manage_stock and not quantity:
            return u"\u221E"

        if sellable.unit:
            unit_desc = obj.sellable.unit.description
        else:
            unit_desc = ''

        data = '%s %s' % (quantity_str, unit_desc)
        return data.strip()
