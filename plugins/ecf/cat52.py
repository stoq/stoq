# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source
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

import datetime
from hashlib import md5
import operator

from kiwi.datatypes import number, filter_locale
from stoqdrivers.enum import TaxType
from stoqlib.lib import latscii

latscii.register_codec()

from ecfdomain import ECFDocumentHistory


def _argtype_name(argtype):
    if argtype == number:
        return 'number'
    else:
        return argtype.__name__

# See http://www.fazenda.sp.gov.br/publicacao/noticia.aspx?id=571
# for a complete list of this:

BRAND_CODES = {
    'daruma': 'DR',
    'bematech': 'BE',
}

MODEL_CODES = {
    ('daruma', 'FS345'): 4,
    ('bematech', 'MP25'): 1,
    ('bematech', 'MP2100'): 'E',
}

BRAND_FULL_NAME = {
    'daruma': 'DARUMA AUTOMACAO',
    'bematech': 'BEMATECH',
}

MODEL_FULL_NAME = {
    ('daruma', 'FS345'): 'FS-345',
    ('bematech', 'MP25'): 'MP-20 FI',
    ('bematech', 'MP2100'): 'MP-2100 TH FI',
}

DOCUMENT_TYPES = {
    ECFDocumentHistory.TYPE_MEMORY_READ: 'MF',
    ECFDocumentHistory.TYPE_Z_REDUCTION: 'RZ',
    ECFDocumentHistory.TYPE_SUMMARY: 'LX',
}


class CATError(Exception):
    pass


