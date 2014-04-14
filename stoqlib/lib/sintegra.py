# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
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
from decimal import Decimal

from stoqlib.lib import latscii
latscii.register_codec()

_number_type = (int, long, Decimal)


def argtype_name(argtype):
    if argtype == _number_type:
        return 'number'
    else:
        return argtype.__name__


class SintegraError(Exception):
    pass


class SintegraFile(object):
    def __init__(self):
        self._registers = []

    def add(self, register):
        """Adds a register to the file
        :param register: a register
        :type register: :class:`SintegraRegister`
        """
        if not isinstance(register, SintegraRegister):
            raise TypeError("register must be a SintegraRegister instance")

        numbers = [f.sintegra_number for f in self._registers]
        if register.sintegra_unique:
            if register.sintegra_number in numbers:
                raise SintegraError("%s can only be added once" % (register.sintegra_number, ))
        if register.sintegra_requires:
            for number in register.sintegra_requires:
                if not number in numbers:
                    raise SintegraError("%s must be added at this point" % (number, ))

        self._registers.append(register)

    def add_header(self, cgc, estadual, company, city, state, fax, start, end):
        """Receive values to generate Sintegra Register type 10.

        :param cgc: the branch CNPJ number.
        :param estadual: the branch 'Inscrição estadual' number or ISENTO.
        :param company: the company fancy name.
        :param city: the branch city.
        :param state: the branch city state.
        :param fax: the branch fax number.
        :param start: start's date period, generally, the 1th month day.
        :type start: datetime.date
        :param end: end's date periodo, generally, the last month day.
        :type end: datetime.date
        """
        self.add(SintegraRegister10(
            cgc, estadual, company,
            city, state, fax,
            int(start.strftime('%Y%m%d')),
            int(end.strftime('%Y%m%d')),
            '331'))

    def add_complement_header(self, address, number, complement, district,
                              postal, name, phone):
        """Receive values to generate Sintegra Register type 11.

        :param address: the branch address.
        :param number: the number of the branch address.
        :param complement: the complement of the branch address.
        :param district: district of the branch address.
        :param postal: postal code number of the branch address.
        :param name: the branch manager name.
        :param phone: the branch phone number.
        """
        self.add(SintegraRegister11(
            address, number, complement, district,
            postal, name, phone))

    def add_fiscal_coupon(self, date, printerserial, printerid,
                          coupon_start, coupon_end, crz, cro, period_total,
                          total):
        """Receive values for generate 60M Sintegra Register.

        :param date: emission date of the fiscal coupon.
        :type date: datetime.date
        :param printerserial: serial number of the fiscal printer.
        :param printerid: the refered number (id) for the fiscal printer
          in a branch.
        :param coupon_start: the number in which the coupon fiscal starts.
        :param coupon_end: the number in which the fiscal coupon ends.
        :param crz: counter the number of 'Zs reduction' made by fiscal printer.
        :param cro: counter how many times the fiscal printer was restarted
          their operations.
        :param period_total: value total in a fiscal day.
        :param total: total acumulated in fiscal printer.
        """
        if not isinstance(date, datetime.date):
            raise TypeError
        idate = int(date.strftime('%Y%m%d'))
        total = int(total * 100)
        self.add(SintegraRegister60M('M', idate, printerserial, int(printerid), '2D',
                                     coupon_start, coupon_end, crz, cro,
                                     period_total * 100,
                                     total * 100))

    def add_fiscal_tax(self, date, printerserial, code, value):
        """
        Receive values for generate 60A Sintegra Register.
        :param date: emission date of the fiscal coupon.
        :type date: datetime.date
        :param printerserial: serial number of the fiscal printer.
        :param code: the tax code.
        :param value: the tax value.
        """
        self.add(SintegraRegister60A(
            'A', int(date.strftime('%Y%m%d')), printerserial,
            code,
            value * 100))

    def add_products_summarized(self, date, product_code,
                                product_quantity,
                                total_liquido_produto,
                                total_icms_base,
                                icms_aliquota):
        code = "%014s" % product_code
        product_code = code.replace(' ', '0')
        icms_aliquota = '%04d' % (icms_aliquota)
        if icms_aliquota == '0000':
            icms_aliquota = "I"
        self.add(SintegraRegister60R('R', date, product_code,
                                     product_quantity,
                                     total_liquido_produto,
                                     total_icms_base,
                                     icms_aliquota, ""))

    def add_receiving_order(self, cnpj, state_registry, receival_date,
                            state, modelo, serial, numero, cfop, emitente,
                            total, icms_base, icms_total, isenta, outras,
                            aliquota_icms, situacao):
        cfop_code = cfop.replace(".", "")
        date = int(receival_date.strftime("%Y%m%d"))
        self.add(SintegraRegister50(cnpj, str(state_registry),
                                    date,
                                    str(state), modelo, serial, numero,
                                    int(cfop_code),
                                    emitente,
                                    total * 100,
                                    icms_base * 100,
                                    icms_total * 100,
                                    isenta * 100,
                                    outras * 100,
                                    aliquota_icms * 100,
                                    situacao))

    def add_receiving_order_item(self, cnpj, modelo, serial, numero, cfop, cst,
                                 numero_item, product_code, product_quantity,
                                 valor_bruto_produto, desconto, icms_base,
                                 icms_subst_trib, ipi, icms_aliquota):
        cfop_code = cfop.replace(".", "")
        cfop_int = int(cfop_code)
        if product_code is None:
            product_code = " " * 14
        else:
            code = '%014s' % (product_code, )
            product_code = code.replace(' ', '0')
        if cst is None:
            cst = ' ' * 3
        self.add(SintegraRegister54(cnpj, modelo, serial, numero, cfop_int,
                                    cst, numero_item, product_code,
                                    product_quantity * 1000,
                                    valor_bruto_produto * 100,
                                    desconto * 100,
                                    icms_base * 100,
                                    icms_subst_trib * 100,
                                    ipi * 100,
                                    icms_aliquota * 100))

    def add_inventory_item(self, start, product_code, product_quantity,
                           total_product_value, owner_code, owner_cnpj,
                           owner_state_registry, state):
        inventory_date = int(start.strftime("%Y%m%d"))
        code = '%014s' % product_code
        product_code = code.replace(' ', '0')
        blank = ' ' * 45
        # When the actual company owns the products, the owner_cnpj and
        # owner_state_registry fields must be filled with pre-defined values.
        # See the link in #3708 for details.
        if owner_code == 1:
            owner_cnpj = 0
            owner_state_registry = ' ' * 14

        self.add(SintegraRegister74(inventory_date,
                                    product_code,
                                    product_quantity,
                                    total_product_value,
                                    owner_code,
                                    owner_cnpj,
                                    owner_state_registry,
                                    state,
                                    blank))

    def add_product(self, start, end, product_code, ncm, desc,
                    unit, aliquota_ipi, aliquota_icms,
                    reducao_icms, base_icms):
        start = int(start.strftime("%Y%m%d"))
        end = int(end.strftime("%Y%m%d"))
        product_code = '%014d' % (int(product_code))
        ncm = '%08d' % (int(ncm))

        self.add(SintegraRegister75(start, end, product_code, ncm, desc,
                                    unit, aliquota_ipi, aliquota_icms,
                                    reducao_icms, base_icms))

    def close(self):
        """Closes the file.
        This will add a couple of registers of type 90.
        """
        sums = {}
        for register in self._registers[2:]:
            number = register.sintegra_number
            if not number in sums:
                sums[number] = 1
            else:
                sums[number] += 1

        cgc = self._registers[0].cgc
        estadual = self._registers[0].estadual
        totalizers = len(sums) + 1
        for number, fsum in sorted(sums.items()):
            self.add(SintegraRegister90(cgc, estadual, number, fsum, '',
                                        totalizers))
        self.add(SintegraRegister90(cgc, estadual, 99,
                                    len(self._registers) + 1, '', totalizers))

    def write(self, filename=None, fp=None):
        """Writes out of the content of the file to a filename or fp

        :param filename: filename
        :param fp: file object, anything implementing write(data)
        """
        if filename is None and fp is None:
            raise TypeError
        if filename is not None and fp is not None:
            raise TypeError
        if fp is None:
            fp = open(filename, 'wb')

        for register in self.get_registers():
            fp.write(register.get_string())

    def get_registers(self):
        last_register = self._registers[-1]
        if (last_register.sintegra_number != 90 or
            last_register.type != 99):
            raise TypeError("You need to close the document before calling write()")
        return self._registers


