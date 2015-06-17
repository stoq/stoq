# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2015 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Invoice generation"""

import array
from decimal import Decimal

from kiwi.datatypes import ValidationError

from stoqdrivers.enum import TaxType
from stoqdrivers.escp import EscPPrinter

from stoqlib.domain.sale import Sale
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.message import warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext as _


def splititers(iterator, size):
    while iterator:
        yield iterator[:size]
        iterator = iterator[size:]


class InvoicePage(object):
    """This represent a page part of an invoice"""

    def __init__(self, width, height):
        """
        Create a new InvoicePage object.
        :param width: the width of the page
        :param height: the height of the page
        """
        self._data = []

        for lines in range(height):
            self._data.append(
                array.array('c', (' ' * width) + '\n'))
        self.width = width
        self.height = height

    def __iter__(self):
        return iter(self._data)

    def _put(self, x, y, width, data):
        if type(data) != str:
            raise AssertionError(type(data))
        output = array.array('c', data.upper())
        if y > len(self._data):
            raise ValueError(
                "maximum invoice layout is %d, got %d" % (self.height, y))

        row = self._data[y]
        row[x:x + width] = output[:width]

    def _add_boolean(self, x, y, width, data):
        if data:
            data = 'X'
        else:
            data = ' '
        self._put(x, y, width, data)

    def _add_integer(self, x, y, width, data):
        if data is None:
            data = ''
        else:
            data = '%*.2f' % (int(width), data)
        self._put(x, y, width, data)

    def _add_decimal(self, x, y, width, data):
        if data is None:
            data = ''
        else:
            data = '%*.2f' % (int(width), float(data))
        self._put(x, y, width, data)

    def _add_string(self, x, y, width, data):
        if type(data) == unicode:
            data = str(data)
        if data is None:
            data = ''
        else:
            data = '%-*s' % (int(width), data)
        self._put(x, y, width, data)

    def _add_list(self, data_type, x, y, width, height, data):
        for y_offset, line in enumerate(data):
            self.add(data_type[0], x, y + y_offset,
                     width, height, line)

    def add(self, data_type, x, y, width, height, data):
        """Adds a new field to the page

        :param data_type: data type of the field
        :param x: x position of the left side of the field
        :param y: y position of the upper side of the field
        :param width: width of the field
        :param height: height of the field
        :param data: data to be printed at the field. This is dependent of
          the data type
        """
        if data_type == bool:
            self._add_boolean(x, y, width, data)
        elif data_type == str:
            self._add_string(x, y, width, data)
        elif data_type == Decimal:
            self._add_decimal(x, y, width, data)
        elif data_type == int:
            self._add_integer(x, y, width, data)
        elif type(data_type) == list:
            self._add_list(data_type, x, y, width, height, data)
        else:
            raise AssertionError(
                "unsupported field type: %s" % (data_type, ))