class CATFile(object):
    def __init__(self, printer):
        self._registers = []
        self.printer = printer
        self.software_version = None
        self.brand = BRAND_FULL_NAME[self.printer.brand]
        self.model = MODEL_FULL_NAME[(self.printer.brand, self.printer.model)]
        self._tax_counter = 1

    def add(self, register):
        """Add register to the file.
        @param register: a register
        @type register: L{CATRegister}
        """
        self._registers.append(register)

    # E00
    def add_software_house(self, soft_house, software_name, software_version):
        """
        @param soft_house: Information from the software house: cnpj,
          ie, im, name
        @param software_name: Name of the software
        @param software_version: Version of the software

        Acording to the cat52/07, coo, software_number, line01 and
        line02 should be filled with blanks
        """
        self.add(CATRegisterE00(serial_number=self.printer.device_serial,
                                additional_mf="",
                                user_number=self.printer.user_number,
                                ecf_type='ECF-IF',
                                ecf_brand=self.brand,
                                ecf_model=self.model,
                                coo=0,
                                software_number=0,
                                cnpj=soft_house.cnpj,
                                ie=soft_house.ie,
                                im=soft_house.im,
                                soft_house=soft_house.name,
                                soft_name=software_name,
                                soft_version=(self.software_version or
                                              software_version),
                                line01=" ",
                                line02=" "))

    # E01
    def add_ecf_identification(self, driver, company, initial_crz,
                               final_crz, start, end):
        """
        @param driver:
        @type driver:
        @param initial_crz:
        @param final_crz:
        @param company:
        @type company: PersonAdaptToCompany

        """
        today = datetime.datetime.today()
        self.add(CATRegisterE01(serial_number=self.printer.device_serial,
                                # VERIFY
                                additional_mf='',
                                ecf_type="ECF-IF",
                                ecf_brand=self.brand,
                                ecf_model=self.model,
                                ecf_sb_version=driver.get_firmware_version(),
                                ecf_sb_date=today.date(),
                                ecf_sb_hour=today.time(),
                                # VERIFY
                                ecf_number=self.printer.id,
                                user_cnpj=company.get_cnpj_number(),
                                # Application
                                command="APL",
                                initial_crz=initial_crz,
                                final_crz=final_crz,
                                initial_date=start,
                                final_date=end,
                                library_version='00.00.00',
                                cotepe="AC1704 01.00.00"))

    # E02
    def add_ecf_user_identification(self, company, total):
        """
        @param company:
        @param total:
        """
        full_address = (company.person.address.get_address_string() + ' ' +
                        company.person.address.get_details_string())
        self.add(CATRegisterE02(serial_number=self.printer.device_serial,
                                additional_mf='',
                                ecf_model=self.model,
                                user_cnpj=company.get_cnpj_number(),
                                user_ie=company.get_state_registry_number(),
                                user_name=company.person.name,
                                user_address=full_address,
                                register_date=self.printer.register_date.date(),
                                register_hour=self.printer.register_date.time(),
                                cro=self.printer.register_cro,
                                total=int(total * 100), # 2 decimal positions
                                user_number=self.printer.user_number,
                                ))

    # E12
    def add_z_reduction(self, reduction):
        self.add(CATRegisterE12(serial_number=self.printer.device_serial,
                                additional_mf='',
                                ecf_model=self.model,
                                user_number=self.printer.user_number,
                                crz=reduction.crz,
                                coo=reduction.coupon_end,
                                cro=reduction.cro,
                                moviment_date=reduction.emission_date,
                                reduction_date=reduction.reduction_date.date(),
                                reduction_time=reduction.reduction_date.time(),
                                total=int(reduction.period_total * 100),
                                issqn_discount=False))

    # E13
    def add_z_reduction_details(self, reduction, tax, index):
        # XXX: the totalizer index is quite confusing

        # Before paulista invoice, we didn't store the ISS value!
        # Ignore this as it doesn't have the expected values
        if tax.value == 'ISS':
            return

        totalizer = ''
        if all(c.isdigit() for c in tax.code):
            type = 'T'
            if tax.type == 'ISS':
                type = 'S'

            totalizer = '%0*d%s%s' % (2, index, type, tax.code)

        elif tax.code[0] in 'INF':
            type = ''
            if tax.type == 'ISS':
                type = 'S'

            totalizer = '%s%d' % (tax.code[0], index)

        else:
            type = 'T'
            if tax.type == 'ISS':
                type = 'S'

            if tax.code == 'DESC':
                totalizer = 'D%s' % type
            elif tax.code == 'ACRE':
                totalizer = 'A%s' % type
            elif tax.code == 'CANC':
                totalizer = 'Can-%s' % type

        self.add(CATRegisterE13(serial_number=self.printer.device_serial,
                                additional_mf='',
                                ecf_model=self.model,
                                user_number=self.printer.user_number,
                                crz=reduction.crz,
                                partial_totalizer=totalizer,
                                value=tax.value,
                                ))

    # E14
    def add_fiscal_coupon(self, sale, client, fiscal_data):
        subtotal = (sale.total_amount -
                    sale.surcharge_value +
                    sale.discount_value)
        client_name = ''
        if client:
            client_name = client.person.name

        cpf_cnpj = 0
        if fiscal_data.document:
            cpf_cnpj = int(''.join([c for c in fiscal_data.document
                                          if c.isdigit()]))

        self.add(CATRegisterE14(serial_number=self.printer.device_serial,
                                additional_mf='',
                                ecf_model=self.model,
                                user_number=self.printer.user_number,
                                document_counter=fiscal_data.document_counter,
                                coo=fiscal_data.coo,
                                emission_start=sale.confirm_date,
                                subtotal=subtotal,
                                discount=sale.discount_value,
                                discount_type='V',                  # Value
                                surcharge=sale.surcharge_value,
                                surcharge_type='V',                 # Value
                                total=sale.total_amount,
                                canceled=False,                     # !!!
                                surcharge_canceled=0,
                                #stoqlib/domain/sale.py:489
                                discount_surcharge_order='A',
                                client_name=client_name,
                                client_cpf_cnpj=cpf_cnpj,
        ))

    # E15
    def add_fiscal_coupon_details(self, sale, client, fiscal_data,
                                  item, iss_tax, sequence):
        tax = item.sellable.get_tax_constant()
        partial_totalizer = ''
        if tax.tax_type == TaxType.SERVICE:         # ISS
            partial_totalizer = '01S%0*d' % (4, iss_tax)
        elif tax.tax_type == TaxType.NONE:          # Não tributado
            partial_totalizer = 'N1'
        elif tax.tax_type == TaxType.EXEMPTION:     # Isento
            partial_totalizer = 'I1'
        elif tax.tax_type == TaxType.SUBSTITUTION:  # Substi. Tribut.
            partial_totalizer = 'F1'
        elif tax.tax_type == TaxType.CUSTOM:
            partial_totalizer = '%0*dT%0*d' % (2, self._tax_counter, 4,
                                               tax.tax_value * 100)
            self._tax_counter += 1

        self.add(CATRegisterE15(
            serial_number=self.printer.device_serial,
            additional_mf='',
            ecf_model=self.model,
            user_number=self.printer.user_number,
            coo=fiscal_data.coo,
            document_counter=fiscal_data.document_counter,
            item_number=sequence,
            item_code=item.sellable.code,
            item_description=item.get_description(),
            # precision = 2
            item_amount=item.quantity * 100,
            item_unit=(item.sellable.get_unit_description() or 'un'),
            item_unitary_value=item.price * 100,
            # We don't offer discount,
            item_discount=0,
            # or surcharge for items,
            item_surcharge=0,
            # only for the subtotal
            # precison = 2
            item_total=item.price * item.quantity * 100,
            item_partial_totalizer=partial_totalizer,

            # Stoq does not store
            item_canceled='N',
            # canceled items
            item_canceled_amount=0,
            item_canceled_value=0,
            item_canceled_surcharge=0,
            round_or_trunc='A',                 # !!! A ou T
            amount_decimal_precision=2,         # !!!
            value_decimal_precision=2,          # !!!
        ))

    # E21
    def add_payment_method(self, sale, fiscal_data,
                           payment, renegotiation=None):
        returned = 'N'
        returned_value = 0
        if sale.return_date:
            returned = 'S'
            returned_value = renegotiation.paid_total
            if renegotiation.penalty_value:
                returned = 'P'
                returned_value -= renegotiation.penalty_value

        self.add(CATRegisterE21(
            serial_number=self.printer.device_serial,
            additional_mf='',
            ecf_model=self.model,
            user_number=self.printer.user_number,
            coo=fiscal_data.coo,
            document_counter=fiscal_data.document_counter,
            gnf=0,
            payment_method=payment.method.get_description(),
            value=payment.value * 100,
            returned=returned,                      # S/N/P
            returned_value=returned_value * 100,    # Only if P
            ))

    # E16
    def add_other_document(self, document):
        self.add(CATRegisterE16(serial_number=self.printer.device_serial,
                                additional_mf='',
                                ecf_model=self.model,
                                user_number=self.printer.user_number,
                                coo=document.coo,
                                gnf=document.gnf,
                                grg=0,
                                cdc=0,
                                crz=document.crz or 0,
                                denomination=DOCUMENT_TYPES[document.type],
                                emission_date=document.emission_date.date(),
                                emission_hour=document.emission_date.time()))

    def write(self, filename=None, fp=None):
        """Writes out of the content of the file to a filename or fp

        @param filename: filename
        @param fp: file object, anything implementing write(data)
        """
        if filename is None and fp is None:
            raise TypeError
        if filename is not None and fp is not None:
            raise TypeError
        if fp is None:
            fp = open(filename, 'w')

        self._registers.sort(key=operator.attrgetter('register_type'))

        data = ''
        for register in self._registers:
            data += register.get_string()

        md5sum = md5(data).hexdigest()
        ead = "EAD%s\r\n" % md5sum

        fp.write(data.encode('latin1'))
        fp.write(ead.encode('latin1'))
        fp.close()