class SintegraRegister(object):
    """ This is an abstract class
    The arguments depends on what is defined in the class variable
    sintegra_fields

    :cvar sintegra_number:
    :cvar sintegra_fields:
    :cvar sintegra_unique:
    :cvar sintegra_requires:
    """

    sintegra_number = 0
    sintegra_fields = None
    sintegra_unique = False
    sintegra_requires = None

    def __init__(self, *args, **kwargs):
        """ Creates a new SintegraRegister"""
        if not self.sintegra_fields:
            raise TypeError
        if not self.sintegra_number:
            raise TypeError
        if len(args) != len(self.sintegra_fields):
            raise TypeError('%s expected %d parameters but got %d' % (
                self.__class__.__name__, len(self.sintegra_fields), len(args)))

        sent_args = dict([(field[0], field[1:2])
                          for field in zip(self.sintegra_fields, args)])
        for key in kwargs:
            if key in sent_args:
                raise SintegraError("%s specified two times" % (key, ))

        total = 0
        self._values = {}
        for (name, length, argtype), arg in zip(self.sintegra_fields, args):
            if arg is None:
                pass
            elif not isinstance(arg, argtype):
                fmt = "argument %s should be of type %s but got %s"
                raise TypeError(fmt % (name, argtype_name(argtype),
                                       type(arg).__name__))
            self._values[name] = self._arg_to_string(arg, length, argtype)
            setattr(self, name, arg)
            total += length

        if total > 124:
            raise TypeError(
                "There are items with a total length of %d in %s, "
                "but only 124 is allowed" % (total, self.__class__.__name__))
        elif total < 124:
            self.padding = 124 - total
        else:
            self.padding = 0

    #
    # Public API
    #

    def get_string(self):
        """
        Gets a string for all sintegra fields.
        :returns: sintegra fields as string.
        """
        values = []
        for (name, _, _) in self.sintegra_fields:
            values.append(self._values[name])
        if self.padding:
            values.append(' ' * self.padding)
        return '%02d%s\r\n' % (self.sintegra_number,
                               ''.join(values))

    # Private

    def _arg_to_string(self, value, length, argtype):
        if value is None:
            return ' ' * length

        if argtype == _number_type:
            # If a value is higher the the maximum allowed,
            # set it to the maximum allowed value instead.
            max_value = (10 ** length) - 1
            if value > max_value:
                value = max_value
            arg = '%0*d' % (length, value)
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
        else:
            raise AssertionError

        assert len(arg) <= length, (repr(arg), length)

        return arg