class _Invoice(object):
    date_format = '%d-%m-%Y'

    def __init__(self, layout):
        self.layout = layout
        self.header_fields = []
        self.list_fields = []
        self.footer_fields = []

        self._arrange_fields()

    def _arrange_fields(self):
        """Arrange all the fields.
        We have three field types internally, headers, list and footers.
        The header iterms should appear on all pages
        The list items should be split up and separated by page
        Footer items should only appear on the last page

        List items are items are invoice fields which has a list type
        All items which has are located above a list item is a header item
        and all item which are located belove is a footer item.
        """

        # First pass, figure out upper and lower bounds of the list area,
        # eg the area which the list items cover.

        # FIXME if we have a non-list widget in between lists, it will be treat
        # that widget as a list, which will crash the program
        top = self.layout.height
        bottom = 0
        for field in self.layout.fields:
            invoice_field_class = get_invoice_field_by_name(field.field_name)
            if not isinstance(invoice_field_class.field_type, list):
                continue
            if field.y < top:
                top = field.y
            if (field.y + field.height) > bottom:
                bottom = field.y + field.height

        # Now when we know the interval of all the list items,
        # Just arrange the items by their relative position to the
        # list area:
        #   above area  -> header
        #   below area  -> footer
        #   inside arae -> list

        for field in self.layout.fields:
            if field.y + field.height <= top:
                self.header_fields.append(field)
            elif field.y >= bottom:
                self.footer_fields.append(field)
            else:
                self.list_fields.append(field)

    def _fetch_data_by_field(self, field):
        invoice_field_class = get_invoice_field_by_name(field.field_name)
        if invoice_field_class is None:
            print('WARNING: Could not find field %s' % (field.field_name, ))
            return
        invoice_field = invoice_field_class(self, field)
        return (invoice_field.fetch(field.width, field.height),
                invoice_field.field_type)

    def _add_field(self, page, field, height_delta=0):
        data, field_type = self._fetch_data_by_field(field)

        page.add(field_type,
                 field.x, field.y + height_delta,
                 field.width, field.height,
                 data)

    def _fetch_list_fields(self):
        """Fetch the list field data and seperate/sort it by page.
        The dictionary returned is structured like this::
          - key: page number
          - value: field, field_type, lines for the page
            - field comes from the database
            - field_type is the type of the field
            - lines is all the lines which should be printed on
              the current page
        :returns: a dictionary
        """

        # Fetch the data from all list fields
        list_fields = []
        for field in self.list_fields:
            data, field_type = self._fetch_data_by_field(field)
            list_fields.append((field, field_type, list(data)))

        # Split up the data by page
        page_list_fields = {}
        for field, field_type, data in list_fields:
            if self.layout.continuous_page:
                line_data = [data]
            else:
                line_data = splititers(data, field.height)

            for n, lines in enumerate(line_data):
                if not n in page_list_fields:
                    page_list_fields[n] = []
                page_list_fields[n].append((field, field_type, lines))

        return page_list_fields

    def generate_pages(self):
        """Formats the data from the sale according to the fields specified
        in the layout
        :returns: pages printed
        :rtype: a list of pages
        """

        list_field_data = self._fetch_list_fields()

        pages = []
        # The height delta is how many lines the footer should be offset to the
        # bottom when printing continuously.
        height_delta = 0
        if self.layout.continuous_page:
            # When printing continuously, there is only one page
            first_page = list_field_data[0]
            # Get the first field of this page
            field = first_page[0]
            # And the number of lines in this field
            height_delta = len(field[2]) - 1

        for page_no in sorted(list_field_data):
            list_fields = list_field_data[page_no]

            page = InvoicePage(self.layout.width,
                               self.layout.height + height_delta)

            # Header fields
            for field in self.header_fields:
                self._add_field(page, field)

            # List fields
            for field, field_type, lines in list_fields:
                page.add(field_type,
                         field.x, field.y,
                         field.width, field.height,
                         lines)
            pages.append(page)

        # Footer fields
        if pages:
            last_page = pages[-1]
            for field in self.footer_fields:
                self._add_field(last_page, field, height_delta)

        return pages

    def has_invoice_number(self):
        """Returns if the invoice has an invoice number field or not.

        :returns: True if there is an invoice field, False otherwise
        """
        for field in self.header_fields:
            if field.field_name == 'INVOICE_NUMBER':
                return True
        return False

    def send_to_printer(self, device):
        """Send the printer invoice to the printer
        :param device: device name of the printer
        :type device: string
        """
        try:
            printer = EscPPrinter(device)
        except IOError as e:
            warning(str(e))
            return
        for page in self.generate_pages():
            for line in page:
                printer.send(line.tostring())
            printer.form_feed()
        printer.done()


class SaleInvoice(_Invoice):
    def __init__(self, sale, layout):
        """Creates a new sale invoice
        :param sale: sale to print an invoice for
        :param layout: the invoice layout to use
        """
        _Invoice.__init__(self, layout)
        self.sale = sale
        self.type = _('Sale')
        self.today = localtoday().date()


class PurchaseInvoice(_Invoice):
    def __init__(self, purchase, layout):
        _Invoice.__init__(self, layout)
        self.purchase = purchase
        self.type = _('Purchase')
        self.today = localtoday().date()