class CATRegister(object):
    register_type = None
    register_fields = None

    def __init__(self, *args, **kwargs):
        if not self.register_fields:
            raise TypeError
        if not self.register_type:
            raise TypeError
        if len(kwargs) != len(self.register_fields):
            raise TypeError('%s expected %d parameters but got %d' % (
                self.__class__.__name__, len(self.register_fields),
                                             len(kwargs)))

        sent_args = dict([(field[0], field[1:2])
                          for field in zip(self.register_fields,
                                           kwargs.values())])
        for key in kwargs:
            if key in sent_args:
                raise CATRegister("%s specified two times" % (key, ))

        self._values = {}
        for (name, length, argtype) in self.register_fields:
            if kwargs[name] == "":
                pass
            elif not isinstance(kwargs[name], argtype):
                raise TypeError(
                    "argument %s should be of type %s but got %s" % (
                    name, _argtype_name(argtype), type(kwargs[name]).__name__))
            self._values[name] = self._arg_to_string(kwargs[name], length,
                                                     argtype)
            setattr(self, name, kwargs[name])

    #
    # Public API
    #

    def get_string(self):
        """
        @returns:
        """
        values = []
        for (name, a, b) in self.register_fields:
            values.append(self._values[name])
        return '%s%s\r\n' % (self.register_type,
                              ''.join(values))
    #
    # Private
    #

    def _arg_to_string(self, value, length, argtype):
        if value == "":
            return ' ' * length

        if argtype == number:
            # If a value is higher the the maximum allowed,
            # set it to the maximum allowed value instead.
            max_value = (10 ** length) - 1
            if value > max_value:
                value = max_value

            # Remove locale specific marks and replace the decimal digit dot.
            str_value = filter_locale(str(value))
            # Return to int again, so in the formatting we add the correct
            # numbers of zeros.
            re_value = int(str_value.replace('.', ''))

            arg = '%0*d' % (length, re_value)
        elif argtype == basestring:
            # Accept normal strings, which are assumed to be UTF-8
            if type(value) == str:
                value = unicode(value, 'utf-8')

            # Convert to latscii
            value = value.encode('ascii', 'replacelatscii')

            arg = '%-*s' % (length, value)
            # Chop strings which are too long
            if len(arg) > length:
                arg = arg[:length]
        elif argtype == datetime.date:
            # YYYYMMDD
            arg = value.strftime("%Y%m%d")
        elif argtype == datetime.time:
            # HHMM
            arg = value.strftime("%H%M%S")
        elif argtype == bool:
            arg = 'N'
            if value:
                arg = 'S'
        else:
            raise TypeError
        assert len(arg) <= length
        return arg


