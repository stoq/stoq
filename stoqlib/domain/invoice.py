# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Invoice domain classes; field, layout and printer
"""

# pylint: enable=E1101

from storm.references import Reference
from zope.interface import implementer

from stoqlib.database.properties import IntCol, UnicodeCol, IdCol, BoolCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable


@implementer(IDescribable)
class InvoicePrinter(Domain):
    """An invoice printer is a representation of a physical printer
    connected to a branch station.
    It has a layout assigned which will be used to format the data sent
    to the printer
    """
    __storm_table__ = 'invoice_printer'

    #: a operating system specific identifier for the
    #: device used to send the printer job, /dev/lpX on unix
    device_name = UnicodeCol()

    #: a human friendly description of the printer, this
    #: will appear in interfaces
    description = UnicodeCol()

    #: the station this printer is connected to
    station_id = IdCol()
    station = Reference(station_id, 'BranchStation.id')

    #: the layout used to format the invoices
    layout_id = IdCol()
    layout = Reference(layout_id, 'InvoiceLayout.id')

    def get_description(self):
        """
        Gets the description of the printer.
        :returns: description
        """
        return self.description

    @classmethod
    def get_by_station(cls, station, store):
        """Gets the printer given a station.
        If there's no invoice printer configured for this station, return None.

        :param station: the station
        :param store: a store
        :returns: an InvoiceLayout or None
        """
        return store.find(InvoicePrinter, station=station).one()


@implementer(IDescribable)
class InvoiceLayout(Domain):
    """A layout of an invoice.
    """
    __storm_table__ = 'invoice_layout'

    #: description of the layout, this is human friendly
    #: string which is displayed in interfaces.
    description = UnicodeCol()

    #: the width in units of the layout
    width = IntCol()

    #: the height in units of the layout
    height = IntCol()

    #: Indicates the type of paper used to print the layout
    continuous_page = BoolCol()

    @property
    def size(self):
        return self.width, self.height

    @property
    def fields(self):
        """Fetches all the fields tied to this layout

        :returns: a sequence of InvoiceField
        """
        return self.store.find(InvoiceField,
                               layout=self)

    def get_description(self):
        """Gets the description of the field

        :returns: description.
        """
        return self.description


class InvoiceField(Domain):
    """Represents a field in an InvoiceLayout.
    """

    __storm_table__ = 'invoice_field'

    #: x position of the upper left corner of the field
    x = IntCol()

    #: y position of the upper left corner of the field
    y = IntCol()

    #: the width of the field, must be larger than 0
    width = IntCol()

    #: the height of the field, must be larger than 0
    height = IntCol()

    #: the name of the field, this is used to identify
    #: and fetch the data when printing the invoice
    field_name = UnicodeCol()

    #: the free text of the field
    content = UnicodeCol(default=u'')

    #: the layout this field belongs to
    layout_id = IdCol()
    layout = Reference(layout_id, 'InvoiceLayout.id')
