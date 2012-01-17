# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import os
import sys

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

class BoletoData(object):
    codigo_banco = ''
    logo = ''
    aceite = 'N'
    especie = "R$"
    moeda = "9"
    local_pagamento = "Pagável em qualquer banco até o vencimento"
    quantidade = ""

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
        if (not kwargs.has_key('numero_documento') and
            kwargs.has_key('nosso_numero')):
            kwargs['numero_documento'] = kwargs['nosso_numero']

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.logo_image_path = ""
        if self.logo:
            self.logo_image_path = os.path.join(os.path.dirname(__file__),
                                                "media",
                                                self.logo)

    @property
    def campo_livre(self):
        raise NotImplementedError

    @property
    def barcode(self):
        num = "%3s%1s%1s%4s%10s%24s" % (
            self.codigo_banco,
            self.moeda,
            'X',
            self.fator_vencimento,
            self.formata_valor(self.valor_documento,10),
            self.campo_livre
        )
        dv = self.calculate_dv_barcode(num.replace('X', '', 1))

        num = num.replace('X', str(dv), 1)
        assert len(num) == 44, 'Código com %d caracteres' % len(num)
        return num


    @property
    def dv_nosso_numero(self):
        """Returns nosso número DV

            It should be implemented by derived class
        """
        raise NotImplementedError

    def calculate_dv_barcode(self, line):
        resto2 = self.modulo11(line,9,1)
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
        date_ref = datetime.date(2000,7,3) # Fator = 1000
        delta = self.data_vencimento - date_ref
        fator = delta.days + 1000
        return fator

    @property
    def agencia_conta(self):
        return "%s/%s" % (self.agencia, self.conta)

    @property
    def codigo_dv_banco(self):
        cod = "%s-%s" % (self.codigo_banco, self.modulo11(self.codigo_banco))
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

    @staticmethod
    def formata_numero(numero, tamanho):
        if len(numero) > tamanho:
            raise BoletoException(
                u'Tamanho do numero maior que o permitido' )
        return numero.zfill(tamanho)

    @staticmethod
    def formata_texto(texto, tamanho):
        if len(texto) > tamanho:
            raise BoletoException(
                u'Tamanho do texto maior que o permitido' )
        return texto.ljust(tamanho)

    @staticmethod
    def formata_valor(nfloat, tamanho):
        try:
            txt = nfloat.replace('.', '')
            txt = BoletoData.formata_numero(txt, tamanho)
            return txt
        except AttributeError:
            pass

    @staticmethod
    def modulo10(num):
        soma = 0
        peso = 2
        for i in range(len(num)-1,-1,-1):
            parcial = int(num[i]) * peso
            if parcial > 9:
                s = "%d" % parcial
                parcial = int(s[0])+int(s[1])
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
        soma=0
        fator=2
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

_banks = {}
def get_bank(codigo_banco):
    global _banks
    if not _banks:
        get_banks()
    return _banks.get(codigo_banco, None)


def get_banks():
    from pyboleto import bank
    _dir = os.path.dirname(bank.__file__)
    global _banks

    for brand in os.listdir(_dir):
        if not brand.endswith('.py'):
            continue
        brand = brand.replace('.py', '')

        __import__('pyboleto.bank.%s' % brand)
        mod = sys.modules['pyboleto.bank.%s' % brand]

        for item in mod.__dict__.values():
            if hasattr(item, 'codigo_banco') and item.codigo_banco:
                _banks[item.codigo_banco] = item

    return _banks
