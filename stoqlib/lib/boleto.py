# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011-2017 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Boleto generation code.

"""

import datetime
import logging

from kiwi.environ import environ
from kiwi.currency import currency
from kiwi.datatypes import converter

from stoqlib.lib.algorithms import (modulo10,
                                    modulo11,
                                    calculaDuploDigito)
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.cnab.bb import BBCnab
from stoqlib.lib.cnab.bradesco import BradescoCnab
from stoqlib.lib.cnab.caixa import CaixaCnab
from stoqlib.lib.cnab.itau import ItauCnab
from stoqlib.lib.cnab.santander import SantanderCnab
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = logging.getLogger(__name__)


(BILL_OPTION_BANK_BRANCH,
 BILL_OPTION_BANK_ACCOUNT,
 BILL_OPTION_CUSTOM) = range(3)


class BoletoException(Exception):
    pass


def custom_property(name, num_length):
    """Function to create properties on boleto

    It accepts a number with or without a DV and zerofills it
    """
    internal_attr = '_%s' % name

    def _set_attr(self, val):
        val = val.split('-')

        if len(val) is 1:
            val[0] = str(val[0]).zfill(num_length)
            setattr(self, internal_attr, val[0])
        elif len(val) is 2:
            val[0] = str(val[0]).zfill(num_length)
            setattr(self, internal_attr, '-'.join(val))
        else:
            raise BoletoException(_('Wrong value format'))

    return property(
        lambda self: getattr(self, internal_attr),
        _set_attr,
        lambda self: delattr(self, internal_attr),
        name
    )


class BankInfo(object):
    """Base class for generating bill information

    For each bank, a subclass of this should be created defining how the value
    is formatted for the bill.
    """

    aceite = 'N'
    especie = "R$"
    moeda = "9"
    local_pagamento = "Pagável em qualquer banco até o vencimento"

    # This 2 values are usually empty in the printed bill
    quantidade = None
    valor = None

    # Override in base class
    description = None
    bank_name = None
    bank_number = None
    options = {}
    logo = ''

    validate_field_func = None
    validate_field_dv = None

    nosso_numero = custom_property('nosso_numero', 13)
    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 7)

    def __init__(self, payment):
        self.payment = payment
        self.payer = payment.group.payer
        self.branch = payment.branch
        self.bank = payment.method.destination_account.bank
        self.data_processamento = localtoday()

        props = self.get_properties(payment)
        for key, value in props.items():
            setattr(self, key, value)

        self.logo_image_path = ""
        if self.logo:
            self.logo_image_path = environ.get_resource_filename(
                'stoq', 'pixmaps', self.logo)

    def get_properties(self, payment):
        """Get values necesary for bill emission.

        This includes nosso numero, bank agency and bank account.

        Also, any other custom options that the bank require will be present
        here.
        """
        props = dict(
            nosso_numero=str(int(payment.identifier)),
            agencia=self.bank.bank_branch,
            conta=self.bank.bank_account)
        for opt in self.bank.options:
            props[opt.option] = opt.value

        return props

    #
    # Properties
    #

    @property
    def numero_documento(self):
        payment = self.payment
        sale = payment.group.sale
        if sale:
            return sale.invoice.invoice_number
        else:
            return payment.identifier

    @property
    def instrucoes(self):
        instructions = []
        payment = self.payment
        penalty = currency(
            (sysparam.get_decimal('BILL_PENALTY') / 100) * payment.value)
        interest = currency(
            (sysparam.get_decimal('BILL_INTEREST') / 100) * payment.value)
        discount = currency(
            (sysparam.get_decimal('BILL_DISCOUNT') / 100) * payment.value)
        data = sysparam.get_string('BILL_INSTRUCTIONS')
        for line in data.split('\n')[:4]:
            line = line.replace('$DATE', payment.due_date.strftime('%d/%m/%Y'))
            line = line.replace('$PENALTY',
                                converter.as_string(currency, penalty))
            line = line.replace('$INTEREST',
                                converter.as_string(currency, interest))
            line = line.replace('$DISCOUNT',
                                converter.as_string(currency, discount))
            line = line.replace('$INVOICE_NUMBER', str(self.numero_documento))
            instructions.append(line)

        # FIXME: Only add this if not a stoq.link subscriber
        #instructions.append('')
        #instructions.append('\n' + _('Stoq Retail Management') + ' - www.stoq.com.br')
        return instructions

    @property
    def demonstrativo(self):
        payment = self.payment
        demonstrativo = [payment.group.get_description().capitalize()]
        sale = payment.group.sale
        if sale:
            for item in sale.get_items():
                demonstrativo.append(' - %s' % item.get_description())
        return demonstrativo

    @property
    def campo_livre(self):  # pragma no cover
        raise NotImplementedError

    @property
    def barcode(self):
        num = "%03d%1s%1s%4s%10s%25s" % (
            self.bank_number,
            self.moeda,
            'X',
            self.fator_vencimento,
            self.formata_valor(self.payment.value, 10),
            self.campo_livre
        )

        dv = self.calculate_dv_barcode(num.replace('X', '', 1))

        num = num.replace('X', str(dv), 1)
        if len(num) != 44:
            raise BoletoException(
                _('The barcode must have 44 caracteres, found %d') % len(num))
        return num

    @property
    def dv_nosso_numero(self):  # pragma no cover
        """Returns nosso número DV

        It should be implemented by derived class
        """
        raise NotImplementedError

    @property
    def dv_agencia(self):
        if '-' in self.agencia:
            return self.agencia.split('-')[1]
        else:
            return ''

    @property
    def dv_conta(self):
        if '-' in self.conta:
            return self.conta.split('-')[1]
        else:
            return ''

    @property
    def dv_agencia_conta(self):
        """Verifier digit for agency and account

        Some banks don't require this. The ones that does, should override this
        method
        """
        return ''

    def calculate_dv_barcode(self, line):
        resto2 = modulo11(line, 9, 1)
        if resto2 in [0, 1, 10]:
            dv = 1
        else:
            dv = 11 - resto2
        return dv

    def format_nosso_numero(self):
        """Return Formatted Nosso Número for bill printing

        It should be implemented by derived class
        """
        return self.nosso_numero

    @property
    def fator_vencimento(self):
        date_ref = datetime.date(2000, 7, 3)  # Fator = 1000
        delta = self.payment.due_date.date() - date_ref
        return delta.days + 1000

    @property
    def agencia_conta(self):
        return "%s/%s" % (self.agencia, self.conta)

    @property
    def codigo_dv_banco(self):
        num = '%03d' % (self.bank_number, )
        cod = "%s-%s" % (num, modulo11(num))
        return cod

    @property
    def linha_digitavel(self):
        """Linha que o cliente pode utilizar para digitar se o código
            de barras não puder ser lido

        Posição    Conteúdo
        1 a 3    Número do banco
        4        Código da Moeda - 9 para Real
        5        Digito verificador do Código de Barras
        6 a 19   Valor (12 inteiros e 2 decimais)
        20 a 44  Campo Livre definido por cada banco
        """
        linha = self.barcode
        assert linha, "Boleto doesn't have a barcode"

        def monta_campo(campo):
            campo_dv = "%s%s" % (campo, modulo10(campo))
            return "%s.%s" % (campo_dv[0:5], campo_dv[5:])

        campo1 = monta_campo(linha[0:4] + linha[19:24])
        campo2 = monta_campo(linha[24:34])
        campo3 = monta_campo(linha[34:44])
        campo4 = linha[4]
        campo5 = linha[5:19]

        return "%s %s %s %s %s" % (campo1, campo2, campo3, campo4, campo5)

    #
    # Class Methods
    #

    @classmethod
    def get_cnab(cls, payments):
        branch = payments[0].branch
        bank = payments[0].method.destination_account.bank
        info = cls(payments[0])

        cnab = cls.cnab_class(branch, bank, info)
        cnab.add_record(cnab.FileHeader)
        cnab.add_record(cnab.BatchHeader)
        for i, payment in enumerate(payments):
            info = cls(payment)
            cnab.add_record(cnab.RecordP, payment, info, registry_sequence=3 * i + 1)
            cnab.add_record(cnab.RecordQ, payment, info, registry_sequence=3 * i + 2)
            cnab.add_record(cnab.RecordR, payment, info, registry_sequence=3 * i + 3)

        cnab.add_record(cnab.BatchTrailer)
        cnab.add_record(cnab.FileTrailer)
        return cnab.as_string()

    @classmethod
    def get_extra_options(cls):
        rv = []
        for option, kind in cls.options.items():
            if kind == BILL_OPTION_CUSTOM:
                rv.append(option)
        return rv

    @classmethod
    def validate_field(cls, field):
        if ' ' in field:
            raise BoletoException(_('The field cannot have spaces'))
        if '.' in field or ',' in field:
            raise BoletoException(_('The field cannot have dots of commas'))
        dv = None
        if '-' in field:
            if field.count('-') != 1:
                raise BoletoException(_('More than one hyphen found'))
            field, dv = field.split('-', 1)
            if not dv:
                raise BoletoException(_('Verifier digit cannot be empty'))
        try:
            int(field)
        except ValueError:
            raise BoletoException(_('Account needs to be a number'))

        if dv and cls.validate_field_dv is not None:
            func = cls.validate_field_func
            if func == 'modulo11':
                ret = modulo11(field)
            elif func == 'modulo10':
                ret = modulo10(field)
            else:
                ret = None

            if dv.lower() in [cls.validate_field_dv]:
                # FIXME: Is it correct that the rest of 0 is
                #        the same as 10?
                if ret == 0:
                    pass
                elif (ret is not None and
                      str(ret) != dv.lower() and
                      ret < 10):
                    raise BoletoException(_('Invalid verifier digit'))
            else:
                try:
                    dv = int(dv)
                except ValueError:
                    raise BoletoException(
                        _('Verifier digit must be a number or %s') %
                        cls.validate_field_dv)

                if ret is not None and ret != dv:
                    raise BoletoException(_('Invalid verifier digit'))

    @classmethod
    def validate_option(cls, option, value):  # pragma no cover
        pass

    @staticmethod
    def formata_numero(numero, tamanho):
        if len(numero) > tamanho:
            raise BoletoException(
                _('Number length must be less than %s') % tamanho)
        return numero.zfill(tamanho)

    @staticmethod
    def formata_valor(value, tamanho):
        txt = "%.2f" % value
        txt = txt.replace('.', '')
        txt = BankInfo.formata_numero(txt, tamanho)
        return txt


_banks = []


def register_bank(bank_class):
    if not issubclass(bank_class, BankInfo):  # pragma no cover
        raise TypeError
    assert not bank_class in _banks
    _banks.append(bank_class)
    return bank_class


@register_bank
class BankBanrisul(BankInfo):
    description = 'Banrisul'
    bank_number = 41
    logo = 'logo_banrisul.jpg'
    options = {u'agencia': BILL_OPTION_BANK_BRANCH,
               u'conta': BILL_OPTION_BANK_BRANCH,
               u'especie_documento': BILL_OPTION_CUSTOM}

    nosso_numero = custom_property('nosso_numero', 8)
    conta = custom_property('conta', 6)

    @property
    def campo_livre(self):
        content = '21%04d%07d%08d40' % (int(self.agencia),
                                        int(self.conta),
                                        int(self.nosso_numero))
        dv = calculaDuploDigito(content)
        return '%s%s' % (content, dv)


@register_bank
class BankBradesco(BankInfo):
    description = 'Bradesco'
    bank_name = 'BRADESCO'
    cnab_class = BradescoCnab
    bank_number = 237
    logo = "logo_bancobradesco.jpg"

    options = {u'carteira': BILL_OPTION_CUSTOM,
               u'especie_documento': BILL_OPTION_CUSTOM,
               u'convenio': BILL_OPTION_CUSTOM,
               u'identificacao_produto': BILL_OPTION_CUSTOM,
               u'agencia': BILL_OPTION_BANK_BRANCH,
               u'conta': BILL_OPTION_BANK_BRANCH}

    validate_field_func = 'modulo11'
    validate_field_dv = '0'

    # Nosso numero (sem dv) sao 11 digitos
    nosso_numero = custom_property('nosso_numero', 11)
    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 7)

    def format_nosso_numero(self):
        return "%s/%s-%s" % (
            self.carteira,
            self.nosso_numero,
            self.dv_nosso_numero
        )

    @property
    def dv_nosso_numero(self):
        resto2 = modulo11(self.nosso_numero, 7, 1)
        digito = 11 - resto2
        if digito == 10:
            dv = 'P'
        elif digito == 11:
            dv = 0
        else:
            dv = digito
        return dv

    @property
    def campo_livre(self):
        return "%04d%02d%11s%07d0" % (int(self.agencia.split('-')[0]),
                                      int(self.carteira),
                                      self.nosso_numero,
                                      int(self.conta.split('-')[0]))

    @classmethod
    def validate_option(cls, option, value):
        if option == 'carteira':
            if value == '':
                # TRANSLATORS: Do not translate 'Carteira'
                raise BoletoException(_("Carteira cannot be empty"))
            try:
                value = int(value)
            except ValueError:
                # TRANSLATORS: Do not translate 'Carteira'
                raise BoletoException(_("Carteira must be a number"))
            if 0 > value:
                raise BoletoException(
                    # TRANSLATORS: Do not translate 'Carteira'
                    _("Carteira must be a number between 0 and 99"))
            if value > 99:
                raise BoletoException(
                    # TRANSLATORS: Do not translate 'Carteira'
                    _("Carteira must be a number between 0 and 99"))


@register_bank
class BankBB(BankInfo):
    description = 'Banco do Brasil'
    bank_number = 1
    bank_name = 'BANCO DO BRASIL'
    logo = 'logo_bb.gif'
    options = {u'convenio': BILL_OPTION_CUSTOM,
               u'agencia': BILL_OPTION_BANK_BRANCH,
               u'conta': BILL_OPTION_BANK_BRANCH,
               u'especie_documento': BILL_OPTION_CUSTOM}

    validate_field_func = 'modulo11'
    validate_field_dv = 'x'

    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 8)
    cnab_class = BBCnab

    def get_properties(self, payment):
        props = super(BankBB, self).get_properties(payment)

        if not 'carteira' in props:
            props['carteira'] = '18'

        convenio = props.pop('convenio', None)
        if convenio:
            self.len_convenio = len(convenio)
            self.convenio = convenio
        else:
            self.len_convenio = 7
            self.convenio = ''

        self.format_nnumero = 1
        if 'format_nnumero' in props:
            self.format_nnumero = int(props.pop('format_nnumero'))
        props['agencia'] = props['agencia'].split('-')[0]
        props['conta'] = props['conta'].split('-')[0]
        return props

    def format_nosso_numero(self):
        return "%s-%s" % (
            self.nosso_numero,
            self.dv_nosso_numero
        )

    # Nosso numero (sem dv) sao 11 digitos

    @property
    def nosso_numero(self):
        return self.convenio + self._nosso_numero

    @nosso_numero.setter
    def nosso_numero(self, val):
        val = str(val)
        if self.len_convenio == 4:
            nn = val.zfill(7)
        if self.len_convenio == 6:
            if self.format_nnumero == 1:
                nn = val.zfill(5)
            elif self.format_nnumero == 2:
                nn = val.zfill(17)
        elif self.len_convenio == 7:
            nn = val.zfill(10)
        elif self.len_convenio == 8:
            nn = val.zfill(9)
        self._nosso_numero = nn

    @property
    def convenio(self):
        return self._convenio

    @convenio.setter
    def convenio(self, val):
        self._convenio = str(val).ljust(self.len_convenio, '0')

    @property
    def agencia_conta(self):
        return "%s-%s / %s-%s" % (
            self.agencia,
            modulo11(self.agencia),
            self.conta,
            modulo11(self.conta)
        )

    @property
    def dv_nosso_numero(self):
        return modulo11(self.nosso_numero)

    @property
    def campo_livre(self):
        if self.len_convenio in (7, 8):
            return "%6s%s%s" % ('000000',
                                self.nosso_numero,
                                self.carteira)
        elif self.len_convenio is 6:
            if self.format_nnumero is 1:
                return "%s%s%s%s" % (self.nosso_numero,
                                     self.agencia,
                                     self.conta,
                                     self.carteira)
            if self.format_nnumero is 2:
                return "%s%2s" % (self.nosso_numero,
                                  '21')  # numero do serviço

    @classmethod
    def validate_option(cls, option, value):
        if option == 'convenio':
            if value == '':
                # TRANSLATORS: Do not translate 'Convenio'
                raise BoletoException(_('Convenio cannot be empty'))
            try:
                int(value)
            except ValueError:
                # TRANSLATORS: Do not translate 'Convenio'
                raise BoletoException(_("Convenio must be a number"))
            if len(value) not in [6, 7, 8]:
                raise BoletoException(
                    # TRANSLATORS: Do not translate 'Convenio'
                    _("Convenio length must be 6, 7 or 8. Try filing it with "
                      "'0's at the left."))


@register_bank
class BankCaixa(BankInfo):
    description = 'Caixa Econômica Federal'
    bank_name = 'CAIXA ECONOMICA FEDERAL'
    bank_number = 104
    cnab_class = CaixaCnab
    logo = 'logo_bancocaixa.jpg'
    options = {u'carteira': BILL_OPTION_CUSTOM,
               u'especie_documento': BILL_OPTION_CUSTOM,
               u'agencia': BILL_OPTION_BANK_BRANCH,
               u'codigo_beneficiario': BILL_OPTION_CUSTOM,
               u'codigo_convenio': BILL_OPTION_CUSTOM,
               u'conta': BILL_OPTION_BANK_BRANCH}

    inicio_nosso_numero = '80'

    conta = custom_property('conta', 11)

    # Nosso numero (sem dv) sao 10 digitos
    @property
    def nosso_numero(self):
        '''Nosso Número sem DV, máximo 8 chars'''
        return self._nosso_numero

    @nosso_numero.setter
    def nosso_numero(self, val):
        self._nosso_numero = (self.inicio_nosso_numero +
                              self.formata_numero(val, 8))

    @property
    def dv_nosso_numero(self):
        resto2 = modulo11(self.nosso_numero.split('-')[0], 9, 1)
        digito = 11 - resto2
        if digito == 10 or digito == 11:
            dv = 0
        else:
            dv = digito
        return dv

    @property
    def campo_livre(self):
        return "%10s%4s%11s" % (self.nosso_numero,
                                self.agencia,
                                self.conta.split('-')[0])


@register_bank
class BankItau(BankInfo):
    description = 'Banco Itaú'
    bank_name = 'BANCO ITAU SA'
    bank_number = 341
    cnab_class = ItauCnab
    logo = 'logo_itau.gif'
    options = {u'carteira': BILL_OPTION_CUSTOM,
               u'especie_documento': BILL_OPTION_CUSTOM,
               u'agencia': BILL_OPTION_BANK_BRANCH,
               u'conta': BILL_OPTION_BANK_BRANCH}

    nosso_numero = custom_property('nosso_numero', 8)
    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 5)

    @property
    def dac_nosso_numero(self):
        agencia = self.agencia.split('-')[0]
        conta = self.conta.split('-')[0]
        return modulo10(agencia +
                        conta +
                        self.carteira +
                        self.nosso_numero)

    def format_nosso_numero(self):
        return '%s/%s-%s' % (self.carteira,
                             self.nosso_numero,
                             self.dac_nosso_numero)

    @property
    def dv_agencia_conta(self):
        agencia = self.agencia.split('-')[0]
        conta = self.conta.split('-')[0]
        return modulo10(agencia + conta)

    @property
    def agencia_conta(self):
        agencia = self.agencia.split('-')[0]
        conta = self.conta.split('-')[0]
        return '%s / %s-%s' % (agencia,
                               conta,
                               self.dv_agencia_conta)

    @property
    def campo_livre(self):
        agencia = self.agencia.split('-')[0]
        conta = self.conta.split('-')[0]
        return "%3s%8s%1s%4s%5s%1s%3s" % (
            self.carteira,
            self.nosso_numero,
            self.dac_nosso_numero,
            agencia,
            conta,
            modulo10(agencia + conta),
            '000'
        )


@register_bank
class BankReal(BankInfo):
    description = 'Banco Real'
    bank_number = 356
    logo = 'logo_bancoreal.jpg'
    options = {u'carteira': BILL_OPTION_CUSTOM,
               u'especie_documento': BILL_OPTION_CUSTOM,
               u'agencia': BILL_OPTION_BANK_BRANCH,
               u'conta': BILL_OPTION_BANK_BRANCH}

    @property
    def agencia_conta(self):
        return "%s/%s-%s" % (self.agencia,
                             self.conta,
                             self.digitao_cobranca)

    @property
    def digitao_cobranca(self):
        num = "%s%s%s" % (self.nosso_numero,
                          self.agencia,
                          self.conta)
        return modulo10(num)

    @property
    def campo_livre(self):
        return "%4s%7s%1s%13s" % (self.agencia,
                                  self.conta,
                                  self.digitao_cobranca,
                                  self.nosso_numero)


@register_bank
class BankSantander(BankInfo):
    description = 'Banco Santander'
    bank_name = description
    bank_number = 33
    cnab_class = SantanderCnab
    logo = 'logo_santander.jpg'
    options = {u'carteira': BILL_OPTION_CUSTOM,
               u'especie_documento': BILL_OPTION_CUSTOM,
               u'codigo_transmissao': BILL_OPTION_CUSTOM,
               u'agencia': BILL_OPTION_BANK_BRANCH,
               u'conta': BILL_OPTION_BANK_BRANCH}

    # Numero fixo na posição 5
    fixo = '9'

    # IOS - somente para Seguradoras (Se 7% informar 7, limitado 9%)
    # Demais clientes usar 0 (zero)
    ios = '0'

    nosso_numero = custom_property('nosso_numero', 7)

    carteira = '102'

    def format_nosso_numero(self):
        return "00000%s-%s" % (
            self.nosso_numero,
            modulo11(self.nosso_numero))

    @property
    def campo_livre(self):
        conta = self.formata_numero(self.conta, 7)
        dv_nosso_numero = modulo11(self.nosso_numero)

        return '%s%s00000%s%s%s%s' % (self.fixo,
                                      conta,
                                      self.nosso_numero,
                                      dv_nosso_numero,
                                      self.ios,
                                      self.carteira)


def get_all_banks():
    return _banks


def get_bank_info_by_number(number):
    for bank in _banks:
        if bank.bank_number == number:
            return bank
    raise NotImplementedError(number)  # pragma no cover