class CATRegisterE00(CATRegister):
    """Register E00 - Software House Identification
    """

    register_type = "E00"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('user_number', 2, number),
        ('ecf_type', 7, basestring),
        ('ecf_brand', 20, basestring),
        ('ecf_model', 20, basestring),
        ('coo', 6, number),
        ('software_number', 2, number),
        ('cnpj', 14, number),
        ('ie', 14, number),
        ('im', 14, number),
        ('soft_house', 40, basestring),
        ('soft_name', 40, basestring),
        ('soft_version', 10, basestring),
        ('line01', 42, basestring),
        ('line02', 42, basestring),
        ]


class CATRegisterE01(CATRegister):
    """Register E01 - ECF Identification
    """
    register_type = "E01"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_type', 7, basestring),
        ('ecf_brand', 20, basestring),
        ('ecf_model', 20, basestring),
        ('ecf_sb_version', 10, basestring),
        ('ecf_sb_date', 8, datetime.date),
        ('ecf_sb_hour', 6, datetime.time),
        ('ecf_number', 3, number),
        ('user_cnpj', 14, number),
        ('command', 3, basestring),
        ('initial_crz', 6, number),
        ('final_crz', 6, number),
        ('initial_date', 8, datetime.date),
        ('final_date', 8, datetime.date),
        ('library_version', 8, basestring),
        ('cotepe', 15, basestring),
        ]


class CATRegisterE02(CATRegister):
    """Register E02 - ECF User Identification
    """
    register_type = "E02"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_model', 20, basestring),
        ('user_cnpj', 14, number),
        # XXX: This should be number, but acording to cat52, it is
        # string ?!?
        ('user_ie', 14, number),

        ('user_name', 40, basestring),
        ('user_address', 120, basestring),
        ('register_date', 8, datetime.date),
        ('register_hour', 6, datetime.time),
        ('cro', 6, number),
        ('total', 18, number),
        ('user_number', 2, number),
        ]


class CATRegisterE12(CATRegister):
    """Register E12 - Z reduction list
    """
    register_type = "E12"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_model', 20, basestring),
        ('user_number', 2, number),
        ('crz', 6, number),
        ('coo', 6, number),
        ('cro', 6, number),
        ('moviment_date', 8, datetime.date),
        ('reduction_date', 8, datetime.date),
        ('reduction_time', 6, datetime.time),
        ('total', 14, number),
        ('issqn_discount', 1, bool),            # False, right now
        ]


