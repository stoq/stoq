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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" NF-e XML document generation """

from collections import namedtuple
from dateutil.tz import tzlocal
from decimal import Decimal
import datetime
import math
import os.path
import random
import StringIO
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from kiwi.python import strip_accents, Settable

from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.domain.sale import Sale
from stoqlib.enums import NFeDanfeOrientation
from stoqlib.exceptions import ModelDataError
from stoqlib.lib.ibpt import generate_ibpt_message
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.validators import validate_cnpj

# NF-e operation type
INVOICE_IN = 0
INVOICE_OUT = 1


def nfe_tostring(element):
    """Returns the canonical XML string of a certain element with line feeds
    and carriage return stripped.

    @param element: a xml.etree.Element instance.
    @returns: a XML string of the element.
    """
    message = ElementTree.tostring(element, 'utf8')
    node = ElementTree.XML(message)
    tree = ElementTree.ElementTree(node)
    # The transformation of the XML to its canonical form is required along
    # all the NF-e specification and its not supported by the xml.etree module
    # of the standard python library. See http://www.w3.org/TR/xml-c14n for
    # details.
    xml = StringIO.StringIO()
    tree.write_c14n(xml)

    xml_str = xml.getvalue()
    xml_str = xml_str.replace('\r', '')
    xml_str = xml_str.replace('\n', '')
    return xml_str


def format_cst(cst):
    return str(cst).zfill(2)

#
# the page numbers refers to the "Manual de integração do contribuinte v3.00"
# and could be found at http://www.nfe.fazenda.gov.br/portal/integracao.aspx
# (brazilian portuguese only).
#


class NFeGenerator(object):
    """NF-e Generator class.
    The NF-e generator is responsible to create a NF-e XML document for a
    given operation (e.g. sale, loan, transfer).
    """

    def __init__(self, operation, store):
        self._order = operation
        self._total_taxes = 0

        self.store = store
        self.root = ElementTree.Element(
            'NFe', xmlns='http://www.portalfiscal.inf.br/nfe')

    #
    # Public API
    #

    def generate(self):
        """Generates the NF-e."""
        branch = self._order.branch
        self._add_identification(branch, self._order.recipient)
        self._add_issuer(branch)

        self._add_recipient(self._order.recipient)

        operation_items = self._order.get_items().order_by('te_id')
        self._add_items(operation_items)

        self._add_totals()
        self._add_transport_data(self._order.transporter,
                                 operation_items)

        self._add_billing_data()
        self._add_additional_information(operation_items)

    def save(self, location=''):
        """Saves the NF-e.
        @param location: the path to save the NF-e.
        """
        # a string like: NFe35090803852995000107550000000000018859747268
        data_id = self._nfe_data.get_id_value()
        # ignore the NFe prefix
        name = "%s-nfe.xml" % data_id[3:]
        filename = os.path.join(location, name)
        fp = open(filename, 'wb')
        fp.write(nfe_tostring(self.root))
        fp.close()

    def export_txt(self, location=''):
        """Exports the NF-e in a text format that can used to import the NF-e
        by the current NF-e management software provided by the government.
        More information: http://www.emissornfehom.fazenda.sp.gov.br/.

        @param location: the patch to save the NF-e in text format.
        """
        # a string like: NFe35090803852995000107550000000000018859747268
        data_id = self._nfe_data.get_id_value()
        # ignore the NFe prefix
        name = "%s-nfe.txt" % data_id[3:]
        filename = os.path.join(location, name)
        fp = open(filename, 'wb')
        # we need to remove the accentuation to avoid import errors from
        # external applications.
        fp.write(strip_accents(self._as_txt()))
        fp.close()

    #
    # Private API
    #

    def __str__(self):
        return nfe_tostring(self.root)

    def _as_txt(self):
        nfe = [u'NOTAFISCAL|1|\n',
               self._nfe_data.as_txt()]
        return u''.join(nfe)

    def _calculate_verifier_digit(self, key):
        # Calculates the verifier digit. The verifier digit is used to
        # validate the NF-e key, details in page 72 of the manual.
        assert len(key) == 43

        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        weights_size = len(weights)
        key_numbers = [int(k) for k in key]
        key_numbers.reverse()

        key_sum = 0
        for i, key_number in enumerate(key_numbers):
            # cycle though weights
            i = i % weights_size
            key_sum += key_number * weights[i]

        remainder = key_sum % 11
        if remainder == 0 or remainder == 1:
            return '0'
        return str(11 - remainder)

    def _get_now_datetime(self):
        return datetime.datetime.now()

    def _get_cnpj(self, branch):
        company = branch.person.company
        assert company is not None

        # FIXME: fix get_cnpj_number method (fails if start with zero).
        cnpj = ''.join([c for c in company.cnpj if c in '1234567890'])
        if not validate_cnpj(cnpj):
            raise ModelDataError(_("The CNPJ of %s is not valid.")
                                 % branch.person.name)

        return cnpj

    def _format_state_registry(self, state_registry):
        if state_registry.isalpha():
            return state_registry.upper()
        return ''.join([s for s in state_registry if s in '1234567890'])

    def _add_identification(self, branch, recipient):
        # Pg. 71
        branch_location = branch.person.get_main_address().city_location
        cuf = str(branch_location.state_code or '')

        recipient_address = recipient.get_main_address()
        if recipient_address:
            recipient_location = recipient_address.city_location
        else:
            recipient_location = branch_location
        now = self._get_now_datetime()
        aamm = now.strftime('%y%m')

        invoice = self._order.invoice
        nnf = invoice.invoice_number
        assert nnf

        payments = self._order.payments or []
        series = sysparam.get_int('NFE_SERIAL_NUMBER')
        orientation = sysparam.get_int('NFE_DANFE_ORIENTATION')

        ecf_info = None
        tpnf = INVOICE_OUT
        if isinstance(self._order, Sale):
            ecf_info = self._order.nfe_coupon_info
        elif isinstance(self._order, ReturnedSale):
            tpnf = INVOICE_IN

        nat_op = self._order.operation_nature or ''

        nfe_identification = NFeIdentification(cuf, branch_location, recipient_location,
                                               series, nnf, now,
                                               list(payments), orientation,
                                               ecf_info, nat_op, tpnf)
        # The nfe-key requires all the "zeros", so we should format the
        # values properly.
        mod = '%02d' % int(nfe_identification.get_attr('mod'))
        serie = '%03d' % int(nfe_identification.get_attr('serie'))

        cnf = '%08d' % nfe_identification.get_attr('cNF')
        nnf_str = '%09d' % nnf
        cnpj = self._get_cnpj(branch)
        tpemis = nfe_identification.get_attr('tpEmis')
        # Key format (Pg. 71):
        # cUF + AAMM + CNPJ + mod + serie + nNF + cNF + (cDV)
        key = cuf + aamm + cnpj + mod + serie + nnf_str + tpemis + cnf
        cdv = self._calculate_verifier_digit(key)
        key += cdv

        # Save key and cnf in Invoice table.
        invoice.save_nfe_info(unicode(cnf), unicode(key))

        nfe_identification.set_attr('cDV', cdv)
        self._nfe_identification = nfe_identification

        self._nfe_data = NFeData(key)
        self._nfe_data.append(nfe_identification)
        self.root.append(self._nfe_data.element)

    def _add_issuer(self, branch):
        cnpj = self._get_cnpj(branch)
        # FIXME: Should we use branch.get_description here?
        name = branch.person.name
        person = branch.person
        company = person.company
        state_registry = self._format_state_registry(company.state_registry)
        crt = self._order.branch.crt
        self._nfe_issuer = NFeIssuer(name, cnpj=cnpj,
                                     state_registry=state_registry, crt=crt)
        self._nfe_issuer.set_address(person.get_main_address(),
                                     person.get_phone_number_number())
        self._nfe_data.append(self._nfe_issuer)

    def _add_recipient(self, recipient):
        name = recipient.name
        individual = recipient.individual
        company = recipient.company
        email = recipient.email
        if individual and individual.cpf:
            cpf = ''.join([c for c in individual.cpf if c in '1234567890'])
            self._nfe_recipient = NFeRecipient(name, cpf=cpf, email=email)
        elif company and company.cnpj:
            cnpj = ''.join([c for c in company.cnpj if c in '1234567890'])
            state_registry = self._format_state_registry(company.state_registry)

            self._nfe_recipient = NFeRecipient(name, cnpj=cnpj,
                                               state_registry=state_registry,
                                               email=email)
        else:
            self._nfe_recipient = NFeRecipient(name, cpf='', email=email)

        self._nfe_recipient.set_address(recipient.get_main_address(),
                                        recipient.get_phone_number_number())
        self._nfe_data.append(self._nfe_recipient)

    def _add_items(self, operation_items):
        coupon = None
        if isinstance(self._order, Sale):
            coupon = self._order.coupon_id

        for item_number, operation_item in enumerate(operation_items):
            # item_number should start from 1, not zero.
            item_number += 1
            nfe_item = NFeProduct(item_number)

            sellable = operation_item.sellable
            product = sellable.product
            if product:
                ncm = product.ncm
                ex_tipi = product.ex_tipi
                genero = product.genero
            else:
                ncm = ''
                ex_tipi = ''
                genero = ''

            nfe_item.add_product_details(sellable.code,
                                         sellable.get_description(),
                                         operation_item.nfe_cfop_code,
                                         operation_item.quantity,
                                         operation_item.price,
                                         sellable.unit_description,
                                         barcode=sellable.barcode,
                                         ncm=ncm,
                                         ex_tipi=ex_tipi,
                                         genero=genero)

            nfe_item.add_tax_details(operation_item, self._order.branch.crt, coupon)
            self._nfe_data.append(nfe_item)

    def _add_totals(self):
        nfe_total = NFeTotal()
        nfe_total.add_icms_total(self._order)
        self._nfe_data.append(nfe_total)

    def _add_transport_data(self, transporter, operation_items):
        nfe_transport = NFeTransport()
        self._nfe_data.append(nfe_transport)
        if transporter:
            person = transporter.person
            individual = person.individual
            if individual is not None:
                cpf = ''.join([c for c in individual.cpf if c in '1234567890'])
                nfe_transporter = NFeTransporter(transporter, cpf=cpf)
            else:
                company = person.company
                cnpj = ''.join([c for c in company.cnpj if c in '1234567890'])
                state_registry = self._format_state_registry(company.state_registry)
                nfe_transporter = NFeTransporter(transporter, cnpj=cnpj,
                                                 state_registry=state_registry)

            self._nfe_data.append(nfe_transporter)

        for item_number, operation_item in enumerate(operation_items):
            sellable = operation_item.sellable
            product = sellable.product
            if not product:
                continue

            unitary_weight = product.weight
            if not unitary_weight:
                continue

            unit = sellable.unit and sellable.unit.get_description() or ''
            weight = operation_item.quantity * unitary_weight
            vol = NFeVolume(quantity=operation_item.quantity, unit=unit,
                            net_weight=weight, gross_weight=weight)
            self._nfe_data.append(vol)

    def _add_billing_data(self):
        cob = NFeBilling()
        self._nfe_data.append(cob)

        operation_total = self._order.invoice_total
        items_total = self._order.invoice_subtotal

        fat = NFeInvoice(int(self._order.identifier), items_total,
                         self._order.discount_value, operation_total)
        self._nfe_data.append(fat)

        payments = self._order.payments or []
        for i, p in enumerate(payments):
            dup = NFeDuplicata(int(p.identifier), p.due_date, p.value)
            self._nfe_data.append(dup)

    def _add_additional_information(self, operation_items):
        fisco_info = generate_ibpt_message(operation_items)
        fisco_info += sysparam.get_string('NFE_FISCO_INFORMATION')
        comments = self._order.comments
        # The SEFAZ software, do not accepts '\n' in the additional information field.
        fisco_info = fisco_info.replace('\n', ' ')
        if isinstance(comments, basestring):
            notes = comments.replace('\n', ' ')
        else:
            notes = ' / '.join(c.comment.replace('\n', ' ') for c in self._order.comments)
        nfe_info = NFeAdditionalInformation(fisco_info, notes)
        self._nfe_data.append(nfe_info)

