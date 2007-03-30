# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Sales invoice implementation. All this module is brazil-specific """

from datetime import datetime, date, time
from decimal import Decimal

from kiwi.argcheck import argcheck, number
from kiwi.python import ClassInittableObject
from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import new_transaction
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.domain.interfaces import IIndividual, ICompany
from stoqlib.domain.sale import Sale
from stoqlib.domain.person import PersonAdaptToClient
from stoqlib.domain.service import Service

ENABLED = "X"
INVOICE_TYPE_IN  = 1
INVOICE_TYPE_OUT = 2

class InvoiceType(number):
    @classmethod
    def value_check(mcs, name, value):
        if not value in (INVOICE_TYPE_IN, INVOICE_TYPE_OUT):
            raise ValueError("%s must be one of INVOICE_TYPE_* "
                             "constants" % name)

class SysCoordinate:
    """ A simple class to allow us define a simple matrix and put data on
    it easily, e.g:

    >>> syscoord = SysCoordinate(80, 25)
    >>> syscoord.insert_string(10, 20, 'A string')

    If you insert a string which has a column or line value which is out of
    range, a ValueError will be raised

    >>> syscoord.insert_string(81, 20, 'Foo')
    Traceback (most recent call last):
    ValueError: ...

    >>> syscoord.insert_string(78, 20, 'Bar')
    >>> raw_data = syscoord.get_data()
    ...

    To return the matrix properly formatted, call:
    >>> syscoord.get_data_as_string()
    ...

    """

    def __init__(self, lines, cols):
        self._lines = lines
        self._cols = cols
        self._data = [[' ' for _ in range(cols)] for _ in range(lines)]

    def get_data(self):
        return self._data

    def get_data_as_string(self):
        res = []
        for row in self.get_data():
            res.append("".join(row))
        return "\n".join(res)

    @argcheck(int, int, basestring)
    def insert_string(self, line, col, data):
        if line > self._lines:
            raise ValueError("line can't be greater than %d (given %d)"
                             % (self._lines, line))
        elif line < 0:
            raise ValueError("line can't be less than 0")
        elif col > self._cols:
            raise ValueError("col can't be greater than %d (given %d)"
                             % (self._cols, col))
        elif col < 0:
            raise ValueError("col can't be less than 0")

        for idx, d in enumerate(data[:self._cols - col]):
            self._data[line][col+idx] = d

