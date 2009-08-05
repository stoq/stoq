# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   George Y. Kussumoto     <george@async.com.br>
##
""" NF-e XML document generation
"""

import random
from xml.etree.ElementTree import ElementTree, Element, tostring

from utils import get_uf_code_from_state_name

import stoqlib


class NFeGenerator(object):

    def __init__(self):
        #self._sale = sale
        #self.conn = conn
        self.root = Element('NFe', xmlns='http://www.portalfiscal.inf.br/nfe')

    def __str__(self):
        return tostring(self.root)

    def _calculate_dv(self, key):
        # Pg. 72
        assert len(key) == 43

        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        weights_size = len(weights)
        key_characters = list(key)
        key_numbers = [int(k) for k in key_characters]
        key_numbers.reverse()

        dv_sum = 0
        for i, key_number in enumerate(key_numbers):
            # cycle though weights
            i = i % weights_size
            dv_sum += key_number * weights[i]

        dv_mod = dv_sum % 11
        if dv_mod == 0 or dv_mod == 1:
            return 0
        return 11 - dv_mod

    def add_nfe_data(self, key):
        self._nfe_data = NFeData(key)
        self.root.append(self._nfe_data.element)

    def add_nfe_branch(self, branch):
        person = branch.get_adapted()
        address = person.get_main_address()
        city_location = address.city_location
        state = city_location.state


class BaseNFeField(object):
    tag = u''
    attributes = dict()

    def __init__(self):
        self._element = None

    @property
    def element(self):
        if self._element is not None:
            return self._element

        self._element = Element(self.tag)
        for key, value in self.attributes.items():
            sub_element = Element(key)
            sub_element.text = str(value)
            self._element.append(sub_element)

        return self._element

    def format_nfe_date(self, nfe_date):
        # Pg. 93 (and others)
        return nfe_date.strftime('%Y-%m-%d')

    def __str__(self):
        return tostring(self.element)


class NFeData(BaseNFeField):
    """
    - Attributes:

        - versao: Versao do leiaute.

        - Id: Chave de acesso da NF-e precedida do literal 'NFe'.
    """
    tag = 'infNFe'

    def __init__(self, key):
        BaseNFeField.__init__(self)
        self.element.set('versao', u'1.10')

        # Pg. 92
        assert len(key) == 44

        value = u'NFe%s' % key
        self.element.set('Id', value)


class NFeIdentification(BaseNFeField):
    """
    - Attributes:

        - cUF: Código da UF do emitente do Documento Fiscal. Utilizar a Tabela
               do IBGE de código de unidades da federação.

        - cNF: Código numérico que compõe a Chave de Acesso. Número aleatório
               gerado pelo emitente para cada NF-e para evitar acessos
               indevidos da NF-e.

        - natOp: Natureza da operação

        - indPag: 0 - Pagamento a vista (default)
                  1 - Pagamento a prazo
                  2 - outros

        - mod: Utilizar código 55 para identificação de NF-e emitida em
               substituição ao modelo 1 ou 1A.

        - serie: Série do Documento Fiscal, informar 0 (zero) para série
                 única.

        - nNF: Número do documento fiscal.

        - dEmi: Data de emissão do documento fiscal.

        - tpNF: Tipo de documento fiscal.
                0 - entrada
                1 - saída (default)

        - cMunFG: Código do município de ocorrência do fato gerador.

        - tpImp: Formato de impressão do DANFE.
                 1 - Retrato
                 2 - Paisagem (default)

        - tpEmis: Forma de emissão da NF-e
                  1 - Normal (default)
                  2 - Contingência FS
                  3 - Contingência SCAN
                  4 - Contingência DPEC
                  5 - Contingência FS-DA

        - cDV: Dígito verificador da chave de acesso da NF-e.

        - tpAmb: Identificação do ambiente.
                 1 - Produção
                 2 - Homologação

        - finNFe: Finalidade de emissão da NF-e.
                  1 - NF-e normal (default)
                  2 - NF-e complementar
                  3 - NF-e de ajuste

        - procEmi: Identificador do processo de emissão da NF-e.
                   0 - emissãp da NF-e com aplicativo do contribuinte
                       (default)
                   1 - NF-e avulsa pelo fisco
                   2 - NF-e avulsa pelo contribuinte com certificado através
                       do fisco
                   3 - NF-e pelo contribuinte com aplicativo do fisco.

        - verProc: Identificador da versão do processo de emissão (versão do
                   aplicativo emissor de NF-e)
    """
    tag = u'ide'
    # The commented attributes are optional and not implemented yet.
    attributes = dict(
                    # dSaiEnt='',
                    # NFref='',
                    # refNFe='',
                    # refNF='',
                    # AAMM='',
                    # CNPJ='',
                      cUF='',
                      cNF='',
                      natOp='venda',
                      indPag='0',
                      mod='55',
                      serie='0',
                      nNF='',
                      dEmi='',
                      tpNF='1',
                      cMunFG='',

                      tpImp='2',
                      tpEmis='1',
                      cDV='',
                    #TODO: Change tpAmb=1 in the final version.
                      tpAmb='2',
                      finNFe='1',
                      procEmi='0',
                      verProc='stoq-%s' % stoqlib.version,)

    def __init__(self, state, city, payment_type, fiscal_document_number,
                 emission_date, cdv):
        BaseNFeField.__init__(self)

        uf_code = get_uf_code_from_state_name(state)
        self.attributes['cUF'] = uf_code
        # Pg. 92: Random number of 9-digits
        self.attributes['cNF'] = str(random.randint(100000000, 999999999))
        self.attributes['indPag'] = payment_type
        self.attributes['nNF'] = fiscal_document_number
        self.attributes['dEmi'] = self.format_nfe_date(emission_date)
        self.attributes['cDV'] = cdv
        #TODO: get city code
        # self.attributes['cMunFG'] = city_code


