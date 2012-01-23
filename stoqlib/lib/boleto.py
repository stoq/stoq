# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011 Async Open Source
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
from decimal import Decimal

from kiwi.environ import environ
from kiwi.log import Logger

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = Logger('stoqlib.lib.boleto')


(BILL_OPTION_BANK_BRANCH,
 BILL_OPTION_BANK_ACCOUNT,
 BILL_OPTION_CUSTOM) = range(3)


class BoletoException(Exception):
    pass


def custom_property(name, num_length):
    """
        Function to create properties on boleto

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
            raise BoletoException('Wrong value format')

    return property(
        lambda self: getattr(self, internal_attr),
        _set_attr,
        lambda self: delattr(self, internal_attr),
        name
    )


class BankInfo(object):

    aceite = 'N'
    especie = "R$"
    moeda = "9"
    local_pagamento = "Pagável em qualquer banco até o vencimento"
    quantidade = ""

    # Override in base class

    description = None
    bank_number = None
    options = {}
    logo = ''

    validate_field_func = None
    validate_field_dv_10 = None

    def __init__(self, **kwargs):
        # Informações gerais
        self.especie_documento = ""
        self.instrucoes = []

        # Cedente (empresa - dados do banco)
        self.agencia = ""
        self.carteira = ""
        self.cedente = ""
        self.conta = ""

        # Sacado (cliente)
        self.sacado_nome = ""
        self.sacado_cidade = ""
        self.sacado_uf = ""
        self.sacado_endereco = ""
        self.sacado_bairro = ""
        self.sacado_cep = ""

        # Pagamento
        self.data_documento = ""
        self.data_processamento = datetime.date.today()
        self.data_vencimento = ""
        self.demonstrativo = []
        if (not 'numero_documento' in kwargs and
            'nosso_numero' in kwargs):
            kwargs['numero_documento'] = kwargs['nosso_numero']

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.logo_image_path = ""
        if self.logo:
            self.logo_image_path = environ.find_resource('pixmaps', self.logo)

    @property
    def campo_livre(self):
        raise NotImplementedError

    @property
    def barcode(self):
        num = "%03d%1s%1s%4s%10s%24s" % (
            self.bank_number,
            self.moeda,
            'X',
            self.fator_vencimento,
            self.formata_valor(self.valor_documento, 10),
            self.campo_livre
        )

        dv = self.calculate_dv_barcode(num.replace('X', '', 1))

        num = num.replace('X', str(dv), 1)
        if len(num) != 44:
            raise BoletoException(
                'Código com %d caracteres' % len(num))
        return num

    @property
    def dv_nosso_numero(self):
        """Returns nosso número DV

            It should be implemented by derived class
        """
        raise NotImplementedError

    def calculate_dv_barcode(self, line):
        resto2 = self.modulo11(line, 9, 1)
        if resto2 in [0, 1, 10]:
            dv = 1
        else:
            dv = 11 - resto2
        return dv

    def format_nosso_numero(self):
        """
            Return Formatted Nosso Número

            It should be implemented by derived class
        """
        return self.nosso_numero

    nosso_numero = custom_property('nosso_numero', 13)
    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 7)

    def _get_valor(self):
        try:
            return "%.2f" % self._valor
        except AttributeError:
            pass

    def _set_valor(self, val):
        if type(val) is Decimal:
            self._valor = val
        else:
            self._valor = Decimal(str(val), 2)
    valor = property(_get_valor, _set_valor)

    def _get_valor_documento(self):
        try:
            return "%.2f" % self._valor_documento
        except AttributeError:
            pass

    def _set_valor_documento(self, val):
        if type(val) is Decimal:
            self._valor_documento = val
        else:
            self._valor_documento = Decimal(str(val), 2)
    valor_documento = property(
        _get_valor_documento,
        _set_valor_documento
    )

    def _instrucoes_get(self):
        try:
            return self._instrucoes
        except AttributeError:
            pass

    def _instrucoes_set(self, list_inst):
        self._instrucoes = list_inst
    instrucoes = property(_instrucoes_get, _instrucoes_set)

    def _demonstrativo_get(self):
        try:
            return self._demonstrativo
        except AttributeError:
            pass

    def _demonstrativo_set(self, list_dem):
        self._demonstrativo = list_dem
    demonstrativo = property(_demonstrativo_get, _demonstrativo_set)

    def _sacado_get(self):
        if not hasattr(self, '_sacado'):
            self.sacado = [
                self.sacado_nome,
                self.sacado_endereco,
                '%s - %s - %s - %s' % (
                    self.sacado_bairro,
                    self.sacado_cidade,
                    self.sacado_uf,
                    self.sacado_cep
                )
            ]
        return self._sacado

    def _sacado_set(self, list_sacado):
        if len(list_sacado) > 3:
            raise BoletoException(u'Número de linhas do sacado maior que 3')
        for line in list_sacado:
            if len(line) > 80:
                raise BoletoException(
                    u'Linha de sacado possui mais que 80 caracteres')
        self._sacado = list_sacado
    sacado = property(_sacado_get, _sacado_set)

    @property
    def fator_vencimento(self):
        date_ref = datetime.date(2000, 7, 3)  # Fator = 1000
        delta = self.data_vencimento - date_ref
        fator = delta.days + 1000
        return fator

    @property
    def agencia_conta(self):
        return "%s/%s" % (self.agencia, self.conta)

    @property
    def codigo_dv_banco(self):
        num = '%03d' % (self.bank_number, )
        cod = "%s-%s" % (num, self.modulo11(num))
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
            campo_dv = "%s%s" % (campo, self.modulo10(campo))
            return "%s.%s" % (campo_dv[0:5], campo_dv[5:])

        campo1 = monta_campo(linha[0:4] + linha[19:24])
        campo2 = monta_campo(linha[24:34])
        campo3 = monta_campo(linha[34:44])
        campo4 = linha[4]
        campo5 = linha[5:19]

        return "%s %s %s %s %s" % (campo1, campo2, campo3, campo4, campo5)

    @classmethod
    def get_extra_options(cls):
        rv = []
        for option, kind in cls.options.items():
            if kind == BILL_OPTION_CUSTOM:
                rv.append(option)
        return rv

    @classmethod
    def validate_field(cls, field, dv_10=None, func=None):
        if ' ' in field:
            raise BoletoException(
                u'Campo não pode ter espaços')
        if '.' in field or ',' in field:
            raise BoletoException(
                u'Campo não pode ter pontos ou virgulas')
        dv = None
        if '-' in field:
            if field.count('-') != 1:
                raise BoletoException(
                    u'Só pode ter um hífen')
            field, dv = field.split('-', 1)
            if not dv:
                raise BoletoException(
                    u'Digito verificador não pode ser vazio')
        try:
            int(field)
        except ValueError:
            raise BoletoException(
                u'Conta precisa ser um número')

        if dv and dv_10 is not None:
            func = cls.validate_field_func
            if func == 'modulo11':
                ret = cls.modulo11(field)
            elif func == 'modulo10':
                ret = cls.modulo10(field)
            else:
                ret = None

            if dv.lower() in [dv_10]:
                # FIXME: Is it correct that the rest of 0 is
                #        the same as 10?
                if ret == 0:
                    pass
                elif (ret is not None and
                    str(ret) != dv.lower() and
                    ret < 10):
                    raise BoletoException(
                        u'Dígito verificador invalido')
            else:
                try:
                    dv = int(dv)
                except ValueError:
                    raise BoletoException(
                        u'Dígito verificador tem que ser um número ou %s' % (
                        dv_10))

                if ret is not None and ret != dv:
                    raise BoletoException(
                        u'Dígito verificador invalido')

    @classmethod
    def validate_option(cls, option, value):
        pass

    @staticmethod
    def formata_numero(numero, tamanho):
        if len(numero) > tamanho:
            raise BoletoException(
                u'Tamanho do numero maior que o permitido')
        return numero.zfill(tamanho)

    @staticmethod
    def formata_texto(texto, tamanho):
        if len(texto) > tamanho:
            raise BoletoException(
                u'Tamanho do texto maior que o permitido')
        return texto.ljust(tamanho)

    @staticmethod
    def formata_valor(nfloat, tamanho):
        try:
            txt = nfloat.replace('.', '')
            txt = BankInfo.formata_numero(txt, tamanho)
            return txt
        except AttributeError:
            pass

    @staticmethod
    def modulo10(num):
        soma = 0
        peso = 2
        for i in range(len(num) - 1, -1, -1):
            parcial = int(num[i]) * peso
            if parcial > 9:
                s = "%d" % parcial
                parcial = int(s[0]) + int(s[1])
            soma += parcial
            if peso == 2:
                peso = 1
            else:
                peso = 2

        resto10 = soma % 10
        if resto10 == 0:
            modulo10 = 0
        else:
            modulo10 = 10 - resto10

        return modulo10

    @staticmethod
    def modulo11(num, base=9, r=0):
        soma = 0
        fator = 2
        for i in range(len(str(num))).__reversed__():
            parcial10 = int(num[i]) * fator
            soma += parcial10
            if fator == base:
                fator = 1
            fator += 1
        if r == 0:
            soma = soma * 10
            digito = soma % 11
            if digito == 10:
                digito = 0
            return digito
        if r == 1:
            resto = soma % 11
            return resto


_banks = []


def register_bank(bank_class):
    if not issubclass(bank_class, BankInfo):
        raise TypeError
    assert not bank_class in _banks
    _banks.append(bank_class)
    return bank_class


@register_bank
class BankBanrisul(BankInfo):
    description = 'Banrisul'
    bank_number = 41
    logo = 'logo_banrisul.jpg'
    options = {'agencia': BILL_OPTION_BANK_BRANCH,
               'conta': BILL_OPTION_BANK_BRANCH}

    nosso_numero = custom_property('nosso_numero', 8)
    conta = custom_property('conta', 6)

    def __init__(self, **kwargs):
        BankInfo.__init__(self, **kwargs)

    # From http://jrimum.org/bopepo/browser/trunk/src/br/com/nordestefomento/jrimum/bopepo/campolivre/AbstractCLBanrisul.java
    def calculaDuploDigito(self, seisPrimeirosCamposConcatenados):
        def sum11(s, lmin, lmax):
            soma = 0
            peso = lmin
            for c in reversed(s):
                soma += peso * int(c)
                peso += 1
                if peso > lmax:
                    peso = lmin
            return soma
        primeiroDV = self.modulo10(seisPrimeirosCamposConcatenados)
        somaMod11 = sum11(
            seisPrimeirosCamposConcatenados + str(primeiroDV), 2, 7)
        restoMod11 = self.calculeRestoMod11(somaMod11)
        while restoMod11 == 1:
            primeiroDV = self.encontreValorValidoParaPrimeiroDV(primeiroDV)
            somaMod11 = sum11(
                seisPrimeirosCamposConcatenados + str(primeiroDV), 2, 7)
            restoMod11 = self.calculeRestoMod11(somaMod11)
        segundoDV = self.calculeSegundoDV(restoMod11)
        return str(primeiroDV) + str(segundoDV)

    def calculeSegundoDV(self, restoMod11):
        if restoMod11 == 0:
            return restoMod11
        else:
            return 11 - restoMod11

    def calculePrimeiroDV(self, restoMod10):
        if restoMod10 == 0:
            return 0
        else:
            return 10 - restoMod10

    def calculeRestoMod10(self, somaMod10):
        if somaMod10 < 10:
            return somaMod10
        else:
            return somaMod10 % 10

    def encontreValorValidoParaPrimeiroDV(self, primeiroDV):
        if primeiroDV == 9:
            return 0
        else:
            return primeiroDV + 1

    def calculeRestoMod11(self, somaMod11):
        if somaMod11 < 11:
            return somaMod11
        else:
            return somaMod11 % 11

    @property
    def campo_livre(self):
        content = '21%04d%07d%08d40' % (int(self.agencia),
                                        int(self.conta),
                                        int(self.nosso_numero))
        dv = self.calculaDuploDigito(content)
        return '%s%s' % (content, dv)


@register_bank
class BankBradesco(BankInfo):
    description = 'Bradesco'
    bank_number = 237
    logo = "logo_bancobradesco.jpg"

    options = {'carteira': BILL_OPTION_CUSTOM,
               'agencia': BILL_OPTION_BANK_BRANCH,
               'conta': BILL_OPTION_BANK_BRANCH}

    validate_field_func = 'modulo11'
    validate_field_dv_10 = '0'

    def format_nosso_numero(self):
        return "%s/%s-%s" % (
            self.carteira,
            self.nosso_numero,
            self.dv_nosso_numero
        )

    # Nosso numero (sem dv) sao 11 digitos
    nosso_numero = custom_property('nosso_numero', 11)

    @property
    def dv_nosso_numero(self):
        resto2 = self.modulo11(self.nosso_numero, 7, 1)
        digito = 11 - resto2
        if digito == 10:
            dv = 'P'
        elif digito == 11:
            dv = 0
        else:
            dv = digito
        return dv

    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 7)

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
                return
            try:
                value = int(value)
            except ValueError:
                raise BoletoException("carteira tem que ser um número")
            if 0 > value:
                raise BoletoException("carteira tem que ser entre 0 e 99")
            if value > 99:
                raise BoletoException("carteira tem que ser entre 0 e 99")


@register_bank
class BankBB(BankInfo):
    description = 'Banco do Brasil'
    bank_number = 1
    logo = 'logo_bb.gif'
    options = {'convenio': BILL_OPTION_CUSTOM,
               'len_convenio': BILL_OPTION_CUSTOM,
               'agencia': BILL_OPTION_BANK_BRANCH,
               'conta': BILL_OPTION_BANK_BRANCH}

    validate_field_func = 'modulo11'
    validate_field_dv_10 = 'x'

    def __init__(self, **kwargs):
        if not 'carteira' in kwargs:
            kwargs['carteira'] = '18'

        self.len_convenio = 7
        if 'len_convenio' in kwargs:
            self.len_convenio = int(kwargs.pop('len_convenio'))
        self.convenio = ''

        self.format_nnumero = 1
        if 'format_nnumero' in kwargs:
            self.format_nnumero = int(kwargs.pop('format_nnumero'))
        kwargs['agencia'] = kwargs['agencia'].split('-')[0]
        kwargs['conta'] = kwargs['conta'].split('-')[0]
        super(BankBB, self).__init__(**kwargs)

    def format_nosso_numero(self):
        return "%s-%s" % (
            self.nosso_numero,
            self.dv_nosso_numero
        )

    # Nosso numero (sem dv) sao 11 digitos
    def _get_nosso_numero(self):
        return self.convenio + self._nosso_numero

    def _set_nosso_numero(self, val):
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

    nosso_numero = property(_get_nosso_numero, _set_nosso_numero)

    def _get_convenio(self):
        return self._convenio

    def _set_convenio(self, val):
        self._convenio = str(val).ljust(self.len_convenio, '0')
    convenio = property(_get_convenio, _set_convenio)

    @property
    def agencia_conta(self):
        return "%s-%s / %s-%s" % (
            self.agencia,
            self.modulo11(self.agencia),
            self.conta,
            self.modulo11(self.conta)
        )

    @property
    def dv_nosso_numero(self):
        return self.modulo11(self.nosso_numero)

    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 8)

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
                raise BoletoException('Convenio não pode ser vazio')
            try:
                int(value)
            except ValueError:
                raise BoletoException(_("Must be a number"))
            if len(value) > 8:
                raise BoletoException(_("Cannot be longer than %d") % (8,))

        if option == 'len_convenio':
            if value not in ['6', '7', '8']:
                raise BoletoException('Tem que ser 6, 7 ou 8')


@register_bank
class BankCaixa(BankInfo):
    description = 'Caixa Econômica Federal'
    bank_number = 104
    logo = 'logo_bancocaixa.jpg'
    options = {'carteira': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}

    inicio_nosso_numero = '80'

    # Nosso numero (sem dv) sao 10 digitos
    def _nosso_numero_get(self):
        return self._nosso_numero
    '''
        Nosso Número sem DV, máximo 8 chars
    '''
    def _nosso_numero_set(self, val):
        self._nosso_numero = (self.inicio_nosso_numero +
                              self.formata_numero(val, 8))

    nosso_numero = property(_nosso_numero_get, _nosso_numero_set)

    @property
    def dv_nosso_numero(self):
        resto2 = self.modulo11(self.nosso_numero.split('-')[0], 9, 1)
        digito = 11 - resto2
        if digito == 10 or digito == 11:
            dv = 0
        else:
            dv = digito
        return dv

    conta = custom_property('conta', 11)

    @property
    def campo_livre(self):
        return "%10s%4s%11s" % (self.nosso_numero,
                                self.agencia,
                                self.conta.split('-')[0])


@register_bank
class BankItau(BankInfo):
    description = 'Banco Itaú'
    bank_number = 341
    logo = 'logo_itau.gif'
    options = {'carteira': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}

    nosso_numero = custom_property('nosso_numero', 8)
    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 5)

    @property
    def dac_nosso_numero(self):
        agencia = self.agencia.split('-')[0]
        conta = self.conta.split('-')[0]
        return self.modulo10(agencia +
                             conta +
                             self.carteira +
                             self.nosso_numero)

    def format_nosso_numero(self):
        return '%s/%s-%s' % (self.carteira,
                             self.nosso_numero,
                             self.dac_nosso_numero)

    @property
    def agencia_conta(self):
        agencia = self.agencia.split('-')[0]
        conta = self.conta.split('-')[0]
        return '%s / %s-%s' % (agencia,
                               conta,
                               self.modulo10(agencia + conta))

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
            self.modulo10(agencia + conta),
            '000'
        )


@register_bank
class BankReal(BankInfo):
    description = 'Banco Real'
    bank_number = 356
    logo = 'logo_bancoreal.jpg'
    options = {'carteira': BILL_OPTION_CUSTOM,
               'agencia': BILL_OPTION_BANK_BRANCH,
               'conta': BILL_OPTION_BANK_BRANCH}

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
        return self.modulo10(num)

    @property
    def campo_livre(self):
        return "%4s%7s%1s%13s" % (self.agencia,
                                  self.conta,
                                  self.digitao_cobranca,
                                  self.nosso_numero)


@register_bank
class BankSantander(BankInfo):
    description = 'Banco Santander'
    bank_number = 33
    logo = 'logo_santander.jpg'
    options = {'carteira': BILL_OPTION_CUSTOM,
               'agencia': BILL_OPTION_BANK_BRANCH,
               'conta': BILL_OPTION_BANK_BRANCH}

    # Numero fixo na posição 5
    fixo = '9'

    # IOS - somente para Seguradoras (Se 7% informar 7, limitado 9%)
    # Demais clientes usar 0 (zero)
    ios = '0'

    nosso_numero = custom_property('nosso_numero', 7)

    def __init__(self, **kwargs):
        BankInfo.__init__(self, **kwargs)
        self.carteira = '102'

    def format_nosso_numero(self):
        return "00000%s-%s" % (
            self.nosso_numero,
            self.modulo11(self.nosso_numero))

    @property
    def campo_livre(self):
        conta = self.formata_numero(self.conta, 7)
        dv_nosso_numero = self.modulo11(self.nosso_numero)

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
    raise NotImplementedError(number)