class SintegraRegister10(SintegraRegister):
    sintegra_number = 10
    sintegra_fields = [
        ('cgc', 14, _number_type),
        ('estadual', 14, basestring),
        ('company', 35, basestring),
        ('city', 30, basestring),
        ('state', 2, basestring),
        ('fax', 10, _number_type),
        ('start_date', 8, _number_type),
        ('end_date', 8, _number_type),
        ('codes', 3, basestring),
        # 1: 1..3
        # 2: 1..3
        # 3: 1..3,5
    ]
    sintegra_unique = True


class SintegraRegister11(SintegraRegister):
    sintegra_number = 11
    sintegra_fields = [
        ('place', 34, basestring),
        ('number', 5, _number_type),
        ('complement', 22, basestring),
        ('dibasestringict', 15, basestring),
        ('postal', 8, _number_type),
        ('name', 28, basestring),
        ('phone', 12, _number_type),
    ]

    sintegra_requires = 10,
    sintegra_unique = True


class SintegraRegister60M(SintegraRegister):
    sintegra_number = 60
    sintegra_fields = [
        ('type', 1, basestring),
        ('date', 8, _number_type),
        ('printerserial', 20, basestring),
        ('printerid', 3, _number_type),
        ('model', 2, basestring),
        ('start_coo', 6, _number_type),
        ('end_coo', 6, _number_type),
        ('crz', 6, _number_type),
        ('cro', 3, _number_type),
        ('period_total', 16, _number_type),
        ('total', 16, _number_type),
    ]
    sintegra_requires = 10, 11


class SintegraRegister60A(SintegraRegister):
    sintegra_number = 60
    sintegra_fields = [
        ('type', 1, basestring),
        ('date', 8, _number_type),
        ('printerserial', 20, basestring),
        ('tax', 4, basestring),
        ('total', 12, _number_type),
    ]
    sintegra_requires = 10, 11