def print_sale_invoice(sale_invoice, invoice_printer):
    """Utility function to print a sale invoice.

    :param sale: a :class:`stoqlib.domain.sale.Sale` instance
    :param invoice_printer: :class:`stoqlib.domain.invoice.InvoicePrinter` instance
    """
    sale_invoice.send_to_printer(invoice_printer.device_name)


def validate_invoice_number(invoice_number, store):
    if not 0 < invoice_number <= 999999999:
        return ValidationError(
            _("Invoice number must be between 1 and 999999999"))

    sale = store.find(Sale, invoice_number=invoice_number).one()
    if sale is not None:
        return ValidationError(_(u'Invoice number already used.'))


class InvoiceFieldDescription(object):
    field_type = str
    height = 1
    description = ''
    name = None
    category = ''
    length = -1

    def __init__(self, invoice, field):
        self.invoice = invoice
        self.field = field
        self.sale = invoice.sale
        self.store = self.sale.store

    @classmethod
    def get_description(cls):
        return cls.description or cls.name

invoice_fields = {}


def _register_invoice_field(field):
    invoice_fields[field.name] = field
    return field


def get_invoice_field_by_name(field_name):
    return invoice_fields.get(field_name)


def get_invoice_fields():
    return list(invoice_fields.values())


@_register_invoice_field
class FreeTextField(InvoiceFieldDescription):
    name = u"FREE_TEXT"
    description = _("Free text")
    category = _("Other")
    length = 10

    def fetch(self, width, height):
        return self.field.content


#
# Company fields
#

@_register_invoice_field
class CompanyDocumentField(InvoiceFieldDescription):
    name = u"COMPANY_DOCUMENT"
    description = _("Company document number")
    category = _("Branch")
    length = 18

    def fetch(self, width, height):
        return self.sale.branch.person.company.cnpj


@_register_invoice_field
class StateRegistryField(InvoiceFieldDescription):
    name = u"STATE_REGISTRY"
    description = _("State registry number")
    category = _("Branch")
    length = 14

    def fetch(self, width, height):
        return self.sale.branch.person.company.state_registry


@_register_invoice_field
class CityRegistryField(InvoiceFieldDescription):
    name = u"CITY_REGISTRY"
    description = _("City registry number")
    category = _("Branch")
    length = 14

    def fetch(self, width, height):
        return self.sale.branch.person.company.city_registry


@_register_invoice_field
class InscrEstadualSubstitudoField(InvoiceFieldDescription):
    name = u"INSCR_ESTADUAL_SUBSTITUTO_TRIB"
    category = _("Branch")
    length = 4

    def fetch(self, width, height):
        # TODO figure out what to return
        return ''


@_register_invoice_field
class CompanyAddressField(InvoiceFieldDescription):
    name = u"COMPANY_ADDRESS"
    description = _("Company address")
    category = _("Branch")
    length = 34

    def fetch(self, width, height):
        return self.sale.branch.person.address.get_address_string()


@_register_invoice_field
class CompanyNameField(InvoiceFieldDescription):
    name = u"COMPANY_NAME"
    description = _("Company name")
    category = _("Branch")
    length = 34

    def fetch(self, width, height):
        return self.sale.branch.person.name


@_register_invoice_field
class CompanyFancyNameField(InvoiceFieldDescription):
    name = u"COMPANY_FANCY_NAME"
    description = _("Company fancy name")
    category = _("Branch")
    length = 34

    def fetch(self, width, height):
        return self.sale.branch.person.company.fancy_name


@_register_invoice_field
class CompanyPostalCodeField(InvoiceFieldDescription):
    name = u"COMPANY_POSTAL_CODE"
    description = _("Company postal code")
    category = _("Branch")
    length = 8

    def fetch(self, width, height):
        return self.sale.branch.person.address.postal_code


@_register_invoice_field
class CompanyCityLocationField(InvoiceFieldDescription):
    name = u"COMPANY_CITY_LOCATION"
    description = _("Company city location")
    category = _("Branch")
    length = 8

    def fetch(self, width, height):
        city_location = self.sale.branch.person.address.city_location
        return '%s / %s' % (city_location.city, city_location.state)


#
# Sale fields
#

