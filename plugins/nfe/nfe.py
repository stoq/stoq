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

from xml.etree.ElementTree import ElementTree, Element, tostring


class NFe(object):
    pass

    #
    # Public API
    #

    #
    # Private API
    #



class BaseNFeField(object):
    tag = u''
    attributes = dict()
    _element = None

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


class NFeData(BaseNFeField):
    """
    - Attributes:

        - versao: Versao do leiaute.

        - Id: Chave de acesso da NF-e precedida do literal 'NFe'.
    """
    tag = 'infNFe'

    def __init__(self):
        BaseNFeField.__init__(self)

        self._items = dict(versao=u'1.10', Id=u'')
        self._set_access_key()

    def _set_access_key(self):
        # TODO:
        self._items['Id'] = u'NFe123'


class NFeIdentification(BaseNFeField):
    """
    - Attributes:

        - cUF: Código da UF do emitente do Documento Fiscal. Utilizar a Tabela
               do IBGE de código de unidades da federação.

        - cNF: Código Numérico que compõe a E B01 N 1-1 9 Código numérico que
               compõe a Chave de Acesso. Número aleatório gerado pelo emitente
               para cada NF-e para evitar acessos indevidos da NF-e.

        - natOp: Natureza da operação

        - indPag: 0 - Pagamento a vista (default)
                  1 - Pagamento a prazo
                  2 - outros

        - mod: Utilizar código 55 para identificação de NF-e emitida em
               substituição ao modelo 1 ou 1A.

        - serie: Série do Documento Fiscal, informar 0 (zero) para série
                 única.

        - nNF: Número do documento fiscal.

        - dEmi:
        - tpNF:
        - cMunFG:
        - tpImp:
        - tpEmis:
        - cDV:
        - tpAmb:
        - finNFe:
        - procEmi:
        - verProc:
    """
    tag = u'ide'
    # The commented attributes are optional and not implemented yet.
    attributes = dict(cUF='',
                      cNF='',
                      natOp='',
                      indPag=0,
                      mod=55,
                      serie=0,
                      nNF='',
                      dEmi='',
                      tpNF='',
                      cMunFG='',
                    # dSaiEnt='',
                    # NFref='',
                    # refNFe='',
                    # refNF='',
                    # AAMM='',
                    # CNPJ='',
                      tpImp='',
                      tpEmis='',
                      cDV='',
                      tpAmb='',
                      finNFe='',
                      procEmi='',
                      verProc='',)



class NFeEmitAddress(BaseNFeField):
    tag = u'enderEmit'
    attributes = dict(xLgr='',
                      nro='',
                    # xCpl='',
                      xBairro='',
                      cMun='',
                      xMun='',
                      UF='',
                    # CEP='',
                    # cPais='',
                    # xPais='',
                    # fone='',
                        )


class NFeIssuer(BaseNFeField):
    """
    - Attributes:
    """
    tag = u'emit'
    #TODO: enderEmit should be added later
    attributes = dict(CNPJ='',
                    # CPF='',
                      xNome='',
                      IE='',
                    # xFant='',
                    # IEST='',
                    # IM='',
                    # CNAE='',
                    )


class NFeRecipient(NFeIssuer):
    tag = 'dest'
    attributes = NFeIssuer.attributes.copy()