#
# NF-e XML Groups
#


class BaseNFeXMLGroup(object):
    """Base XML group class.
    A XML group is a helper interface to xml.etree.Element hierarchy of
    several elements. Example:
    <root>
        <child1>default</child1>
    </root>

    @cvar tag: the root element of the hierarchy.
    @cvar txttag: the root element of the hierarchy used in the text format,
                  mainly used to export the NF-e.
    @cvar attributes: a list of tuples containing the child name and the
                      default value.
    """
    tag = u''
    txttag = u''
    attributes = []

    def __init__(self):
        self._element = None
        self._data = dict(self.attributes)
        self._children = []

    #
    # Properties
    #

    @property
    def element(self):
        if self._element is not None:
            return self._element

        self._element = ElementTree.Element(self.tag)
        for key, value in self.attributes:
            element_value = self._data[key] or value
            # ignore empty values
            if element_value is None:
                continue

            sub_element = ElementTree.Element(key)
            sub_element.text = self.escape(str(element_value))
            self._element.append(sub_element)

        return self._element

    #
    # Public API
    #

    def append(self, element):
        self._children.append(element)
        self.element.append(element.element)

    def get_children(self):
        return self._children

    def get_attr(self, attr):
        return self._data[attr]

    def set_attr(self, attr, value):
        self._data[attr] = value

    def format_date(self, date):
        # Pg. 93 (and others)
        return date.strftime('%Y-%m-%d')

    def format_datetime(self, date):
        return date.replace(tzinfo=tzlocal(), microsecond=0).isoformat()

    def format_value(self, value, precision=2):
        _format = Decimal('10e-%d' % precision)
        return value.quantize(_format)

    def escape(self, string):
        # Pg. 71
        return escape(string)

    def as_txt(self):
        """Returns the group as text, in the format expected to be accepted by
        the importer of the current NF-e management software provided by the
        government.
        If the element do not a txttag attribute value, it will be ignored.
        Subclasses should might override this method to handle more complex
        outputs.
        @returns: a string with the element in text format.
        """
        if not self.txttag:
            return ''

        txt = '%s|' % self.txttag
        for attr, default in self.attributes:
            # use the current value, not the default.
            value = self.get_attr(attr)
            txt += '%s|' % value
        return txt + '\n'

    def __str__(self):
        return nfe_tostring(self.element)


# Pg. 92
class NFeData(BaseNFeXMLGroup):
    """
    - Attributes:

        - versao: Versao do leiaute.
        - Id: Chave de acesso da NF-e precedida do literal 'NFe'.
    """
    tag = 'infNFe'
    txttag = 'A'

    def __init__(self, key):
        BaseNFeXMLGroup.__init__(self)
        self.element.set('xmlns', 'http://www.portalfiscal.inf.br/nfe')
        self.element.set('versao', u'3.10')

        # Pg. 92
        assert len(key) == 44

        value = u'NFe%s' % key
        self.element.set('Id', value)

    def get_id_value(self):
        return self.element.get('Id')

    def as_txt(self):
        txt = u'%s|%s|%s|\n' % (self.txttag, self.element.get('versao'),
                                self.get_id_value())
        for child in self.get_children():
            txt += child.as_txt()

        return txt