@_register_invoice_field
class SaleNumberField(InvoiceFieldDescription):
    name = u"SALE_NUMBER"
    category = _("Sale")
    length = 1

    def fetch(self, width, height):
        return unicode(self.sale.identifier)


@_register_invoice_field
class SalesPersonNameField(InvoiceFieldDescription):
    name = u"SALESPERSON_NAME"
    category = _("Sale")
    length = 1

    def fetch(self, width, height):
        return self.sale.get_salesperson_name()


@_register_invoice_field
class CfopField(InvoiceFieldDescription):
    name = u"CFOP"
    category = _("Other")
    length = 4

    def fetch(self, width, height):
        if self.sale.cfop:
            return self.sale.cfop.code


@_register_invoice_field
class SaleTotalValueField(InvoiceFieldDescription):
    name = u"VALOR_TOTAL_NOTA"
    category = _("Sale")
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        return self.sale.get_sale_subtotal()


@_register_invoice_field
class AdditionalSaleNotesField(InvoiceFieldDescription):
    name = u"ADDITIONAL_SALE_NOTES"
    category = _("Sale")
    lenght = 1

    def fetch(self, width, height):
        comments = []
        # FIXME We may have problems to print multiples comments.
        # If we have comments that exceeds the lenght of the widget, it wont
        # print it properly
        for comment in self.sale.comments:
            comments.append(comment.comment)
        return '\n'.join(comments)


@_register_invoice_field
class SaleTokenField(InvoiceFieldDescription):
    name = u"SALE_TOKEN_CODE"
    description = _("Sale token code")
    category = _("Sale")
    length = 8

    def fetch(self, width, height):
        if not self.sale.sale_token_id:
            return ''
        return self.sale.sale_token.code


#
# Product fields
#

@_register_invoice_field
class ProductItemCounterField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_COUNTER"
    description = _('Product item counter')
    category = _("Product")
    length = 3
    field_type = [str]

    def fetch(self, width, height):
        product_count = self.sale.products.count()
        for i in range(product_count):
            # This will pad zeros dynamicly, accordingly to product_count
            yield '%0*d' % (len(str(product_count)), i + 1)


@_register_invoice_field
class ProductItemCodeDescriptionField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_CODE_DESCRIPTION"
    description = _('Product item code / description')
    category = _("Product")
    length = 35
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            code = '%014s' % sale_item.sellable.code
            yield '%s / %s' % (
                code.replace(' ', '0'),
                sale_item.get_description())


@_register_invoice_field
class ProductItemDescriptionField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_DESCRIPTION"
    description = _('Product item description')
    category = _("Product")
    length = 30
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            yield '%s' % sale_item.get_description()


@_register_invoice_field
class ProductItemCodeField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_CODE"
    description = _('Product item code')
    category = _("Product")
    length = 5
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            code = '%05s' % sale_item.sellable.code
            yield code[-width:]


@_register_invoice_field
class ProductItemCodeSituationField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_CODE_SITUATION"
    description = _('Product item situation')
    category = _("Product")
    length = 1
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            yield 'N'


@_register_invoice_field
class ProductItemCodeUnitField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_CODE_UNIT"
    description = _('Product item unit')
    category = _("Product")
    length = 2
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            yield sale_item.sellable.unit_description


@_register_invoice_field
class ProductItemQuantityField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_QUANTITY"
    description = _('Product item quantity')
    category = _("Product")
    length = 5
    field_type = [Decimal]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            yield sale_item.quantity


@_register_invoice_field
class ProductItemPriceField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_PRICE"
    description = _('Product item price')
    category = _("Product")
    length = 5
    field_type = [Decimal]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            yield sale_item.price


@_register_invoice_field
class ProductItemTotalField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_TOTAL"
    description = _('Product item total (price * quantity)')
    category = _("Product")
    length = 7
    field_type = [Decimal]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            yield sale_item.get_total()


@_register_invoice_field
class ValorTotalProductsField(InvoiceFieldDescription):
    name = u"VALOR_TOTAL_PRODUTOS"
    category = _("Product")
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        return self.sale.get_sale_subtotal()


#
# Client fields
#