class NFeAddress(BaseNFeField):
    """
    - Attributes:
        - xLgr: logradouro.
        - nro: número.
        - xBairro: bairro.
        - cMun: código do município.
        - xMun: nome do município.
        - UF: sigla da UF. Informar EX para operações com o exterior.
    """
    tag = u''
    attributes = dict(
                    # xCpl='',
                    # CEP='',
                    # cPais='',
                    # xPais='',
                    # fone='',
                      xLgr='',
                      nro='',
                      xBairro='',
                      cMun='',
                      xMun='',
                      UF='')

    def __init__(self, tag, rua, numero, bairro, cidade, estado):
        self.tag = tag
        BaseNFeField.__init__(self)
        self.attributes['xLgr'] = rua
        self.attributes['nro'] = numero
        self.attributes['xBairro'] = bairro
        self.attributes['xMun'] = cidade
        #TODO: add city code
        self.attributes['cMun'] = '123123'
        self.attributes['UF'] = estado


class NFeIssuer(BaseNFeField):
    """
    - Attributes:
        - CNPJ: CNPJ do emitente.
        - xNome: Razão social ou nome do emitente
        - IE: inscrição estadual
    """
    tag = u'emit'
    #TODO: enderEmit should be added later
    attributes = dict(
                    # CPF='',
                    # xFant='',
                    # IEST='',
                    # IM='',
                    # CNAE='',
                      CNPJ='',
                      xNome='',
                      IE='')

    def __init__(self, cnpj, nome, ie):
        BaseNFeField.__init__(self)
        self.attributes['CNPJ'] = cnpj
        self.attributes['xNome'] = nome
        self.attributes['IE'] = ie
        #TODO: add address


class NFeRecipient(NFeIssuer):
    tag = 'dest'
    attributes = NFeIssuer.attributes.copy()


class NFeProduct(BaseNFeField):
    """
    - Attributes:
        - nItem: número do item
    """
    tag = u'det'

    def __init__(self, number, ):
        BaseNFeField.__init__(self)
        self.element.set('nItem', str(number))
        #TODO: add product details


class NFeProductDetails(BaseNFeField):
    """
    - Attributes:
        - cProd:
        - cEAN:
        - xProd:
        - NCM:
        - CFOP:
        - uCom:
        - qCom:
        - vUnCom:
        - vProd:
        - cEANTrib:
        - uTrib:
        - qTrib:
        - vUnTrib:
    """
    tag = u'prod'
    attributes = dict(
                      #NCM='',
                      #EXTIPI='',
                      #genero='',
                      #vFrete='',
                      #vSeg='',
                      #vDesc='',

                      #DI='',
                      #    nDI='',
                      #    dDI='',
                      #    xLocDesemb='',
                      #    UFDesemb='',
                      #    dDesemb='',
                      #    cExportador='',

                      #adi='',
                      #    nAdicao='',
                      #    nSeqAdic='',
                      #    cFabricante='',
                      #    #vDescDI='',
                      cProd='',
                      cEAN='',
                      xProd='',
                      CFOP='',
                      uCom='',
                      qCom='',
                      vUnCom='',
                      vProd='',
                      cEANTrib='',
                      uTrib='',
                      qTrib='',
                      vUnTrib='')


class NFeTax(BaseNFeField):
    tag = 'imposto'


class NFeICMS(BaseNFeField):
    tag = 'ICMS'
    attributes = dict(ICMS00='',
                      orig='',
                      CST='',
                      modBC='',
                      vBC='',
                      pICMS='',
                      vICMS='',

                      ICMS10='')