class SaleInvoice(ClassInittableObject):
    """ This class implements the Stoq's invoice. """
    # (line, column)
    coords = {
        "INVOICE_TYPE_IN": (6, 53),
        "INVOICE_TYPE_OUT": (6, 60),
        # XXX The Branch Document is already typed in the fiscal note,
        # so there is no use for this field here.
        "BRANCH_DOCUMENT": (9, 52),
        "OPERATION_TYPE": (12, 0),
        "BRANCH_CFOP": (12, 25),
        "STATE_REGISTRY_SUBST_TRIB": (12, 31),
        # XXX The State Registry is already typed in the fiscal note,
        # so there is no use for this field here also.
        "STATE_REGISTRY": (12, 52),
        "CLIENT_NAME": (15, 0),
        "CLIENT_DOCUMENT": (15, 49),
        "CREATION_DATE": (15, 70),
        "CLIENT_ADDRESS": (17, 0),
        "CLIENT_DISTRICT": (17, 39),
        "CLIENT_POSTAL_CODE": (17, 59),
        "EXPEDITION_DATE": (17, 70),
        "CLIENT_CITY": (19, 0),
        "CLIENT_PHONE": (19, 29),
        "CLIENT_STATE": (19, 45),
        "CLIENT_STATE_REGISTRY": (19, 49),
        "EXPEDITION_TIME": (19, 70),
        # These coordinates are referred to the fist row of the
        # products table.
        "PRODUCT_CODE": (28, 0),
        "PRODUCT_DESCRIPTION": (28, 5),
        "PRODUCT_CST": (28, 34),
        "PRODUCT_UNITY": (28, 38),
        "PRODUCT_QUANTITY": (28, 41),
        "PRODUCT_UNIT_VALUE": (28, 47),
        "PRODUCT_TOTAL_VALUE": (28, 56),
        "PRODUCT_ICMS_PERCENT": (28, 65),
        "PRODUCT_IPI_PERCENT": (28, 68),
        "PRODUCT_IPI_VALUE": (28, 71),
        # These coordinates are related to the "tax table"
        "ICMS_CALC_BASE": (49, 0),
        "ICMS_VALUE": (49, 15),
        "SUBST_ICMS_CALC_BASE": (49, 30),
        "SUBST_ICMS_VALUE": (49, 45),
        "TOTAL_PRODUCTS_VALUE": (49, 63),
        "FREIGHT_VALUE": (51 , 0),
        "INSURANCE_VALUE": (51, 15),
        "TOTAL_IPI_VALUE": (51, 45),
        "INVOICE_TOTAL_VALUE": (51, 63),
        }

    # "setter_name" : (max_size, coord_name)
    setters = {
        "operation_type" : (24, "OPERATION_TYPE"),
        "branch_document": (17, "BRANCH_DOCUMENT"),
        "branch_cfop": (5, "BRANCH_CFOP"),
        "state_registry_subst_trib": (21, "STATE_REGISTRY_SUBST_TRIB"),
        "state_registry": (17, "STATE_REGISTRY"),
        "client_name": (48, "CLIENT_NAME"),
        "client_document": (19, "CLIENT_DOCUMENT"),
        "creation_date": (None, "CREATION_DATE"),
        "client_address": (38, "CLIENT_ADDRESS"),
        "client_district": (19, "CLIENT_DISTRICT"),
        "client_postal_code": (9, "CLIENT_POSTAL_CODE"),
        "expedition_date": (None, "EXPEDITION_DATE"),
        "client_city": (28, "CLIENT_CITY"),
        "client_phone": (15, "CLIENT_PHONE"),
        "client_state": (2, "CLIENT_STATE"),
        "client_state_registry": (19, "CLIENT_STATE_REGISTRY"),
        "expedition_time": (None, "EXPEDITION_TIME"),
        "icms_calc_base": (14, "ICMS_CALC_BASE"),
        "icms_value": (14, "ICMS_VALUE"),
        "subst_icms_calc_base": (14, "SUBST_ICMS_CALC_BASE"),
        "subst_icms_value": (17, "SUBST_ICMS_VALUE"),
        "total_products_value": (16, "TOTAL_PRODUCTS_VALUE"),
        "freight_value": (14, "FREIGHT_VALUE"),
        "insurance_value": (14, "INSURANCE_VALUE"),
        "total_ipi_value": (17, "TOTAL_IPI_VALUE"),
        "invoice_total_value": (16, "INVOICE_TOTAL_VALUE"),
        }

    ROWS_QTY = 60
    COLS_QTY = 80
    MAX_PRODUCT_QTY = 18
    # default filename for the invoice
    default_filename = _(u"invoice") + ".txt"

    @argcheck(basestring, Sale, datetime, InvoiceType)
    def __init__(self, filename, sale, date=datetime.now(),
                 invoice_type=INVOICE_TYPE_OUT):
        """
        @param filename:  The filename where the invoice will be saved in.
        @type filename:   basestring

        @param sale:      The Sale object where this class will get data
                          from.
        @type sale:       Sale

        @param date:      The invoice expedition date
        @type date:       datetime

        @param invoice_type: The invoice type (one of INVOICE_TYPE_*
                          constants).
        @type invoice_type: InvoiceType

        @param type_desc: The invoice description (this is the 'Natureza
                          'da operacao' field on invoice).
        @type type_desc:  basestring
        """
        ClassInittableObject.__init__(self)
        if sale.client is None:
            raise ValueError("It is not possible to emit an invoice for a "
                             "sale without client")
        self._syscoord = SysCoordinate(SaleInvoice.ROWS_QTY,
                                       SaleInvoice.COLS_QTY)
        self.branch_cfop = sale.cfop.code
        self._type_desc = sale.cfop.description
        self._sale = sale
        self._products_qty = 0
        self._date = date
        self._type = invoice_type
        self._filename = filename

    @classmethod
    def __class_init__(cls, namespace):
        for setter_name, (maxlen, cname) in cls.setters.items():
            p = property(
                fset=lambda self, data, max_len=maxlen, coord_name=cname:\
                        self._insert_data_on_coordinate(data, coord_name,
                                                        max_len=max_len))
            setattr(cls, setter_name, p)

    def _get_coordinates_for(self, coord_name):
        try:
            return SaleInvoice.coords[coord_name]
        except KeyError:
            raise TypeError("coordinates for `%s' doesn't exists" % coord_name)

    def _insert_string_on_coordinate(self, text, coord_name, max_len=None,
                                     increment=None):
        if max_len is not None:
            text = text[:max_len]
        if (increment is not None and isinstance(increment, (list, tuple))
            and len(increment) == 2):
            y, x = increment
        else:
            y = x = 0
        coords = self._get_coordinates_for(coord_name)
        self._syscoord.insert_string(coords[0]+y, coords[1]+x, text)

    def _insert_data_on_coordinate(self, data, coord_name, max_len=None,
                                   increment=None):
        if isinstance(data, date):
            data = data.strftime("%d/%m/%y")
        elif isinstance(data, time):
            data = data.strftime("%X")
        elif isinstance(data, unicode):
            data = data.encode("cp850")
        elif not isinstance(data, basestring):
            raise TypeError("The datatype %r isn't supported" % type(data))
        return self._insert_string_on_coordinate(data, coord_name, max_len,
                                                 increment=increment)

    @argcheck(PersonAdaptToClient)
    def _identify_client(self, client):
        self.client_name = client.get_name()
        client_role = self._sale.get_sale_client_role()
        if IIndividual.providedBy(client_role):
            self.client_document = client_role.cpf
        elif ICompany.providedBy(client_role):
            self.client_state_registry = client_role.state_registry
            self.client_document = client_role.cnpj
        else:
            raise TypeError("The client role for sale %r must be a "
                            "Invidual or a Company" % self._sale)
        address = client.person.get_main_address()
        self.client_address = "%s, %s" % (address.street, address.number)
        self.client_district = address.district
        self.client_postal_code = address.postal_code
        self.client_city = address.city_location.city
        self.client_state = address.city_location.state
        self.client_phone = client.person.phone_number

    def get_document_as_string(self):
        return self._syscoord.get_data_as_string()

    def _setup_products(self, products):
        trans = new_transaction()
        icms_total = Decimal(0)
        subst_total = Decimal(0)
        prod_total = Decimal(0)
        icms_tax = sysparam(trans).ICMS_TAX
        subst_tax = sysparam(trans).SUBSTITUTION_TAX

        for i, item in enumerate(products):
            if i == SaleInvoice.MAX_PRODUCT_QTY:
                break
            elif isinstance(item.sellable.get_adapted(), Service):
                continue
            self._insert_data_on_coordinate(item.sellable.get_code_str(),
                                            "PRODUCT_CODE",
                                            max_len=4, increment=(i,0))
            self._insert_data_on_coordinate(item.sellable.get_description(),
                                            "PRODUCT_DESCRIPTION",
                                            max_len=26, increment=(i,0))
            if item.sellable.unit:
                self._insert_data_on_coordinate(
                    item.sellable.get_unit_description(), "PRODUCT_UNITY",
                    max_len=2, increment=(i,0))
            self._insert_data_on_coordinate("%2.2f" % item.quantity,
                                            "PRODUCT_QUANTITY", increment=(i,0))
            self._insert_data_on_coordinate("%5.2f" % item.price,
                                            "PRODUCT_UNIT_VALUE",
                                            increment=(i,0))
            total_value = item.price * item.quantity
            self._insert_data_on_coordinate("%5.2f" % total_value,
                                            "PRODUCT_TOTAL_VALUE",
                                            increment=(i,0))
            if item.sellable.tax_type == TaxType.SUBSTITUTION:
                value = "%3d" % subst_tax
                subst_total += total_value
            elif item.sellable.tax_type == TaxType.CUSTOM:
                raise NotImplementedError
            else:
                raise TypeError("Invalid tax type for product %r, got %r"
                                % (item.sellable, item.sellable.tax_type))
            prod_total += total_value
            self._insert_data_on_coordinate(value, "PRODUCT_ICMS_PERCENT",
                                            max_len=3, increment=(i,0))

        self.icms_calc_base = "%.2f" % icms_total
        self.subst_icms_calc_base = "%.2f" % subst_total
        self.total_products_value = "%.2f" % prod_total
        self.invoice_total_value = "%.2f" % prod_total
        self.subst_icms_value = "%.2f" % ((Decimal(str(subst_tax))
                                           / Decimal(100))
                                          * subst_total)
        self.icms_value = "%.2f" % ((Decimal(str(icms_tax))
                                     / Decimal(100))
                                    * icms_total)

    def build(self):
        if self._type == INVOICE_TYPE_IN:
            self._insert_string_on_coordinate(ENABLED, "INVOICE_TYPE_IN")
        elif self._type == INVOICE_TYPE_OUT:
            self._insert_string_on_coordinate(ENABLED, "INVOICE_TYPE_OUT")
        self.operation_type = self._type_desc
        self.creation_date = self._sale.model_created
        self.expedition_date = self._date.date()
        self.expedition_time = self._date.time()
        self._identify_client(self._sale.client)
        self._setup_products(self._sale.get_items())

    def save(self):
        self.build()
        open(self._filename, "w").write(self.get_document_as_string())