class SintegraRegister60R(SintegraRegister):
    sintegra_number = 60
    sintegra_fields = [
        ('type', 1, basestring),
        ('date', 6, _number_type),
        ('product_code', 14, basestring),
        ('product_quantity', 13, _number_type),
        ('total_liquido_produto', 16, _number_type),
        ('total_icms_base', 16, _number_type),
        ('icms_aliquota', 4, basestring),
        ('blank', 54, basestring),
    ]


class SintegraRegister50(SintegraRegister):
    sintegra_number = 50
    sintegra_fields = [
        ('cnpj', 14, _number_type),
        ('estadual', 14, basestring),
        ('date', 8, _number_type),
        ('state', 2, basestring),
        ('modelo', 2, _number_type),
        ('serial', 3, basestring),
        ('numero', 6, _number_type),
        ('cfop', 4, _number_type),
        ('emitente', 1, basestring),
        ('total', 13, _number_type),
        ('icms_base', 13, _number_type),
        ('icms_total', 13, _number_type),
        ('isenta', 13, _number_type),
        ('outras', 13, _number_type),
        ('aliquota_icms', 4, _number_type),
        ('situacao', 1, basestring),
    ]


class SintegraRegister54(SintegraRegister):
    sintegra_number = 54
    sintegra_fields = [
        ('cnpj', 14, _number_type),
        ('modelo', 2, _number_type),
        ('serial', 3, basestring),
        ('numero', 6, _number_type),
        ('cfop', 4, _number_type),
        ('cst', 3, basestring),
        ('numero_item', 3, _number_type),
        ('product_code', 14, basestring),
        ('product_quantity', 11, _number_type),
        ('valor_bruto_produto', 12, _number_type),
        ('desconto', 12, _number_type),
        ('icms_base', 12, _number_type),
        ('icms_subst_trib', 12, _number_type),
        ('ipi', 12, _number_type),
        ('icms_aliquota', 4, _number_type),
    ]


class SintegraRegister74(SintegraRegister):
    sintegra_number = 74
    sintegra_fields = [
        ('inventory_date', 8, _number_type),
        ('product_code', 14, basestring),
        ('product_quantity', 13, _number_type),
        ('total_product_value', 13, _number_type),
        # 'owner_code' accept the following values:
        # 1, Mercadorias de propriedade do Informante e em seu poder
        # 2, Mercadorias de propriedade do Informante em poder de terceiros
        # 3, Mercadorias de propriedade de terceiros em poder do Informante
        # according to the document linked in #3708
        ('owner_code', 1, _number_type),
        ('owner_cnpj', 14, _number_type),
        # The 'owner_state_registry' field must conform to the value in
        # 'owner_code' eg 'owner_state_registry' must be filled with the
        # company's data that really owns the product.
        ('owner_state_registry', 14, basestring),
        ('state', 2, basestring),
        ('blank', 45, basestring),
    ]


class SintegraRegister75(SintegraRegister):
    sintegra_number = 75
    sintegra_fields = [
        ('start_date', 8, _number_type),
        ('end_date', 8, _number_type),
        ('product_code', 14, basestring),
        ('ncm', 8, basestring),
        ('descricao', 53, basestring),
        ('unit', 6, basestring),
        ('aliquota_ipi', 5, _number_type),
        ('aliquota_icms', 4, _number_type),
        ('reducao_icms', 5, _number_type),
        ('base_icms', 13, _number_type),
    ]


class SintegraRegister90(SintegraRegister):
    sintegra_number = 90
    sintegra_fields = [
        ('cgc', 14, _number_type),
        ('estadual', 14, basestring),
        ('type', 2, _number_type),
        ('registers', 8, _number_type),
        ('blank', 85, basestring),
        ('number', 1, _number_type),
    ]
    sintegra_requires = 10, 11


def test():  # pragma nocover
    s = SintegraFile()
    cgc = int('03852995000107')
    estadual = '110042490114'
    s.add(SintegraRegister10(
        cgc, estadual, 'TESTES E TESTES LTDA',
        'CANDEIAS', 'SP', int('0710802316'),
        20070401, 20070430, '331'))
    s.add(SintegraRegister11(
        'RODOVIA BA 000 KM 00', 12, ',CX',
        'POSTAL 60', 43800000, 'EDSON / PEDRO',
        int('07100000000')))
    s.add_fiscal_coupon(datetime.date(2007, 4, 1),
                        '12345678901234567890', 1,
                        1, 10, 1, 1, 100, 1000)
    s.close()
    s.write('/tmp/sintegra-dos.txt')

if __name__ == '__main__':  # pragma nocover
    test()