class NFeIdentification(BaseNFeXMLGroup):
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
            substituição ao modelo 1 ou 1A. # XXX: Para NFC-e, o modelo é 65
        - serie: Série do Documento Fiscal, informar 0 (zero) para série
                 única.
        - nNF: Número do documento fiscal.
        - dhEmi: Data de emissão do documento fiscal.
        - dhSaiEnt: Data e hora da saída (opcional).
        - tpNF: Tipo de documento fiscal.
                0 - entrada
                1 - saída (default)
        - idDest: Identificador destino (1/2/3 - Interna/Interstadual/Exterior)
        - cMunFG: Código do município de ocorrência do fato gerador.
        - tpImp: Formato de impressão do DANFE.
                 1 - Retrato
                 2 - Paisagem (default)
                 3 - Simplificado;
                 4 - Danfe NFC-e
                 5 - Danfe NFC-e em msg eletronica (ver doc)
        - tpEmis: Forma de emissão da NF-e
                  1 - Normal (default)
                  2 - Contingência FS
                  3 - Contingência SCAN
                  4 - Contingência DPEC
                  5 - Contingência FS-DA
                  6 - Contingência SVC-AN
                  7 - Contingência SVC-RS
                  9 - Contingência off-line da NFC-e
        - cDV: Dígito verificador da chave de acesso da NF-e.
        - tpAmb: Identificação do ambiente.
                 1 - Produção
                 2 - Homologação
        - finNFe: Finalidade de emissão da NF-e.
                  1 - NF-e normal (default)
                  2 - NF-e complementar
                  3 - NF-e de ajuste
                  4 - Devolução de mercadoria
        - indFinal: Indica operação com consumidor final (0 - normal, 1 Consum.
        Final)
        - indPres: Indica presença do comprador no momento da operação
            0 - Não se aplica
            1 - presencial
            2 - não presencial, pela internet
            3 - não presencial, teleatendimento
            4 - NFC-e em entrga a domicilio
            9 - Não presencial - outros
        - procEmi: Identificador do processo de emissão da NF-e.
                   0 - emissãp da NF-e com aplicativo do contribuinte
                   1 - NF-e avulsa pelo fisco
                   2 - NF-e avulsa pelo contribuinte com certificado através
                       do fisco
                   3 - NF-e pelo contribuinte com aplicativo do fisco.
                       (default).
        - verProc: Identificador da versão do processo de emissão (versão do
                   aplicativo emissor de NF-e)

        Verificar documentação para tags sobre entrada em contingencia
    """
    tag = u'ide'
    attributes = [(u'cUF', ''),
                  (u'cNF', ''),
                  (u'natOp', 'venda'),
                  (u'indPag', '0'),
                  (u'mod', '55'),
                  (u'serie', '0'),
                  (u'nNF', ''),
                  (u'dhEmi', ''),
                  (u'dhSaiEnt', ''),
                  (u'tpNF', '1'),
                  (u'idDest', '1'),
                  (u'cMunFG', ''),
                  (u'tpImp', '2'),
                  (u'tpEmis', '1'),
                  (u'cDV', ''),
                  # TODO: Change tpAmb=1 in the final version.
                  (u'tpAmb', '1'),
                  (u'finNFe', '1'),
                  (u'indFinal', '0'),  # FIXME
                  (u'indPres', '0'),  # FIXME
                  (u'procEmi', '3'),
                  (u'verProc', ''),
                  (u'dhCont', ''),
                  (u'xJust', '')]
    txttag = 'B'
    danfe_orientation = {
        NFeDanfeOrientation.PORTRAIT: '1',
        NFeDanfeOrientation.LANDSCAPE: '2',
    }

    def __init__(self, cUF, branch_location, recipient_location, series, nnf,
                 emission_date, payments, orientation, ecf_info, nat_op, tpnf):
        BaseNFeXMLGroup.__init__(self)

        self.set_attr('cUF', cUF)
        # Pg. 92: Random number of 8-digits. (This used to be 9, but was
        # changed to 8 in nfe 2.0)
        self.set_attr('cNF', self._get_random_cnf())

        payment_type = 1
        # FIXME:Improve the way to check the payment_type ('indPag' attribute).
        # We must consider card payment method, as cash payment ('à vista')
        installments = len(payments)
        if installments == 1:
            payment = payments[0]
            if (payment.paid_date and
                    payment.paid_date.date() == datetime.date.today()):
                payment_type = 0
        self.set_attr('indPag', payment_type)

        if branch_location.country != recipient_location.country:
            idDest = 3
        elif branch_location.state != recipient_location.state:
            idDest = 2
        else:
            idDest = 1
        self.set_attr('idDest', idDest)

        self.set_attr('nNF', nnf)
        self.set_attr('serie', series)
        self.set_attr('dhEmi', self.format_datetime(emission_date))
        self.set_attr('tpNF', tpnf)
        self.set_attr('cMunFG', str(branch_location.city_code or ''))
        self.set_attr('tpImp', self.danfe_orientation[orientation])
        self.set_attr('natOp', nat_op[:60] or 'Venda')

        if tpnf == INVOICE_IN:
            self.set_attr('finNFe', '4')

        if ecf_info:
            info = NFeEcfInfo(ecf_info.number, ecf_info.coo)
            self.append(info)

    def as_txt(self):
        base = BaseNFeXMLGroup.as_txt(self)
        children = self.get_children()
        if children:
            return base + children[0].as_txt()
        return base

    def _get_random_cnf(self):
        return random.randint(10000000, 99999999)


class NFeEcfInfo(BaseNFeXMLGroup):
    """
    - Attributes:
        - mod: preencher com 2D no caso de cupom fiscal emitido por ecf
        - nECF: numero de ordem sequencial da ECF
        - nCOO: numero do coo do cupom impresso
    """
    attributes = [(u'mod', '2D'),
                  (u'nECF', ''),
                  (u'nCOO', '')]

    txttag = 'BA|\nBA20'

    def __init__(self, n_ecf, coo):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('nECF', n_ecf)
        self.set_attr('nCOO', coo)


class NFeAddress(BaseNFeXMLGroup):
    """
    - Attributes:
        - xLgr: logradouro.
        - nro: número.
        - xCpl: complemento
        - xBairro: bairro.
        - cMun: código do município.
        - xMun: nome do município.
        - UF: sigla da UF. Informar EX para operações com o exterior.
        - CEP: código postal.
        - CPais: código do país.
        - XPais: nome do país.
        - Fone: número do telefone.
    """
    # TODO: For countries different of Brazil.
    # The fields -> xMun, UF, CPais and XPais must be represented
    # respectively by 'Exterior', 'EX', Country code and Country name.
    attributes = [(u'xLgr', ''),
                  (u'nro', ''),
                  (u'xCpl', ''),
                  (u'xBairro', ''),
                  (u'cMun', ''),
                  (u'xMun', ''),
                  (u'UF', ''),
                  (u'CEP', ''),
                  (u'CPais', '1058'),
                  (u'XPais', 'BRASIL'),
                  (u'Fone', '')]

    def __init__(self, tag, address, phone_number=''):
        self.tag = tag
        BaseNFeXMLGroup.__init__(self)

        # FIXME: We should make sure that there is an address in Stoq before
        # creating the sale (or whatever other operation)
        if not address:
            return
        location = address.city_location
        postal_code = ''.join([i for i in
                               address.postal_code if i in '1234567890'])

        self.set_attr('xLgr', address.street[:60])
        self.set_attr('nro', address.streetnumber or '0')
        self.set_attr('xCpl', address.complement)
        self.set_attr('xBairro', address.district)
        self.set_attr('xMun', location.city)
        self.set_attr('cMun', str(location.city_code or ''))
        self.set_attr('UF', location.state)
        self.set_attr('CEP', postal_code)
        # Only export the phone number if it has 6 digits or more
        if len(str(phone_number)) > 6:
            self.set_attr('Fone', phone_number)


# Pg. 96
class NFeIssuer(BaseNFeXMLGroup):
    """
    - Attributes:
        - CNPJ: CNPJ do emitente.
        - xNome: Razão social ou nome do emitente
        - IE: inscrição estadual
    """
    tag = u'emit'
    address_tag = u'enderEmit'
    attributes = [(u'CNPJ', None),
                  (u'CPF', None),
                  (u'xNome', ''),
                  (u'CRT', ''),
                  ]
    txttag = 'C'
    address_txt_tag = 'C05'
    doc_cnpj_tag = 'C02'
    doc_cpf_tag = 'C02a'

    def __init__(self, name, cpf=None, cnpj=None, state_registry=None,
                 crt=None):
        BaseNFeXMLGroup.__init__(self)
        if cnpj is not None:
            self.set_attr('CNPJ', cnpj)
        else:
            self.set_attr('CPF', cpf)

        self.set_attr('xNome', name[:60])
        self.set_attr('CRT', crt)

        self._ie = state_registry

    def set_address(self, address, phone_number=None):
        self._address = NFeAddress(self.address_tag, address,
                                   phone_number or '')
        self._address.txttag = self.address_txt_tag
        self.append(self._address)
        # If we set IE in the __init__, the order will not be correct. :(
        ie_element = ElementTree.Element(u'IE')
        ie_element.text = self._ie
        self.element.append(ie_element)

    def get_doc_txt(self):
        doc_value = self.get_attr('CNPJ')
        if doc_value is not None:
            doc_tag = self.doc_cnpj_tag
        else:
            doc_tag = self.doc_cpf_tag
            doc_value = self.get_attr('CPF')
        return '%s|%s|\n' % (doc_tag, doc_value, )

    def as_txt(self):
        if self.get_attr('CNPJ'):
            ie = self._ie or 'ISENTO'
        else:
            ie = ''
        crt = self.get_attr('CRT') or ''
        base = '%s|%s||%s||||%s|\n' % (self.txttag, self.get_attr('xNome'),
                                       ie, crt)
        return base + self.get_doc_txt() + self._address.as_txt()


# Pg. 99
class NFeRecipient(NFeIssuer):
    """
    - Txttag(E) attributes:
        - xNome: Razão social ou nome do emitente.
        - indIEDest: Indicador da IE do Destinatário.
            1 - Contribuinte ICMS
            2 - Contribuinte isento de Inscrição no cadastro de Contribuinte do ICMS
            9 - Não Contribuinte, que pode ou não possuir Inscrição Estadual no
                Cadastro de Contribuintes do ICMS.
        - IE: Inscrição estadual.
        - ISUF: Inscrição Suframa.
        - IM: Inscrição Municipal do Tomador do Serviço.
        - email: email.
    """
    tag = 'dest'
    address_tag = u'enderDest'
    txttag = 'E'
    address_txt_tag = 'E05'
    doc_cnpj_tag = 'E02'
    doc_cpf_tag = 'E03'

    def __init__(self, name, cpf=None, cnpj=None, state_registry=None,
                 email=None):
        NFeIssuer.__init__(self, name=name, cpf=cpf, cnpj=cnpj,
                           state_registry=state_registry)
        if email is not None:
            self.set_attr('email', email)

    def as_txt(self):
        if self.get_attr('CNPJ'):
            ie = self._ie or 'ISENTO'
        else:
            ie = ''

        if ie and ie != 'ISENTO':
            iedest = 1
        elif self.get_attr('CNPJ'):
            iedest = 2
            # In version 3.10, the field IE is not informed with literal 'ISENTO'.
            ie = ''
        else:
            iedest = 9

        base = '%s|%s|%s|%s|||%s\n' % (self.txttag, self.get_attr('xNome'), iedest,
                                       ie, self.get_attr('email'))
        return base + self.get_doc_txt() + self._address.as_txt()

# Pg. 102


class NFeProduct(BaseNFeXMLGroup):
    """
    - Attributes:
        - nItem: número do item
    """
    tag = u'det'
    txttag = 'H'

    def __init__(self, number):
        BaseNFeXMLGroup.__init__(self)
        # "nItem" is part of "det", not a regular attribute. So we need to
        # ensure it is a string.
        self.element.set('nItem', str(number))

    def add_product_details(self, code, description, cfop, quantity, price,
                            unit, barcode, ncm, ex_tipi, genero):
        details = NFeProductDetails(code, description, cfop, quantity, price,
                                    unit, barcode, ncm, ex_tipi, genero)
        self.append(details)

    def add_tax_details(self, operation_item, crt, coupon=None):
        nfe_tax = NFeTax()

        # TODO: handle service tax (ISS).

        # If the operation was also printed on a coupon, then we cannot add icms
        # details to the NF-e, we should add a empty empty icms informatio tag
        if coupon:
            # in this case, the cst should be 90 ou 900 (for the 'SIMPLES'). and
            # the values should be empty (note that they should not be 0.00,
            # since that those values may be invalid. Just '')
            operation_icms = Settable()
            operation_icms.csosn = 900
            operation_icms.cst = 90
            # We still have to export the 'orig' field of the icms info.
            operation_icms.orig = operation_item.icms_info.orig
        else:
            operation_icms = operation_item.icms_info

        if operation_icms:
            nfe_icms = NFeICMS(operation_icms, crt)
            nfe_tax.append(nfe_icms)

        invoice_ipi = operation_item.ipi_info
        if invoice_ipi:
            nfe_ipi = NFeIPI(invoice_ipi)
            nfe_tax.append(nfe_ipi)

        if operation_item.pis_info and operation_item.pis_info.cst:
            nfe_pis = NFePIS(operation_item)
            nfe_tax.append(nfe_pis)

        if operation_item.cofins_info and operation_item.cofins_info.cst:
            nfe_cofins = NFeCOFINS(operation_item)
            nfe_tax.append(nfe_cofins)

        self.append(nfe_tax)

    def as_txt(self):
        base = '%s|%s||\n' % (self.txttag, self.element.get('nItem'), )
        details, tax = self.get_children()
        tax_txt = 'M|\nN|\n%s' % tax.as_txt()
        return base + details.as_txt() + tax_txt


# Pg. 102
class NFeProductDetails(BaseNFeXMLGroup):
    """
    - Attributes:
        - cProd: Código do produto ou serviço. Preencher com CFOP caso se
                 trate de itens não relacionados com mercadorias/produtos e
                 que o contribuinte não possua codificação própria.

        - cEAN: GTIN (Global Trade Item Number) do produto, antigo código EAN
                ou código de barras.

        - xProd: Descrição do produto ou serviço.

        - NCM: Código NCM. Preencher de acordo com a tabela de capítulos da
                NCM. EM caso de serviço, não incluir a tag.

        - CFOP: Código fiscal de operações e prestações. Serviço, não incluir
                a tag.

        - uCom: Unidade comercial. Informar a unidade de comercialização do
                produto.

        - qCom: Quantidade comercial. Informar a quantidade de comercialização
                do produto.

        - vUnCom: Valor unitário de comercialização. Informar o valor unitário
                  de comercialização do produto.

        - vProd: Valor total bruto dos produtos ou serviços.

        - cEANTrib: GTIN da unidade tributável, antigo código EAN ou código de
                    barras.

        - uTrib: Unidade tributável.

        - qTrib: Quantidade tributável.

        - vUnTrib: Valor unitário de tributação.
    """
    tag = u'prod'
    attributes = [(u'cProd', ''),
                  (u'cEAN', ''),
                  (u'xProd', ''),
                  (u'NCM', ''),
                  (u'EXTIPI', ''),
                  (u'CFOP', ''),
                  (u'uCom', ''),
                  (u'qCom', ''),
                  (u'vUnCom', ''),
                  (u'vProd', ''),
                  (u'cEANTrib', ''),
                  (u'uTrib', ''),
                  (u'qTrib', ''),
                  (u'vUnTrib', ''),
                  (u'vFrete', ''),
                  (u'vSeg', ''),
                  (u'vDesc', ''),
                  (u'vOutro', ''),
                  (u'indTot', '1'),
                  (u'xPed', ''),
                  (u'nItemPed', ''),
                  ]
    txttag = 'I'

    def __init__(self, code, description, cfop, quantity, price, unit,
                 barcode, ncm, ex_tipi, genero):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('cProd', code)

        if barcode and len(barcode) in (8, 12, 13, 14):
            self.set_attr('cEAN', barcode)

        self.set_attr('xProd', description)
        self.set_attr('NCM', ncm or '')
        self.set_attr('EXTIPI', ex_tipi or '')
        # XXX: Genero was removed from nfe 2.0. Figure out what to do with
        # the value from the product
        # self.set_attr('genero', genero or '')

        self.set_attr('CFOP', cfop)
        self.set_attr('vUnCom', self.format_value(price, precision=4))
        self.set_attr('vUnTrib', self.format_value(price, precision=4))
        self.set_attr('vProd', self.format_value(quantity * price))
        self.set_attr('qCom', self.format_value(quantity, precision=4))
        self.set_attr('qTrib', self.format_value(quantity, precision=4))
        self.set_attr('uTrib', unit or 'un')
        self.set_attr('uCom', unit or 'un')


#
#   Tax details
#


# Pg. 107
class NFeTax(BaseNFeXMLGroup):
    tag = 'imposto'
    taxtag = 'M|\nN|\n'

    def as_txt(self):
        base = '%s' % self.txttag
        for i in self.get_children():
            base += i.as_txt()
        return base


# Pg. 107
class NFeICMS(BaseNFeXMLGroup):
    tag = 'ICMS'

    def __init__(self, operation_icms_info, crt):
        BaseNFeXMLGroup.__init__(self)

        # Simples Nacional
        if crt in [1, 2]:
            icms_tag_class = NFE_ICMS_CSOSN_MAP.get(operation_icms_info.csosn)
        else:  # Regime normal
            icms_tag_class = NFE_ICMS_CST_MAP.get(operation_icms_info.cst)

        if icms_tag_class:
            icms_tag = icms_tag_class(operation_icms_info)
            self.append(icms_tag)

    def as_txt(self):
        children = self.get_children()
        if not children:
            return ''
        icms = children[0]
        return icms.as_txt()


class BaseNFeICMS(BaseNFeXMLGroup):
    # (name, precision)
    INFO_NAME_MAP = {
        'orig': ('orig', None),
        'CST': ('cst', None),
        'modBC': ('mod_bc', None),
        'modBCST': ('mod_bc_st', None),

        'vBC': ('v_bc', 2),
        'vBCST': ('v_bc_st', 2),
        'vICMS': ('v_icms', 2),
        'vICMSST': ('v_icms_st', 2),
        'vICMSDeson': ('v_icms_st_deson', 2),
        'vICMSOp': ('v_icms_op', 2),
        'vICMSDif': ('v_icms_dif', 2),

        'pICMS': ('p_icms', 2),
        'pMVAST': ('p_mva_st', 2),
        'pRedBC': ('p_red_bc', 2),
        'pRedBCST': ('p_red_bc_st', 2),
        'pICMSST': ('p_icms_st', 2),
        'pDif': ('p_dif', 2),

        # Simples Nacional
        'CSOSN': ('csosn', 0),
        'pCredSN': ('p_cred_sn', 2),
        'vCredICMSSN': ('v_cred_icms_sn', 2),
        'vBCSTRet': ('v_bc_st_ret', 2),
        'vICMSSTRet': ('v_icms_st_ret', 2),

        # This are not supported but still need to be here, so they are included
        # in the exported txt.
        'motDesICMS': ('mot_des_icms', None),
        'UFST': ('ufst', None),
        'pBCOp': ('p_bc_op', 2),
        'vBCSTDest': ('v_bc_st_dest', 2),
        'vICMSSTDest': ('v_icms_st_dest', 2),

    }

    def __init__(self, operation_icms_info):
        BaseNFeXMLGroup.__init__(self)

        for (name, default) in self.attributes:
            info_name, precision = self.INFO_NAME_MAP.get(name)
            if not info_name:
                continue

            value = getattr(operation_icms_info, info_name, '')
            # Only format if the value is a number
            if precision is not None and isinstance(value, Decimal):
                value = self.format_value(value, precision)
            if value is None:
                value = ''
            self.set_attr(name, value)


class NFeICMS00(BaseNFeICMS):
    """Tributada integralmente (CST=00).

    - Attributes:

        - orig: Origem da mercadoria.
                0 – Nacional
                1 – Estrangeira – Importação direta
                2 – Estrangeira – Adquirida no mercado interno
        - CST: Tributação do ICMS - 00 Tributada integralmente.
        - modBC: Modalidade de determinação da BC do ICMS.
                 0 - Margem Valor Agregado (%) (default)
                 1 - Pauta (Valor)
                 2 - Preço Tabelado Máx. (valor)
                 3 - Valor da operação
        - vBC: Valor da BC do ICMS.
        - pICMS: Alíquota do imposto.
        - vICMS: Valor do ICMS
    """
    tag = 'ICMS00'
    txttag = 'N02'
    attributes = [(u'orig', None),
                  (u'CST', '00'),
                  (u'modBC', None),
                  (u'vBC', None),
                  (u'pICMS', None),
                  (u'vICMS', None)]

    def __init__(self, operation_icms_info):
        BaseNFeICMS.__init__(self, operation_icms_info)
        # We should fix cst here, otherwise, it will be just 0 (one zero).
        self.set_attr(u'CST', '00')


# Pg. 108
class NFeICMS10(BaseNFeICMS):
    """Tributada com cobrança do ICMS por substituição tributária (CST=10).
    - Attributes:

        - modBCST: Modalidade de determinação da BC do ICMS ST.
                   0 - Preço tabelado ou máximo sugerido
                   1 - Lista negativa (valor)
                   2 - Lista positiva (valor)
                   3 - Lista neutra (valor)
                   4 - Margem valor agregado (%)
                   5 - Pauta (valor)
        - pMVAST: Percentual da margem de valor adicionado do ICMS ST.
        - pRedBCST: Percentual da redução de BC do ICMS ST.
        - vBCST: Valor da BC do ICMS ST.
        - pICMSST: Alíquota do imposto do ICMS ST.
        - vICMSST: Valor do ICMS ST.
    """
    tag = 'ICMS10'
    txttag = 'N03'
    attributes = NFeICMS00.attributes[:]
    attributes.extend([(u'modBCST', ''),
                       (u'pMVAST', ''),
                       (u'pRedBCST', ''),
                       (u'vBCST', ''),
                       (u'pICMSST', ''),
                       (u'vICMSST', '', )])


# Pg. 108
class NFeICMS20(BaseNFeICMS):
    """Tributada com redução de base de cálculo (CST=20).

    - Attributes:
        - pRedBC: Percentual de Redução de BC.
    """
    tag = 'ICMS20'
    txttag = 'N04'
    attributes = NFeICMS00.attributes[:]
    attributes = [(u'orig', ''),
                  (u'CST', '00'),
                  (u'modBC', ''),
                  (u'pRedBC', ''),
                  (u'vBC', ''),
                  (u'pICMS', ''),
                  (u'vICMS', ''),
                  (u'vICMSDeson', ''),
                  (u'motDesICMS', '')]


class NFeICMS30(BaseNFeICMS):
    """Isenta ou não tributada e com cobrança do ICMS por substituição
    tributária (CST=30).
    """
    tag = 'ICMS30'
    txttag = 'N05'
    attributes = [(u'orig', ''),
                  (u'CST', '00'),
                  (u'modBCST', ''),
                  (u'pMVAST', ''),
                  (u'pRedBCST', ''),
                  (u'vBCST', ''),
                  (u'pICMSST', ''),
                  (u'vICMSST', ''),
                  (u'vICMSDeson', ''),
                  (u'motDesICMS', '')]


# Pg. 111
class NFeICMS40(BaseNFeICMS):
    """Isenta (CST=40), Não tributada (CST=41), Suspensão (CST=50).
    """
    tag = 'ICMS40'
    txttag = 'N06'
    attributes = [(u'orig', ''),
                  (u'CST', ''),
                  (u'vICMSDeson', ''),
                  (u'motDesICMS', '')]


class NFeICMS51(BaseNFeICMS):
    tag = 'ICMS51'
    txttag = 'N07'
    attributes = [(u'orig', ''),
                  (u'CST', ''),
                  (u'modBC', ''),
                  (u'pRedBC', ''),
                  (u'vBC', ''),
                  (u'pICMS', ''),
                  (u'vICMSOp', ''),
                  (u'pDif', ''),
                  (u'vICMSDif', ''),
                  (u'vICMS', ''),
                  ]


class NFeICMS60(BaseNFeICMS):
    tag = 'ICMS60'
    txttag = 'N08'
    attributes = [(u'orig', ''),
                  (u'CST', ''),
                  (u'vBCSTRet', ''),
                  (u'vICMSSTRet', '')]


class NFeICMS70(BaseNFeICMS):
    tag = 'ICMS70'
    txttag = 'N09'
    attributes = [(u'orig', ''),
                  (u'CST', ''),
                  (u'modBC', ''),
                  (u'pRedBC', ''),
                  (u'vBC', ''),
                  (u'pICMS', ''),
                  (u'vICMS', ''),
                  (u'modBCST', ''),
                  (u'pMVAST', ''),
                  (u'pRedBCST', ''),
                  (u'vBCST', ''),
                  (u'pICMSST', ''),
                  (u'vICMSST', ''),
                  (u'vICMSDeson', ''),
                  (u'motDesICMS', '')]


class NFeICMS90(BaseNFeICMS):
    tag = 'ICMS90'
    txttag = 'N10'
    attributes = [(u'orig', ''),
                  (u'CST', ''),
                  (u'modBC', ''),
                  (u'vBC', ''),
                  (u'pRedBC', ''),
                  (u'pICMS', ''),
                  (u'vICMS', ''),
                  (u'modBCST', ''),
                  (u'pMVAST', ''),
                  (u'pRedBCST', ''),
                  (u'vBCST', ''),
                  (u'pICMSST', ''),
                  (u'vICMSST', ''),
                  (u'vICMSDeson', ''),
                  (u'motDesICMS', '')]


class NFeICMSPart(BaseNFeICMS):
    """Partilha do ICMS entre a UF de origem e UF de destino ou a UF
    definida na legislação.
    """

    tag = 'ICMSPart'
    txttag = 'N10a'
    attributes = NFeICMS90.attributes[:]
    attributes.extend([(u'pBCOp', ''),
                       (u'UFST', '')])


class NFeICMSST(BaseNFeICMS):
    """ICMS ST – repasse de ICMS ST retido anteriormente em operações
    interestaduais com repasses através do Substituto Tributário.
    """
    tag = 'ICMSST'
    txttag = 'N10b'
    attributes = [(u'orig', ''),
                  (u'CST', ''),
                  (u'vBCSTRet', ''),
                  (u'vICMSSTRet', ''),
                  (u'vBCSTDest', ''),
                  (u'vICMSSTDest', '')]


#
# Simples Nacional
#

class NFeICMSSN101(BaseNFeICMS):
    """Grupo CRT=1 – Simples Nacional e CSOSN=101
    """

    tag = 'ICMSSN101'
    txttag = 'N10c'
    attributes = [(u'orig', ''),
                  (u'CSOSN', ''),
                  (u'pCredSN', ''),
                  (u'vCredICMSSN', ''),
                  ]


class NFeICMSSN102(BaseNFeICMS):
    """Grupo CRT=1 – Simples Nacional e CSOSN=102, 103, 300, 400
    """

    tag = 'ICMSSN102'
    txttag = 'N10d'
    attributes = [(u'orig', ''),
                  (u'CSOSN', ''),
                  ]


class NFeICMSSN201(BaseNFeICMS):
    """Grupo CRT=1 – Simples Nacional e CSOSN=201
    """

    tag = 'ICMSSN201'
    txttag = 'N10e'
    attributes = [(u'orig', ''),
                  (u'CSOSN', ''),
                  (u'modBCST', ''),
                  (u'pMVAST', ''),
                  (u'pRedBCST', ''),
                  (u'vBCST', ''),
                  (u'pICMSST', ''),
                  (u'vICMSST', ''),
                  (u'pCredSN', ''),
                  (u'vCredICMSSN', ''),
                  ]


class NFeICMSSN202(BaseNFeICMS):
    """Grupo CRT=1 – Simples Nacional e CSOSN=202, 203
    """

    tag = 'ICMSSN202'
    txttag = 'N10f'
    attributes = [(u'orig', ''),
                  (u'CSOSN', ''),
                  (u'modBCST', ''),
                  (u'pMVAST', ''),
                  (u'pRedBCST', ''),
                  (u'vBCST', ''),
                  (u'pICMSST', ''),
                  (u'vICMSST', ''),
                  ]


class NFeICMSSN500(BaseNFeICMS):
    """Grupo CRT=1 – Simples Nacional e CSOSN=500
    """

    tag = 'ICMSSN500'
    txttag = 'N10g'
    attributes = [(u'orig', ''),
                  (u'CSOSN', ''),
                  (u'vBCSTRet', ''),
                  (u'vICMSSTRet', ''),
                  ]


class NFeICMSSN900(BaseNFeICMS):
    """Grupo CRT=1 – Simples Nacional e CSOSN=900
    """

    tag = 'ICMSSN900'
    txttag = 'N10h'
    attributes = [(u'orig', ''),
                  (u'CSOSN', ''),
                  (u'modBC', ''),
                  (u'vBC', ''),
                  (u'pRedBC', ''),
                  (u'pICMS', ''),
                  (u'vICMS', ''),
                  (u'modBCST', ''),
                  (u'pMVAST', ''),
                  (u'pRedBCST', ''),
                  (u'vBCST', ''),
                  (u'pICMSST', ''),
                  (u'vICMSST', ''),
                  (u'pCredSN', ''),
                  (u'vCredICMSSN', ''),
                  ]


#
#   End of ICMS
#
#   Begin IPI
#

class NFeIPI(BaseNFeXMLGroup):
    tag = u'IPI'
    txttag = 'O'

    attributes = [(u'ClEnq', ''),
                  (u'CNPJProd', ''),
                  (u'CSelo', ''),
                  (u'QSelo', ''),
                  (u'CEnq', '')]

    def __init__(self, ipi_info):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('ClEnq', ipi_info.cl_enq or '')
        self.set_attr('CNPJProd', ipi_info.cnpj_prod or '')
        self.set_attr('CSelo', ipi_info.c_selo or '')
        self.set_attr('QSelo', ipi_info.q_selo or '')
        self.set_attr('CEnq', ipi_info.c_enq or '')

        if ipi_info.cst in (0, 49, 50, 99):
            self.append(NFeIPITrib(ipi_info))
        else:
            self.append(NFeIPINT(ipi_info))

    def as_txt(self):
        base = BaseNFeXMLGroup.as_txt(self)
        ipi = self.get_children()[0]
        return base + ipi.as_txt()


class NFeIPITrib(BaseNFeXMLGroup):
    tax = u'IPITrib'
    txttag = 'O07'
    # The NF-e documentation is wrong:
    # 'vIPI' is represented on tags 'O10' and 'O11', but when we try
    # import the .txt in SEFAZ emissor, the IPI value is not imported.
    # The 'vIPI' only was imported sucessfully on tag 'O07'.
    attributes = [(u'CST', ''),
                  (u'vIPI', '')]

    def __init__(self, ipi_info):
        BaseNFeXMLGroup.__init__(self)
        if ipi_info.cst is not None:
            self.set_attr('CST', '%02d' % ipi_info.cst)

        if ipi_info.calculo == ipi_info.CALC_ALIQUOTA:
            self.append(NFeIPITribAliq(ipi_info))
        else:
            self.append(NFeIPITribUnid(ipi_info))
        self.set_attr('vIPI', self.format_value(ipi_info.v_ipi))

    def as_txt(self):
        base = BaseNFeXMLGroup.as_txt(self)
        ipi_trib = self.get_children()[0]
        return base + ipi_trib.as_txt()


class NFeIPITribAliq(BaseNFeXMLGroup):
    tax = u'IPITrib'
    txttag = 'O10'
    attributes = [(u'vBC', ''),
                  (u'pIPI', '')]

    def __init__(self, ipi_info):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('vBC', "%.2f" % ipi_info.v_bc)
        self.set_attr('pIPI', ipi_info.p_ipi or '')


class NFeIPITribUnid(BaseNFeXMLGroup):
    tax = u'IPITrib'
    txttag = 'O11'
    attributes = [(u'qUnid', ''),
                  (u'vUnid', '')]

    def __init__(self, ipi_info):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('qUnid', ipi_info.q_unid or '')
        self.set_attr('vUnid', self.format_value(ipi_info.v_unid, precision=4))


class NFeIPINT(BaseNFeXMLGroup):
    tax = u'IPINT'
    txttag = 'O08'
    attributes = [(u'CST', '')]

    def __init__(self, ipi_info):
        BaseNFeXMLGroup.__init__(self)
        if ipi_info.cst:
            self.set_attr('CST', '%02d' % ipi_info.cst)


#
#   End of IPI
#


class NFePIS(BaseNFeXMLGroup):
    tag = u'PIS'
    txttag = 'Q'

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        pis_info = sale_item.pis_info
        pis_class = NFE_PIS_MAP.get(pis_info.cst)
        self.append(pis_class(sale_item))

    def as_txt(self):
        base = '%s|\n' % (self.txttag)
        pis = self.get_children()[0]
        return base + pis.as_txt()


# Pg. 117, 118
class NFePISAliq(BaseNFeXMLGroup):
    """
    - Attributes:
        - CST: Código de Situação tributária do PIS.
               01 - operação tributável (base de cáculo - valor da operação
               normal (cumulativo/não cumulativo))
               02 - operação tributável (base de cálculo = valor da operação
               (alíquota diferenciada))

        - vBC: Valor da base de cálculo do PIS.

        - pPIS: Alíquota do PIS (em percentual).

        - vPIS: Valor do PIS.
    """
    tag = u'PISAliq'
    txttag = 'Q02'
    attributes = [(u'CST', ''),
                  (u'vBC', '0'),
                  (u'pPIS', '0'),
                  (u'vPIS', '0')]

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('CST', format_cst(sale_item.pis_info.cst))
        self.set_attr('vBC', self.format_value(sale_item.pis_info.v_bc, 2))
        self.set_attr('pPIS', sale_item.pis_info.p_pis)
        self.set_attr('vPIS', self.format_value(sale_item.pis_info.v_pis, 2))

    def as_txt(self):
        base = '%s|%s|%s|%s|%s|\n' % (self.txttag,
                                      self.get_attr('CST'),
                                      self.get_attr('vBC'),
                                      self.get_attr('pPIS'),
                                      self.get_attr('vPIS'))
        return base


class NFePISNT(BaseNFeXMLGroup):
    """Grupo de PIS nao tributada (CST 04, 06, 07, 08, 09)

    - Attributes:
        - CST: Código de situação tributária do PIS.
            04 - Operação Tributável (tributação monofásica (alíquota zero)).
            05 - Operação Tributável (substituição tributária).
            06 - Operação Tributável (alíquota zero).
            07 - Operação Isenta da Contribuição.
            08 - Operação Sem Incidência da Contribuição.
            09 - Operação com Suspensão da Contribuição.
    """
    tag = u'PISNT'
    txttag = 'Q04'
    attributes = [(u'CST', '')]

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('CST', format_cst(sale_item.pis_info.cst))

    def as_txt(self):
        base = '%s|%s|\n' % (self.txttag,
                             self.get_attr('CST'))
        return base


# Pg. 118
class NFePISOutr(BaseNFeXMLGroup):
    """Grupo de PIS Outras Operações (CST 49, 50, 51, 52, 53, 54, 55, 56, 60, 61, 62,
                                          63, 64, 65, 67, 70, 71, 72, 73, 74, 75, 98, 99)
    - Attributes:
        -CST: Código de situação tributária do PIS.
            49 - Outras Operações de Saída
            50 - Com Direito a Crédito - Vinculada Exclusivamente a Receita
                 Tributada no Mercado Interno
            51 - Operação com Direito a Crédito – Vinculada Exclusivamente a
                 Receita Não Tributada no Mercado Interno
            52 - Operação com Direito a Crédito - Vinculada Exclusivamente a
                 Receita de Exportação
            53 - Operação com Direito a Crédito - Vinculada a Receitas
                 Tributadas e Não-Tributadas no Mercado Interno
            54 - Operação com Direito a Crédito - Vinculada a Receitas
                 Tributadas no Mercado Interno e de Exportação
            55 - Operação com Direito a Crédito - Vinculada a Receitas
                 Não-Tributadas no Mercado Interno e de Exportação
            56 - Operação com Direito a Crédito - Vinculada a Receitas
                 Tributadas e Não-Tributadas no Mercado Interno, e de Exportação
            60 - Crédito Presumido - Operação de Aquisição Vinculada
                 Exclusivamente a Receita Tributada no Mercado Interno
            61 - Crédito Presumido - Operação de Aquisição Vinculada
                 Exclusivamente a Receita Não-Tributada no Mercado Interno
            62 - Crédito Presumido - Operação de Aquisição Vinculada
                 Exclusivamente a Receita de Exportação
            63 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Tributadas e Não-Tributadas no Mercado Interno
            64 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Tributadas no Mercado Interno e de Exportação
            65 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Não-Tributadas no Mercado Interno e de Exportação
            66 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Tributadas e Não-Tributadas no Mercado Interno, e de
                 Exportação
            67 - Crédito Presumido - Outras Operações
            70 - Operação de Aquisição sem Direito a Crédito
            71 - Operação de Aquisição com Isenção
            72 - Operação de Aquisição com Suspensão
            73 - Operação de Aquisição a Alíquota Zero
            74 - Operação de Aquisição sem Incidência da Contribuição
            75 - Operação de Aquisição por Substituição Tributária
            98 - Outras Operações de Entrada
            99 - Outras Operações
        - vBC: Valor da Base de Cálculo do PIS.
        - pPIS: Alíquota do PIS (em percentual).
        - vPIS: Valor do PIS.
    """
    tag = u'PISOutr'
    txttag = 'Q05'
    attributes = [(u'CST', ''),
                  (u'vBC', '0'),
                  (u'pPIS', '0'),
                  (u'vPIS', '0')]

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('CST', format_cst(sale_item.pis_info.cst))
        self.set_attr('vBC', self.format_value(sale_item.pis_info.v_bc, 2))
        self.set_attr('pPIS', sale_item.pis_info.p_pis)
        self.set_attr('vPIS', self.format_value(sale_item.pis_info.v_pis, 2))

    def as_txt(self):
        base = '%s|%s|%s|\n' % (self.txttag, self.get_attr('CST'),
                                self.get_attr('vPIS'))
        q = '%s|%s|%s|\n' % ('Q07', self.get_attr('vBC'), self.get_attr('pPIS'))
        return base + q


# Pg. 120, 121
class NFeCOFINS(BaseNFeXMLGroup):
    tag = u'COFINS'
    txttag = 'S'

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        cofins_info = sale_item.cofins_info
        cofins_class = NFE_COFINS_MAP.get(cofins_info.cst)
        self.append(cofins_class(sale_item))

    def as_txt(self):
        base = '%s|\n' % self.txttag
        cofins = self.get_children()[0]
        return base + cofins.as_txt()


# Pg. 121
class NFeCOFINSAliq(BaseNFeXMLGroup):
    """
    - Attributes:
        - CST: Código de situação tributária do COFINS.
               01 - Operação tributável (base de cálculo = valor da operação
               alíquota normal (cumulativo/não cumulativo).

               02 - Operação tributável (base de cálculo = valor da operação
               (alíquota diferenciada)).

        - vBC: Valor da base do cálculo da COFINS.
        - pCOFINS: Alíquota do COFINS (em percentual).
        - vCOFINS: Valor do COFINS.
    """
    tag = u'COFINSAliq'
    txttag = 'S02'
    attributes = [(u'CST', ''),
                  (u'vBC', '0'),
                  (u'pCOFINS', '0'),
                  (u'vCOFINS', '0')]

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('CST', format_cst(sale_item.cofins_info.cst))
        self.set_attr('vBC', self.format_value(sale_item.cofins_info.v_bc, 2))
        self.set_attr('pCOFINS', sale_item.cofins_info.p_cofins)
        self.set_attr('vCOFINS', self.format_value(sale_item.cofins_info.v_cofins, 2))

    def as_txt(self):
        base = '%s|%s|%s|%s|%s|\n' % (self.txttag,
                                      self.get_attr('CST'),
                                      self.get_attr('vBC'),
                                      self.get_attr('pCOFINS'),
                                      self.get_attr('vCOFINS'))
        return base


class NFeCOFINSNT(BaseNFeXMLGroup):
    """Grupo de COFINS nao tributada (CST 04, 06, 07, 08, 09)

    - Attributes:
        - CST: Código de situação tributária da COFINS.
            04 - Operação Tributável (tributação monofásica (alíquota zero)).
            05 - Operação Tributável (subtituição tributária)).
            06 - Operação Tributável (alíquota zero).
            07 - Operação Isenta da Contribuição.
            08 - Operação Sem Incidência da Contribuição.
            09 - Operação com Suspensão da Contribuição.
    """
    tag = u'COFINSNT'
    txttag = 'S04'
    attributes = [(u'CST', '')]

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('CST', format_cst(sale_item.cofins_info.cst))

    def as_txt(self):
        base = '%s|%s|\n' % (self.txttag,
                             self.get_attr('CST'))
        return base


# Pg. 121
class NFeCOFINSOutr(NFeCOFINSAliq):
    """Grupo de COFINS Outras Operações (CST 49, 50, 51, 52, 53, 54, 55, 56, 60, 61, 62,
                                          63, 64, 65, 67, 70, 71, 72, 73, 74, 75, 98, 99)
    - Attributes:
        -CST: Código de situação tributária da COFINS.
            49 - Outras Operações de Saída
            50 - Com Direito a Crédito - Vinculada Exclusivamente a Receita
                 Tributada no Mercado Interno
            51 - Operação com Direito a Crédito – Vinculada Exclusivamente a
                 Receita Não Tributada no Mercado Interno
            52 - Operação com Direito a Crédito - Vinculada Exclusivamente a
                 Receita de Exportação
            53 - Operação com Direito a Crédito - Vinculada a Receitas
                 Tributadas e Não-Tributadas no Mercado Interno
            54 - Operação com Direito a Crédito - Vinculada a Receitas
                 Tributadas no Mercado Interno e de Exportação
            55 - Operação com Direito a Crédito - Vinculada a Receitas
                 Não-Tributadas no Mercado Interno e de Exportação
            56 - Operação com Direito a Crédito - Vinculada a Receitas
                 Tributadas e Não-Tributadas no Mercado Interno, e de Exportação
            60 - Crédito Presumido - Operação de Aquisição Vinculada
                 Exclusivamente a Receita Tributada no Mercado Interno
            61 - Crédito Presumido - Operação de Aquisição Vinculada
                 Exclusivamente a Receita Não-Tributada no Mercado Interno
            62 - Crédito Presumido - Operação de Aquisição Vinculada
                 Exclusivamente a Receita de Exportação
            63 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Tributadas e Não-Tributadas no Mercado Interno
            64 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Tributadas no Mercado Interno e de Exportação
            65 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Não-Tributadas no Mercado Interno e de Exportação
            66 - Crédito Presumido - Operação de Aquisição Vinculada a
                 Receitas Tributadas e Não-Tributadas no Mercado Interno, e de
                 Exportação
            67 - Crédito Presumido - Outras Operações
            70 - Operação de Aquisição sem Direito a Crédito
            71 - Operação de Aquisição com Isenção
            72 - Operação de Aquisição com Suspensão
            73 - Operação de Aquisição a Alíquota Zero
            74 - Operação de Aquisição sem Incidência da Contribuição
            75 - Operação de Aquisição por Substituição Tributária
            98 - Outras Operações de Entrada
            99 - Outras Operações
        - vBC: Valor da Base de Cálculo da COFINS.
        - pCOFINS: Alíquota da COFINS (em percentual).
        - vCOFINS: Valor da COFINS.
    """
    tag = u'COFINSOutr'
    attributes = [(u'CST', ''),
                  (u'vBC', '0'),
                  (u'COFINS', '0'),
                  (u'vCOFINS', '0')]
    txttag = 'S05'

    def __init__(self, sale_item):
        BaseNFeXMLGroup.__init__(self)
        self.set_attr('CST', format_cst(sale_item.cofins_info.cst))
        self.set_attr('vBC', self.format_value(sale_item.cofins_info.v_bc, 2))
        self.set_attr('pCOFINS', sale_item.cofins_info.p_cofins)
        self.set_attr('vCOFINS', self.format_value(sale_item.cofins_info.v_cofins, 2))

    def as_txt(self):
        base = '%s|%s|%s|\n' % (self.txttag, self.get_attr('CST'),
                                self.get_attr('vCOFINS'))
        s = '%s|%s|%s|\n' % ('S07', self.get_attr('vBC'),
                             self.get_attr('pCOFINS'))
        return base + s


#
#   End of tax details
#
#   End of product details
#


class NFeTotal(BaseNFeXMLGroup):
    tag = u'total'
    txttag = 'W'

    def add_icms_total(self, operation):
        icms_total = NFeICMSTotal(operation)
        self.append(icms_total)

    def as_txt(self):
        base = '%s|\n' % self.txttag
        total = self.get_children()[0]
        return base + total.as_txt()


# Pg. 123
class NFeICMSTotal(BaseNFeXMLGroup):
    """
    - Attributes:
        - vBC: Base de Cálculo do ICMS.
        - vICMS: Valor Total do ICMS.
        - vICMSDeson: Valor Total do ICMS desonerado.
        - vBCST: Base de Cálculo do ICMS ST.
        - vST: Valor Total do ICMS ST.
        - vProd    Valor Total dos produtos e serviços.
        - vFrete: Valor Total do Frete.
        - vSeg: Valor Total do Seguro.
        - vDesc: Valor Total do Desconto.
        - vII Valor Total do II.
        - vIPI: Valor Total do IPI.
        - vPIS: Valor do PIS.
        - vCOFINS Valor do COFINS.
        - vOutro: Outras Despesas acessórias.
        - vNF: Valor Total da NF-e.
        - vTotTrib: Valor aproximado total de tributos federais, estaduais e municipais.
    """
    tag = u'ICMSTot'
    attributes = [(u'vBC', ''),
                  (u'vICMS', '0.00'),
                  (u'vICMSDeson', ''),
                  (u'vBCST', '0'),
                  (u'vST', '0'),
                  (u'vProd', ''),
                  (u'vFrete', '0'),
                  (u'vSeg', '0'),
                  (u'vDesc', '0'),
                  (u'vII', '0'),
                  (u'vIPI', '0'),
                  (u'vPIS', '0'),
                  (u'vCOFINS', '0'),
                  (u'vOutro', '0'),
                  (u'vNF', ''),
                  (u'vTotTrib', '')]
    txttag = 'W02'

    def __init__(self, operation):
        # FIXME: Adicionar:
        # - Frete, seguro, outras despesas
        BaseNFeXMLGroup.__init__(self)

        totals = self._get_totals(operation)
        self.set_attr('vBC', self.format_value(totals.bc_total))
        self.set_attr('vICMS', self.format_value(totals.icms_total))
        self.set_attr('vBCST', self.format_value(totals.bc_st_total))
        self.set_attr('vST', self.format_value(totals.icms_st_total))
        self.set_attr('vIPI', self.format_value(totals.ipi_total))

        self.set_attr('vProd', self.format_value(totals.prod_total))
        self.set_attr('vDesc', self.format_value(totals.discount_total))
        nf_total = totals.prod_total + totals.icms_st_total
        nf_total += totals.ipi_total - totals.discount_total
        self.set_attr('vNF', self.format_value(nf_total))

    def _get_totals(self, operation):
        Totals = namedtuple('Totals', 'bc_total, bc_st_total, icms_total,'
                            'icms_st_total, ipi_total, prod_total,'
                            'discount_total')
        bc_total = bc_st_total = prod_total = Decimal('0')
        icms_total = icms_st_total = ipi_total = Decimal('0')
        # Keep the discount total equal to 0.
        # The discount was already applied on price of each item.
        discount_total = Decimal('0')
        for item in operation.get_items():
            bc_total += item.icms_info.v_bc or 0
            bc_st_total += item.icms_info.v_bc_st or 0
            prod_total += item.quantity * item.price
            icms_total += item.icms_info.v_icms or 0
            icms_st_total += item.icms_info.v_icms_st or 0
            ipi_total += item.ipi_info.v_ipi or 0
        totals = Totals(bc_total, bc_st_total, icms_total, icms_st_total,
                        ipi_total, prod_total, discount_total)
        return totals


# Pg. 124
class NFeTransport(BaseNFeXMLGroup):
    """
    - Attributes:
        - modFrete: Modalidade do frete.
                    0 - por conta do emitente
                    1 - por conta do destinatário (default)
    """
    tag = u'transp'
    attributes = [('modFrete', '1')]
    txttag = 'X'


# Pg. 124 (optional)
class NFeTransporter(BaseNFeXMLGroup):
    """
    - Attributes:
        - CNPJ: Informar o CNPJ ou o CPF do transportador.
        - CPF: Informar o CNPJ ou o CPF do transportador.
        - xNome: Razão social ou nome.
        - IE: Inscrição estadual.
        - xEnder: Endereço completo.
        - xMun: Nome do município.
        - UF: Sigla da UF.
    """
    tag = u'transporta'
    txttag = 'X03'
    doc_cnpj_tag = 'X04'
    doc_cpf_tag = 'X05'

    attributes = [(u'CNPJ', None),
                  (u'CPF', None),
                  (u'xNome', ''),
                  (u'IE', ''),
                  (u'xEnder', ''),
                  (u'xMun', ''),
                  (u'UF', '')]

    def __init__(self, transporter, cpf=None, cnpj=None, state_registry=None):
        BaseNFeXMLGroup.__init__(self)
        person = transporter.person
        name = person.name
        self.set_attr('xNome', name[:60])
        if cnpj is not None:
            self.set_attr('CNPJ', cnpj)
            self.set_attr('IE', state_registry)
        else:
            self.set_attr('CPF', cpf)

        address = person.get_main_address()
        if address:
            self.set_attr('xEnder', address.get_address_string()[:60])
            self.set_attr('xMun', address.city_location.city[:60])
            self.set_attr('UF', address.city_location.state)

    def get_doc_txt(self):
        doc_value = self.get_attr('CNPJ')
        if doc_value:
            doc_tag = self.doc_cnpj_tag
        else:
            doc_tag = self.doc_cpf_tag
            doc_value = self.get_attr('CPF')
        return '%s|%s|\n' % (doc_tag, doc_value or '', )

    def as_txt(self):
        base_txt = "%s|%s|%s|%s|%s|%s\n" % (self.txttag,
                                            self.get_attr('xNome') or '',
                                            self.get_attr('IE') or '',
                                            self.get_attr('xEnder') or '',
                                            self.get_attr('xMun') or '',
                                            self.get_attr('UF') or '', )
        doc_txt = self.get_doc_txt()

        return base_txt + doc_txt


class NFeVolume(BaseNFeXMLGroup):
    """
    - Attributes:
        - nItem: número do item
    """
    tag = u'vol'
    txttag = 'X26'

    attributes = [(u'qVol', ''),
                  (u'esp', ''),
                  (u'marca', ''),
                  (u'nVol', ''),
                  (u'pesoL', ''),
                  (u'pesoB', '')]

    def __init__(self, quantity=0, unit='', brand='', number='',
                 net_weight=0.0, gross_weight=0.0):
        BaseNFeXMLGroup.__init__(self)
        # XXX: the documentation doesn't really say what quantity is all
        # about...
        if quantity:
            self.set_attr('qVol', int(math.ceil(quantity)))
        self.set_attr('esp', unit)
        self.set_attr('marca', brand)
        self.set_attr('nVol', number)
        if net_weight:
            self.set_attr('pesoL', "%.3f" % net_weight)
        if gross_weight:
            self.set_attr('pesoB', "%.3f" % gross_weight)


# Pg. 126 - Cobranca
class NFeBilling(BaseNFeXMLGroup):
    """NFe Billing node
    """
    tag = u'cobr'
    txttag = 'Y'


# Fatura
class NFeInvoice(BaseNFeXMLGroup):
    """NFe Invoice node
    """
    tag = u'fat'
    txttag = 'Y02'

    attributes = [(u'nFat', ''),
                  (u'vOrig', ''),
                  (u'vDesc', ''),
                  (u'vLiq', '')]

    def __init__(self, number, original_value, discount, liquid_value):
        BaseNFeXMLGroup.__init__(self)

        if discount:
            discount = self.format_value(discount)
        else:
            discount = ''

        self.set_attr('nFat', number)
        self.set_attr('vOrig', self.format_value(original_value))
        self.set_attr('vDesc', discount)
        self.set_attr('vLiq', self.format_value(liquid_value))


class NFeDuplicata(BaseNFeXMLGroup):
    """NFE Duplicate node
    """
    tag = u'dup'
    txttag = 'Y07'

    attributes = [(u'nDup', ''),
                  (u'dVenc', ''),
                  (u'vDup', '')]

    def __init__(self, number, due_date, value):
        BaseNFeXMLGroup.__init__(self)

        self.set_attr('nDup', number)
        self.set_attr('dVenc', self.format_date(due_date))
        self.set_attr('vDup', self.format_value(value))


class NFeAdditionalInformation(BaseNFeXMLGroup):
    tag = u'infAdic'
    attributes = [(u'infAdFisco', None),
                  (u'infCpl', None)]
    txttag = 'Z'

    def __init__(self, fisco_notes, operation_notes):
        BaseNFeXMLGroup.__init__(self)

        self.set_attr('infAdFisco', fisco_notes)
        self.set_attr('infCpl', operation_notes)


NFE_ICMS_CST_MAP = {
    0: NFeICMS00,
    10: NFeICMS10,
    20: NFeICMS20,
    30: NFeICMS30,
    40: NFeICMS40,
    41: NFeICMS40,
    50: NFeICMS40,
    51: NFeICMS51,
    60: NFeICMS60,
    70: NFeICMS70,
    90: NFeICMS90,
}

NFE_ICMS_CSOSN_MAP = {
    101: NFeICMSSN101,
    102: NFeICMSSN102,
    103: NFeICMSSN102,
    201: NFeICMSSN201,
    202: NFeICMSSN202,
    203: NFeICMSSN202,
    300: NFeICMSSN102,
    400: NFeICMSSN102,
    500: NFeICMSSN500,
    900: NFeICMSSN900,
}

NFE_PIS_MAP = {
    1: NFePISAliq,
    2: NFePISAliq,
    4: NFePISNT,
    5: NFePISNT,
    6: NFePISNT,
    7: NFePISNT,
    8: NFePISNT,
    9: NFePISNT,
    49: NFePISOutr,
    50: NFePISOutr,
    51: NFePISOutr,
    52: NFePISOutr,
    53: NFePISOutr,
    54: NFePISOutr,
    55: NFePISOutr,
    56: NFePISOutr,
    60: NFePISOutr,
    61: NFePISOutr,
    62: NFePISOutr,
    63: NFePISOutr,
    64: NFePISOutr,
    65: NFePISOutr,
    66: NFePISOutr,
    67: NFePISOutr,
    70: NFePISOutr,
    71: NFePISOutr,
    72: NFePISOutr,
    73: NFePISOutr,
    74: NFePISOutr,
    75: NFePISOutr,
    98: NFePISOutr,
    99: NFePISOutr,
}


NFE_COFINS_MAP = {
    1: NFeCOFINSAliq,
    2: NFeCOFINSAliq,
    4: NFeCOFINSNT,
    5: NFeCOFINSNT,
    6: NFeCOFINSNT,
    7: NFeCOFINSNT,
    8: NFeCOFINSNT,
    9: NFeCOFINSNT,
    49: NFeCOFINSOutr,
    50: NFeCOFINSOutr,
    51: NFeCOFINSOutr,
    52: NFeCOFINSOutr,
    53: NFeCOFINSOutr,
    54: NFeCOFINSOutr,
    55: NFeCOFINSOutr,
    56: NFeCOFINSOutr,
    60: NFeCOFINSOutr,
    61: NFeCOFINSOutr,
    62: NFeCOFINSOutr,
    63: NFeCOFINSOutr,
    64: NFeCOFINSOutr,
    65: NFeCOFINSOutr,
    66: NFeCOFINSOutr,
    67: NFeCOFINSOutr,
    70: NFeCOFINSOutr,
    71: NFeCOFINSOutr,
    72: NFeCOFINSOutr,
    73: NFeCOFINSOutr,
    74: NFeCOFINSOutr,
    75: NFeCOFINSOutr,
    98: NFeCOFINSOutr,
    99: NFeCOFINSOutr,
}