class CATRegisterE13(CATRegister):
    """Register E13 - Z reduction details list
    """
    register_type = "E13"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_model', 20, basestring),
        ('user_number', 2, number),
        ('crz', 6, number),
        ('partial_totalizer', 7, basestring),   # See table 6.5.1.2
        ('value', 13, number),                  # currency
        ]


class CATRegisterE14(CATRegister):
    """Register E14 - Fiscal Coupon/Fiscal Invoice list
    """
    register_type = "E14"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_model', 20, basestring),
        ('user_number', 2, number),
        ('document_counter', 6, number),        # See documentation
        ('coo', 6, number),
        ('emission_start', 8, datetime.date),
        ('subtotal', 14, number),               # currency
        ('discount', 13, number),               # $ or %
        ('discount_type', 1, basestring),       # V = $ / P = %
        ('surcharge', 13, number),
        ('surcharge_type', 1, basestring),      # V = $ / P = %
        # Total after discount and surcharge
        ('total', 14, number),
        # If the document was canceled
        ('canceled', 1, bool),
        # surcharge canceled value
        ('surcharge_canceled', 13, number),
        # The order that the discount
        # and surchage were applied:
        # 'D' if discount came first or 'A'
        # otherwise
        ('discount_surcharge_order', 1, basestring),
        ('client_name', 40, basestring),
        # cpf or cnpj, depending on the client
        ('client_cpf_cnpj', 14, number),
        ]


class CATRegisterE15(CATRegister):
    """Register E15 - Fiscal Coupon/Fiscal Invoice details list
    """
    register_type = "E15"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_model', 20, basestring),
        ('user_number', 2, number),
        ('coo', 6, number),
        ('document_counter', 6, number),        # See documentation

        ('item_number', 3, number),
        ('item_code', 14, basestring),
        ('item_description', 100, basestring),
        ('item_amount', 7, number),
        ('item_unit', 3, basestring),
        ('item_unitary_value', 8, number),
        ('item_discount', 8, number),
        ('item_surcharge', 8, number),
        ('item_total', 14, number),
        # See table 6.5.1.2. !!!
        ('item_partial_totalizer', 7, basestring),
        # S - yes / N - no / P - partial
        ('item_canceled', 1, basestring),
        # Only if partial cancelment
        ('item_canceled_amount', 7, number),
        # idem
        ('item_canceled_value', 13, number),
        # currency
        ('item_canceled_surcharge', 13, number),
        # A - round / T - trunc
        ('round_or_trunc', 1, basestring),
        # Number of decimal precision for the amount
        ('amount_decimal_precision', 1, number),
        # Number of decimal precision for the unitary
        # value
        ('value_decimal_precision', 1, number),
    ]


class CATRegisterE16(CATRegister):
    """Register E16 - Other documents
    """
    register_type = "E16"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_model', 20, basestring),
        ('user_number', 2, number),
        ('coo', 6, number),
        ('gnf', 6, number),        # See documentation
        ('grg', 6, number),
        ('cdc', 4, number),
        ('crz', 6, number),
        ('denomination', 2, basestring), # See table
        ('emission_date', 8, datetime.date),
        ('emission_hour', 6, datetime.time),
        ]


class CATRegisterE21(CATRegister):
    """Register E21 - Fiscal Coupon and Non-fiscal document - payment methods
    """
    register_type = "E21"
    register_fields = [
        ('serial_number', 20, basestring),
        ('additional_mf', 1, basestring),
        ('ecf_model', 20, basestring),
        ('user_number', 2, number),
        ('coo', 6, number),
        # ccf
        ('document_counter', 6, number),
        # See documentation - not appliable to stoq right now.
        ('gnf', 6, number),
        ('payment_method', 15, basestring),
        ('value', 13, number),
        # S/N/P
        ('returned', 1, basestring),
        ('returned_value', 13, number),
    ]


class CATRegisterEAD(CATRegister):
    """Register EAD - Digital Signature
    """
    register_type = "EAD"
    register_fields = [
        ('digital_signature', 256, basestring)
    ]
