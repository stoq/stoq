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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Johan Dahlin             <jdahlin@async.com.br>
##
"""Invoice generation"""

import array
import datetime
from decimal import Decimal

from stoqdrivers.enum import TaxType
from stoqdrivers.escp import EscPPrinter

from stoqlib.domain.interfaces import ICompany, IIndividual, IPaymentGroup
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext as _


ENABLED = "X"
INVOICE_TYPE_IN  = 1
INVOICE_TYPE_OUT = 2

class SaleInvoice(object):
    def __init__(self, sale, layout):
        """Creates a new sale invoice
        @param sale: sale to print an invoice for
        @param layout: the invoice layout to use
        """
        self.sale = sale
        self.layout = layout
        self.type = _('Sale')
        self.today = datetime.datetime.today()

    def generate(self):
        """Formats the data from the sale according to the fields specified
        in the layout
        @returns: lines printed
        @rtype: a list of array
        """
        printerdata = []
        for lines in range(self.layout.height):
            printerdata.append(
                array.array('c', (' ' * self.layout.width) + '\n'))

        for field in self.layout.fields:
            invoice_field_class = get_invoice_field_by_name(field.field_name)
            if invoice_field_class is None:
                print 'WARNING: Could not find field %s' % (field.field_name,)
                continue
            invoice_field = invoice_field_class(self)

            right = field.x + field.width

            data = invoice_field.fetch()
            if invoice_field.field_type == bool:
                assert field.height == 1
                if data:
                    data = 'X'
                else:
                    data = ' '
                printerdata[field.y][field.x:right] = array.array(
                    'c', data.upper())
            elif invoice_field.field_type == str:
                if data is None:
                    data = 'X' * field.width
                data = str(data)
                data = '%-*s' % (int(field.width),
                                 data[:field.width])
                output = array.array('c', data.upper())
                printerdata[field.y][field.x:right] = output
            elif invoice_field.field_type == iter:
                for y, line in enumerate(data):
                    if line is None:
                        line = 'X' * field.width
                    line = str(line)
                    line = '%-*s' % (int(field.width), line[:field.width])

                    output = array.array('c', line.upper())
                    printerdata[field.y+y][field.x:right] = output
            else:
                raise AssertionError(
                    "unsupported field type: %s" % (
                    invoice_field.field_type,))
        return printerdata

    def send_to_printer(self, device):
        printer = EscPPrinter(device)
        for line in self.generate():
            printer.send(line.tostring())
        printer.form_feed()
        printer.done()



class PurchaseInvoice(object):
    def __init__(self, purchase):
        self.purchase = purchase
        self.type = _('Purchase')


class InvoiceFieldDescription(object):
    field_type = str
    height = 1
    description = ''
    name = None
    length = -1

    def __init__(self, invoice):
        self.invoice = invoice
        self.sale = invoice.sale
        self.conn = self.sale.get_connection()

    @classmethod
    def get_description(self):
        return self.description or self.name

invoice_fields = {}

def _add_invoice_field(field):
    global invoice_fields
    invoice_fields[field.name] = field

def get_invoice_field_by_name(field_name):
    global invoice_fields
    return invoice_fields.get(field_name)

def get_invoice_fields():
    global invoice_fields
    return invoice_fields.values()


class F(InvoiceFieldDescription):
    name = "COMPANY_DOCUMENT"
    description = _("Company document number")
    length =  4
    def fetch(self):
        return ICompany(self.sale.branch).cnpj

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    field_type = bool
    name = "OUTGOING_INVOICE"
    description = _("Outgoing invoice")
    length =  1
    def fetch(self):
        return isinstance(self.sale, SaleInvoice)

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    field_type = bool
    name = "INCOMING_INVOICE"
    description = _("Incoming invoice")
    length =  1
    def fetch(self):
        return isinstance(self.sale, PurchaseInvoice)

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_NAME"
    description = _('Client name')
    length =  35
    def fetch(self):
        return self.sale.client.person.name

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_ADDRESS"
    description = _('Client Address')
    length =  34
    def fetch(self):
        return self.sale.client.person.address.get_address_string()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_DOCUMENT"
    description = _("Client's document number")
    length =  14
    def fetch(self):
        individual = IIndividual(self.sale.client, None)
        if individual is not None:
            return individual.cpf

        company = ICompany(self.sale.client, None)
        if company is not None:
            return company.cnpj

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_DISTRICT"
    description = _('District')
    length =  15
    def fetch(self):
        return self.sale.client.person.address.district

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_POSTAL_CODE"
    description = _("Client's postal code")
    length =  8
    def fetch(self):
        return self.sale.client.person.address.postal_code

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_CITY"
    description = _("Client's City")
    length =  34
    def fetch(self):
        return self.sale.client.person.address.get_city()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_PHONE"
    description = _('Client Phone number')
    length =  12
    def fetch(self):
        return self.sale.client.person.phone_number

_add_invoice_field(F)

class F(InvoiceFieldDescription):
    name = "CLIENT_FAX"
    description = _('Client Fax number')
    length =  12
    def fetch(self):
        return self.sale.client.person.fax_number

_add_invoice_field(F)