@_register_invoice_field
class ClientNameField(InvoiceFieldDescription):
    name = u"CLIENT_NAME"
    description = _('Client name')
    category = _("Client")
    length = 35

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.name


@_register_invoice_field
class ClientAddressField(InvoiceFieldDescription):
    name = u"CLIENT_ADDRESS"
    description = _('Client Address')
    category = _("Client")
    length = 34

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.address.get_address_string()


@_register_invoice_field
class ClientDocumentField(InvoiceFieldDescription):
    name = u"CLIENT_DOCUMENT"
    description = _("Client's document number")
    category = _("Client")
    length = 14

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        individual = self.sale.client.person.individual
        if individual is not None:
            return individual.cpf

        company = self.sale.client.person.company
        if company is not None:
            return company.cnpj


@_register_invoice_field
class ClientDistrictField(InvoiceFieldDescription):
    name = u"CLIENT_DISTRICT"
    description = _("Client's district")
    category = _("Client")
    length = 15

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.address.district


@_register_invoice_field
class ClientPostalCodeField(InvoiceFieldDescription):
    name = u"CLIENT_POSTAL_CODE"
    description = _("Client's postal code")
    category = _("Client")
    length = 8

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.address.postal_code


@_register_invoice_field
class ClientCityField(InvoiceFieldDescription):
    name = u"CLIENT_CITY"
    description = _("Client's city")
    category = _("Client")
    length = 34

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.address.get_city()


@_register_invoice_field
class ClientPhoneField(InvoiceFieldDescription):
    name = u"CLIENT_PHONE"
    description = _('Client Phone number')
    category = _("Client")
    length = 12

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.phone_number


@_register_invoice_field
class ClientFaxField(InvoiceFieldDescription):
    name = u"CLIENT_FAX"
    description = _('Client Fax number')
    category = _("Client")
    length = 12

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.fax_number


@_register_invoice_field
class ClientPhoneFaxField(InvoiceFieldDescription):
    name = u"CLIENT_PHONE_FAX"
    description = _('Client Phone/Fax number')
    category = _("Client")
    length = 12

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return '%s / %s' % (
            self.sale.client.person.phone_number,
            self.sale.client.person.fax_number)


@_register_invoice_field
class ClientStateField(InvoiceFieldDescription):
    name = u"CLIENT_STATE"
    description = _('Client state abbreviation')
    category = _("Client")
    length = 2

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        return self.sale.client.person.address.get_state()


@_register_invoice_field
class ClientStateRegistryDocumentField(InvoiceFieldDescription):
    name = u"CLIENT_STATE_REGISTRY_DOCUMENT"
    description = _('Clients state registry number or document number')
    category = _("Client")
    length = 14

    def fetch(self, width, height):
        if not self.sale.client:
            return ''
        company = self.sale.client.person.company
        if company is None:
            return ''

        return company.state_registry


#
# Payment fields
#

@_register_invoice_field
class PaymentNumbersField(InvoiceFieldDescription):
    name = u"PAYMENT_NUMBERS"
    description = _('Number of payments')
    category = _('Payment')
    length = 4

    def fetch(self, width, height):
        return str(self.sale.payments.count())


@_register_invoice_field
class PaymentDueDatesField(InvoiceFieldDescription):
    name = u"PAYMENT_DUE_DATES"
    description = _('Payment due dates')
    category = _('Payment')
    length = 1

    def fetch(self, width, height):
        dates = [p.due_date.strftime(self.invoice.date_format)
                 for p in self.sale.payments]
        return ', '.join(dates)


@_register_invoice_field
class PaymentValuesField(InvoiceFieldDescription):
    name = u"PAYMENT_VALUES"
    description = _('Payment values')
    category = _('Payment')
    length = 1

    def fetch(self, width, height):
        dates = [str(p.value) for p in self.sale.payments]
        return ', '.join(dates)


#
# Tax fields
#

@_register_invoice_field
class BaseDeCalculoICMSField(InvoiceFieldDescription):
    name = u"BASE_DE_CALCULO_ICMS"
    length = 1
    category = _('Tax')
    field_type = Decimal

    def fetch(self, width, height):
        total = Decimal(0)
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if not tax or not tax.tax_value:
                continue
            total += sale_item.get_total()
        return total