class F(InvoiceFieldDescription):
    name = "CLIENT_PHONE_FAX"
    description = _('Client Phone/Fax number')
    length =  12
    def fetch(self):
        return '%s / %s' % (
            self.sale.client.person.phone_number,
            self.sale.client.person.fax_number)

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_STATE"
    description = _('Client state abbreviation')
    length =  2
    def fetch(self):
        return self.sale.client.person.address.get_state()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CLIENT_STATE_REGISTRY_DOCUMENT"
    description = _('Clients state registry number or document number')
    length =  14
    def fetch(self):
        company = ICompany(self.sale.client, None)
        if company is None:
            return ''

        return company.state_registry

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "ORDER_EMISSION_DATE"
    description = _('Emission date')
    length =  10
    def fetch(self):
        return str(self.invoice.today.date())

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "ORDER_CREATION_DATE"
    description = _('Creation date')
    length =  10
    def fetch(self):
        return str(self.invoice.today.date())

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "ORDER_CREATION_TIME"
    description = _('Creation time')
    length =  8
    def fetch(self):
        return str(self.invoice.today.strftime('%H:%S:%M'))

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PAYMENT_NUMBERS"
    description = _('Number of payments')
    length =  4
    def fetch(self):
        group = IPaymentGroup(self.sale)
        return str(group.get_items().count())

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PAYMENT_DUE_DATES"
    description = _('Payment due dates')
    length =  1
    def fetch(self):
        group = IPaymentGroup(self.sale)
        dates = [str(p.due_date.date()) for p in group.get_items()]
        return ', '.join(dates)

_add_invoice_field(F)

class F(InvoiceFieldDescription):
    name = "PAYMENT_VALUES"
    description = _('Payment values')
    length =  1
    def fetch(self):
        group = IPaymentGroup(self.sale)
        dates = [str(p.value) for p in group.get_items()]
        return ', '.join(dates)

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "BASE_DE_CALCULO_ICMS"
    length =  1
    def fetch(self):
        total = Decimal(0)
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if not tax or not tax.tax_value:
                continue
            total += sale_item.get_total()
        return total

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_ICMS"
    length =  1
    def fetch(self):
        total = Decimal(0)
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if tax and tax.tax_value:
                total += sale_item.get_total() * (tax.tax_value / 100)
        return total

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "BASE_DE_CALCULO_ICMS_SUBST"
    length =  1
    def fetch(self):
        total = Decimal(0)
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if tax.tax_type == TaxType.SUBSTITUTION:
                total += sale_item.get_total()
        return total

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_ICMS_SUBST"
    length =  1
    def fetch(self):
        total = Decimal(0)
        tax_value = sysparam(self.conn).SUBSTITUTION_TAX
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if tax.tax_type == TaxType.SUBSTITUTION:
                total += sale_item.get_total() * (Decimal(tax_value) / 100)
        return total

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_TOTAL_PRODUTOS"
    length =  1
    def fetch(self):
        return self.sale.get_sale_subtotal()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_FRETE"
    length =  1
    def fetch(self):
        return 0

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_SEGURO"
    length =  1
    def fetch(self):
        return 0

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_DESPESAS"
    length =  1
    def fetch(self):
        return 0

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_IPI"
    length =  1
    def fetch(self):
        return 0

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "VALOR_TOTAL_NOTA"
    length =  1
    def fetch(self):
        return self.sale.get_sale_subtotal()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "ADDITIONAL_SALE_NOTES"
    lenght = 1
    def fetch(self):
        return

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "SALE_NUMBER"
    length =  1
    def fetch(self):
        return self.sale.get_order_number_str()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "SALESPERSON_NAME"
    length =  1
    def fetch(self):
        return self.sale.get_salesperson_name()

_add_invoice_field(F)

class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_COUNTER"
    description = _('Product item counter')
    length =  3
    field_type = iter
    def fetch(self):
        for i in range(self.sale.products.count()):
            yield '%03d' % (i+1,)

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_CODE_DESCRIPTION"
    description = _('Product item code / description')
    length =  35
    field_type = iter

    def fetch(self):
        for sale_item in self.sale.products:
            yield '%014d / %s' % (
                sale_item.sellable.id,
                sale_item.get_description())

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_CODE_SITUATION"
    description = _('Product item situation')
    length =  1
    field_type = iter

    def fetch(self):
        for sale_item in self.sale.products:
            yield 'N'

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_CODE_UNIT"
    description = _('Product item unit')
    length =  2
    field_type = iter

    def fetch(self):
        for sale_item in self.sale.products:
            yield sale_item.sellable.get_unit_description()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_QUANTITY"
    description = _('Product item quantity')
    length =  5
    field_type = iter

    def fetch(self):
        for sale_item in self.sale.products:
            yield sale_item.quantity

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_PRICE"
    description = _('Product item price')
    length =  5
    field_type = iter

    def fetch(self):
        for sale_item in self.sale.products:
            yield sale_item.price

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_TOTAL"
    description = _('Product item total (price * quantity)')
    length =  7
    field_type = iter

    def fetch(self):
        for sale_item in self.sale.products:
            yield sale_item.get_total()

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "PRODUCT_ITEM_TAX"
    description = _('Product item tax')
    length =  2
    field_type = iter

    def fetch(self):
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if tax and tax.tax_value:
                value = '%02d' % (int(tax.tax_value),)
            else:
                value = ''
            yield value

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "INVOICE_TYPE"
    description = _("Invoice Type")
    length = 10

    def fetch(self):
        return self.invoice.type

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "CFOP"
    length = 4
    def fetch(self):
        if self.sale.cfop:
            return self.sale.cfop.code

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "STATE_REGISTRY"
    description = _("State registry number")
    length = 14
    def fetch(self):
        return ICompany(self.sale.branch).state_registry

_add_invoice_field(F)


class F(InvoiceFieldDescription):
    name = "INSCR_ESTADUAL_SUBSTITUTO_TRIB"
    length = 4
    def fetch(self):
        return
_add_invoice_field(F)