@_register_invoice_field
class ICMSValueField(InvoiceFieldDescription):
    name = u"VALOR_ICMS"
    category = _('Tax')
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        total = Decimal(0)
        for sale_item in self.sale.products:
            # FIXME: Use the same information we already added for NF-e
            tax = sale_item.sellable.get_tax_constant()
            if tax and tax.tax_value:
                total += sale_item.get_total() * (tax.tax_value / 100)
        return total


@_register_invoice_field
class BaseDeCalculoICMSSubstField(InvoiceFieldDescription):
    name = u"BASE_DE_CALCULO_ICMS_SUBST"
    category = _('Tax')
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        total = Decimal(0)
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if tax.tax_type == TaxType.SUBSTITUTION:
                total += sale_item.get_total()
        return total


@_register_invoice_field
class ValorICMSSubstField(InvoiceFieldDescription):
    name = u"VALOR_ICMS_SUBST"
    category = _('Tax')
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        total = Decimal(0)
        tax_value = sysparam.get_decimal('SUBSTITUTION_TAX')
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if tax.tax_type == TaxType.SUBSTITUTION:
                total += sale_item.get_total() * (Decimal(tax_value) / 100)
        return total


@_register_invoice_field
class BaseDeCalculoISSField(InvoiceFieldDescription):
    name = u"BASE_DE_CALCULO_ISS"
    category = _('Tax')
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        total = Decimal(0)
        for sale_item in self.sale.services:
            tax = sale_item.sellable.get_tax_constant()
            if not tax or not tax.tax_value:
                continue
            total += sale_item.get_total()
        return total


@_register_invoice_field
class ValorISSField(InvoiceFieldDescription):
    name = u"VALOR_ISS"
    category = _('Tax')
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        total = Decimal(0)
        tax_value = sysparam.get_decimal('ISS_TAX')
        for sale_item in self.sale.services:
            tax = sale_item.sellable.get_tax_constant()
            if tax.tax_type == TaxType.SERVICE:
                total += sale_item.get_total() * (Decimal(tax_value) / 100)
        return total


@_register_invoice_field
class ValorIPIField(InvoiceFieldDescription):
    name = u"VALOR_IPI"
    category = _('Tax')
    length = 1

    def fetch(self, width, height):
        # TODO figure out what to return
        return 0


@_register_invoice_field
class ProductItemTaxField(InvoiceFieldDescription):
    name = u"PRODUCT_ITEM_TAX"
    description = _('Product item tax')
    category = _('Tax')
    length = 2
    field_type = [int]

    def fetch(self, width, height):
        for sale_item in self.sale.products:
            tax = sale_item.sellable.get_tax_constant()
            if tax and tax.tax_value:
                value = int(tax.tax_value)
            else:
                value = None
            yield value


#
# Invoice fields
#

@_register_invoice_field
class OutgoingInvoiceField(InvoiceFieldDescription):
    field_type = bool
    name = u"OUTGOING_INVOICE"
    description = _("Outgoing invoice")
    category = _("Invoice")
    length = 1

    def fetch(self, width, height):
        return isinstance(self.invoice, SaleInvoice)


@_register_invoice_field
class IncomingInvoiceField(InvoiceFieldDescription):
    field_type = bool
    name = u"INCOMING_INVOICE"
    description = _("Incoming invoice")
    category = _("Invoice")
    length = 1

    def fetch(self, width, height):
        return isinstance(self.invoice, PurchaseInvoice)


@_register_invoice_field
class OrderEmissionDateField(InvoiceFieldDescription):
    name = u"ORDER_EMISSION_DATE"
    description = _('Emission date')
    category = _("Invoice")
    length = 10

    def fetch(self, width, height):
        return self.invoice.today.strftime(self.invoice.date_format)


@_register_invoice_field
class OrderCreationDateField(InvoiceFieldDescription):
    name = u"ORDER_CREATION_DATE"
    description = _('Creation date')
    category = _("Invoice")
    length = 10

    def fetch(self, width, height):
        return self.invoice.today.strftime(self.invoice.date_format)


@_register_invoice_field
class OrderCreationTimeField(InvoiceFieldDescription):
    name = u"ORDER_CREATION_TIME"
    description = _('Creation time')
    category = _("Invoice")
    length = 8

    def fetch(self, width, height):
        return self.invoice.today.strftime('%H:%S')


@_register_invoice_field
class InvoiceNumberField(InvoiceFieldDescription):
    name = u"INVOICE_NUMBER"
    description = _(u"Invoice number")
    category = _("Invoice")
    length = 6

    def fetch(self, width, height):
        return '%09d' % self.sale.invoice_number


@_register_invoice_field
class InvoiceTypeField(InvoiceFieldDescription):
    name = u"INVOICE_TYPE"
    description = _("Invoice Type")
    category = _("Invoice")
    length = 10

    def fetch(self, width, height):
        return self.invoice.type


#
# Service fields
#

@_register_invoice_field
class ServiceItemCodeDescriptionField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_CODE_DESCRIPTION"
    description = _('Service item code / description')
    category = _("Service")
    length = 35
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            code = '%014s' % sale_item.sellable.code
            yield '%s / %s' % (
                code.replace(' ', '0'),
                sale_item.get_description())


@_register_invoice_field
class ServiceItemDescriptionField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_DESCRIPTION"
    description = _('Service item description')
    category = _("Service")
    length = 30
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            yield '%s' % sale_item.get_description()


@_register_invoice_field
class ServiceItemCodeField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_CODE"
    description = _('Service item code')
    category = _("Service")
    length = 5
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            code = '%05s' % sale_item.sellable.code
            yield code[-width:]


@_register_invoice_field
class ServiceItemCodeUnitField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_CODE_UNIT"
    description = _('Service item unit')
    category = _("Service")
    length = 2
    field_type = [str]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            yield sale_item.sellable.unit_description


@_register_invoice_field
class ServiceItemQuantityField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_QUANTITY"
    description = _('Service item quantity')
    category = _("Service")
    length = 5
    field_type = [Decimal]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            yield sale_item.quantity


@_register_invoice_field
class ServiceItemPriceField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_PRICE"
    description = _('Service item price')
    category = _("Service")
    length = 5
    field_type = [Decimal]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            yield sale_item.price


@_register_invoice_field
class ServiceItemTotalField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_TOTAL"
    description = _('Service item total (price * quantity)')
    category = _("Service")
    length = 7
    field_type = [Decimal]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            yield sale_item.get_total()


@_register_invoice_field
class ServiceItemTaxField(InvoiceFieldDescription):
    name = u"SERVICE_ITEM_TAX"
    description = _('Service item tax')
    category = _("Service")
    length = 2
    field_type = [int]

    def fetch(self, width, height):
        for sale_item in self.sale.services:
            tax = sale_item.sellable.get_tax_constant()
            if tax and tax.tax_value:
                value = int(tax.tax_value)
            else:
                value = None
            yield value


@_register_invoice_field
class ValorTotalServicosField(InvoiceFieldDescription):
    name = u"VALOR_TOTAL_SERVICOS"
    category = _("Service")
    length = 1
    field_type = Decimal

    def fetch(self, width, height):
        return sum([s.quantity * s.price for s in self.sale.services],
                   Decimal(0))


#
# Uncategorized fields
#

#@_register_invoice_field
class ValorFreteField(InvoiceFieldDescription):
    name = u"VALOR_FRETE"
    category = _("Other")
    length = 1

    def fetch(self, width, height):
        # TODO figure out what to return
        return 0


#@_register_invoice_field
class ValorSeguroField(InvoiceFieldDescription):
    name = u"VALOR_SEGURO"
    category = _("Other")
    length = 1

    def fetch(self, width, height):
        # TODO figure out what to return
        return 0


#@_register_invoice_field
class ValorDespesasField(InvoiceFieldDescription):
    name = u"VALOR_DESPESAS"
    category = _("Other")
    length = 1

    def fetch(self, width, height):
        # TODO figure out what to return
        return 0
