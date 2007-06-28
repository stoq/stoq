# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano <henrique@async.com.br>
##              Johan Dahlin <henrique@async.com.br>
##
"""
PertoPay 2023 driver implementation.
"""

import datetime
from decimal import Decimal
import re

from kiwi.python import Settable
from serial import PARITY_EVEN
from zope.interface import implements

from stoqdrivers.devices.serialbase import SerialBase
from stoqdrivers.devices.interfaces import (ICouponPrinter,
                                            IChequePrinter)
from stoqdrivers.devices.printers.cheque import (BaseChequePrinter,
                                                 BankConfiguration)
from stoqdrivers.devices.printers.base import BaseDriverConstants
from stoqdrivers.enum import PaymentMethodType, TaxType, UnitType
from stoqdrivers.exceptions import (
    DriverError, PendingReduceZ, CommandParametersError, CommandError,
    ReadXError, OutofPaperError, CouponTotalizeError, PaymentAdditionError,
    CancelItemError, CouponOpenError, InvalidState, PendingReadX,
    CloseCouponError, CouponNotOpenError)
from stoqdrivers.devices.printers.capabilities import Capability
from stoqdrivers.translation import stoqdrivers_gettext

_ = lambda msg: stoqdrivers_gettext(msg)

# Page 92
[FLAG_INTERVENCAO_TECNICA,
 FLAG_SEM_MFD,
 FLAG_RAM_NOK,
 FLAG_RELOGIO_NOK,
 FLAG_SEM_MF,
 FLAG_DIA_FECHADO,
 FLAG_DIA_ABERTO,
 FLAG_Z_PENDENTE,
 FLAG_SEM_PAPEL,
 FLAG_MECANISM_NOK,
 FLAG_DOCUMENTO_ABERTO,
 FLAG_INSCRICOES_OK,
 FLAG_CLICHE_OK,
 FLAG_EM_LINHA,
 FLAG_MFD_ESGOTADA] = _status_flags = [2**n for n in range(15)]

_flagnames = {
    FLAG_INTERVENCAO_TECNICA: 'FLAG_INTERVENCAO_TECNICA',
    FLAG_SEM_MFD: 'FLAG_SEM_MFD',
    FLAG_RAM_NOK: 'FLAG_RAM_NOK',
    FLAG_RELOGIO_NOK: 'FLAG_RELOGIO_NOK',
    FLAG_SEM_MF: 'FLAG_SEM_MF',
    FLAG_DIA_FECHADO: 'FLAG_DIA_FECHADO',
    FLAG_DIA_ABERTO: 'FLAG_DIA_ABERTO',
    FLAG_Z_PENDENTE: 'FLAG_Z_PENDENTE',
    FLAG_SEM_PAPEL: 'FLAG_SEM_PAPEL',
    FLAG_MECANISM_NOK: 'FLAG_MECANISM_NOK',
    FLAG_DOCUMENTO_ABERTO: 'FLAG_DOCUMENTO_ABERTO',
    FLAG_INSCRICOES_OK: 'FLAG_INSCRICOES_OK',
    FLAG_CLICHE_OK: 'FLAG_CLICHE_OK',
    FLAG_EM_LINHA: 'FLAG_EM_LINHA',
    FLAG_MFD_ESGOTADA: 'FLAG_MFD_ESGOTADA',
    }


class Pay2023Constants(BaseDriverConstants):
    _constants = {
        UnitType.WEIGHT:      'km',
        UnitType.LITERS:      'lt',
        UnitType.METERS:      'm ',
        UnitType.EMPTY:       '  ',
        PaymentMethodType.MONEY:         '-2',
        PaymentMethodType.CHECK:        '2',
#         PaymentMethodType.MONEY: '-2',
#         PaymentMethodType.CHECK: '0',
#         PaymentMethodType.BOLETO: '1',
#         PaymentMethodType.CREDIT_CARD: '2',
#         PaymentMethodType.DEBIT_CARD: '3',
#         PaymentMethodType.FINANCIAL: '4',
#         PaymentMethodType.GIFT_CERTIFICATE: '5,
        }

_RETVAL_TOKEN_RE = re.compile(r"^\s*([^=\s;]+)")
_RETVAL_QUOTED_VALUE_RE = re.compile(r"^\s*=\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\"")
_RETVAL_VALUE_RE = re.compile(r"^\s*=\s*([^\s;]*)")
_RETVAL_ESCAPE_RE = re.compile(r"\\(.)")

class Pay2023(SerialBase, BaseChequePrinter):
    implements(IChequePrinter, ICouponPrinter)

    model_name = "Pertopay Fiscal 2023"
    coupon_printer_charset = "cp850"
    cheque_printer_charset = "ascii"

    CHEQUE_CONFIGFILE = 'perto.ini'

    CMD_PREFIX = '{'
    CMD_SUFFIX = '}'
    EOL_DELIMIT = CMD_SUFFIX

    errors_dict = {
        7003: OutofPaperError,
        7004: OutofPaperError,
        8007: CouponTotalizeError,
        8011: PaymentAdditionError,
        8013: CouponTotalizeError,
        8014: PaymentAdditionError,
        8017: CloseCouponError,
        8044: CancelItemError,
        8045: CancelItemError,
        8068: PaymentAdditionError,
        8086: CancelItemError,
        15009: PendingReduceZ,
        11002: CommandParametersError,
        11006: CommandError,
        11007: InvalidState,
        15007: PendingReadX,
        15008: ReadXError,
        15011: OutofPaperError
        }

    def __init__(self, port, consts=None):
        port.set_options(baudrate=115200, parity=PARITY_EVEN)
        SerialBase.__init__(self, port)
        BaseChequePrinter.__init__(self)
        self._consts = consts or Pay2023Constants
        self._command_id = 0
        self._reset()

    def _reset(self):
        self._customer_name = ''
        self._customer_document = ''
        self._customer_address = ''

    #
    # Helper methods
    #
    def _parse_return_value(self, text):
        # Based on cookielib.split_header_words
        def unmatched(match):
            start, end = match.span(0)
            return match.string[:start] + match.string[end:]

        orig_text = text
        result = {}
        while text:
            m = _RETVAL_TOKEN_RE.search(text)
            if m:
                text = unmatched(m)
                name = m.group(1)
                m = _RETVAL_QUOTED_VALUE_RE.search(text)
                if m:  # quoted value
                    text = unmatched(m)
                    value = m.group(1)
                    value = _RETVAL_ESCAPE_RE.sub(r"\1", value)
                else:
                    m = _RETVAL_VALUE_RE.search(text)
                    if m:  # unquoted value
                        text = unmatched(m)
                        value = m.group(1)
                        value = value.rstrip()
                    else:
                        # no value, a lone token
                        value = None
                result[name] = value
            else:
                raise AssertionError

        return result

    def _send_command(self, command, **params):
        # Page 38-39
        parameters = []
        for param, value in params.items():
            if isinstance(value, Decimal):
                value = ('%.03f' % value).replace('.', ',')
            elif isinstance(value, basestring):
                value = '"%s"' % value
            elif isinstance(value, bool):
                if value is False:
                    value = 'f'
                elif value is True:
                    value = 't'
            elif isinstance(value, datetime.date):
                value = value.strftime('#%d/%m/%y#')

            parameters.append('%s=%s' % (param, value))

        reply = self.writeline("%d;%s;%s;" % (self._command_id,
                                              command,
                                              ' '.join(parameters)))
        if reply[0] != '{':
            # This happened once after the first command issued after
            # the power returned, it should probably be handled gracefully
            raise AssertionError(repr(reply))

        # Page 39
        sections = reply[1:].split(';')
        if len(sections) != 4:
            raise AssertionError

        retdict = self._parse_return_value(sections[2])
        errorcode = int(sections[1])
        if errorcode != 0:
            errorname = retdict['NomeErro']
            errordesc = retdict['Circunstancia']
            try:
                exception = Pay2023.errors_dict[errorcode]
            except KeyError:
                raise DriverError(errordesc, errorcode)
            raise exception(errordesc, errorcode)

        return retdict

    def _read_register(self, name, regtype):
        if regtype == int:
            cmd = 'LeInteiro'
            argname = 'NomeInteiro'
            retname = 'ValorInteiro'
        elif regtype == Decimal:
            cmd = 'LeMoeda'
            argname = 'NomeDadoMonetario'
            retname = 'ValorMoeda'
        elif regtype == datetime.date:
            cmd = 'LeData'
            argname = 'NomeData'
            retname = 'ValorData'
        elif regtype == str:
            cmd = 'LeTexto'
            argname = 'NomeTexto'
            retname = 'ValorTexto'
        else:
            raise AssertionError

        retdict = self._send_command(cmd, **dict([(argname, name)]))
        assert len(retdict) == 1
        assert retname in retdict
        retval = retdict[retname]
        if regtype == int:
            return int(retval)
        elif regtype == Decimal:
            retval = retval.replace('.', '')
            retval = retval.replace(',', '.')
            return Decimal(retval)
        elif regtype == datetime.date:
            # This happens the first time we send a ReducaoZ after
            # opening the printer and removing the jumper.
            if retval == '#00/00/0000#':
                return datetime.date.today()
            else:
                # "29/03/2007" -> datetime.date(2007, 3, 29)
                d, m, y = map(int, retval[1:-1].split('/'))
                return datetime.date(y, m, d)
        elif regtype == str:
            # '"string"' -> 'string'
            return retval[1:-1]
        else:
            raise AssertionError

    def _get_status(self):
        return self._read_register('Indicadores', int)

    def _get_last_item_id(self):
        return self._read_register('ContadorDocUltimoItemVendido', int)

    def _get_coupon_number(self):
        return self._read_register('COO', int)

    def _get_coupon_total_value(self):
        return self._read_register('TotalDocLiquido', Decimal)

    def _get_coupon_remainder_value(self):
        value = self._read_register('TotalDocValorPago', Decimal)
        result = self._get_coupon_total_value() - value
        if result < 0.0:
            result = 0.0
        return result

    # This how the printer needs to be configured.
    def _define_tax_name(self, code, name):
        try:
            retdict = self._send_command(
                'LeNaoFiscal', CodNaoFiscal=code)
        except DriverError, e:
            if e.code != 8057: # Not configured
                raise
        else:
            for retname in ['NomeNaoFiscal', 'DescricaoNaoFiscal']:
                configured_name = retdict[retname]
                if configured_name  != name:
                    raise DriverError(
                        "The name of the tax code %d is set to %r, "
                        "but it needs to be configured as %r" % (
                        code, configured_name, name))

        try:
            self._send_command(
                'DefineNaoFiscal', CodNaoFiscal=code, DescricaoNaoFiscal=name,
                NomeNaoFiscal=name, TipoNaoFiscal=False)
        except DriverError, e:
            if e.code != 8036:
                raise

    def _delete_tax_name(self, code):
        try:
            self._send_command(
                'ExcluiNaoFiscal', CodNaoFiscal=code)
        except DriverError, e:
            if e.code != 8057: # Not configured
                raise

    def _define_payment_method(self, code, name):
        try:
            retdict = self._send_command(
                'LeMeioPagamento', CodMeioPagamentoProgram=code)
        except DriverError, e:
            if e.code != 8014: # Not configured
                raise
        else:
            configure = False
            for retname in ['NomeMeioPagamento', 'DescricaoMeioPagamento']:
                configured_name = retdict[retname]
                if configured_name  != name:
                    configure = True

            if not configure:
                return

        try:
            self._send_command(
                'DefineMeioPagamento',
                CodMeioPagamentoProgram=code, DescricaoMeioPagamento=name,
                NomeMeioPagamento=name, PermiteVinculado=False)
        except DriverError, e:
            raise

    def _delete_payment_method(self, code):
        try:
            self._send_command(
                'ExcluiMeioPagamento', CodMeioPagamentoProgram=code)
        except DriverError, e:
            if e.code != 8014: # Not configured
                raise

    def _define_tax_code(self, code, value, service=False):
        try:
            retdict = self._send_command(
                'LeAliquota', CodAliquotaProgramavel=code)
        except DriverError, e:
            if e.code != 8005: # Not configured
                raise
        else:
            configure = False
            for retname in ['PercentualAliquota']:
                configured_name = retdict[retname]
                if configured_name != value:
                    configure = True

            if not configure:
                return

        try:
            self._send_command(
                'DefineAliquota',
                CodAliquotaProgramavel=code,
                DescricaoAliquota='%2.2f%%' % value ,
                PercentualAliquota=value,
                AliquotaICMS=not service)
        except DriverError, e:
            raise

    def _delete_tax_code(self, code):
        try:
            self._send_command(
                'ExcluiAliquota', CodAliquotaProgramavel=code)
        except DriverError, e:
            if e.code != 8005: # Not configured
                raise

    def _get_taxes(self):
        taxes = [
            ('I', self._read_register('TotalDiaIsencaoICMS', Decimal)),
            ('F', self._read_register('TotalDiaSubstituicaoTributariaICMS',
                                      Decimal)),
            ('N', self._read_register('TotalDiaNaoTributadoICMS', Decimal)),
            ('DESC',
             self._read_register('TotalDiaDescontos', Decimal)),
            ('CANC',
             self._read_register('TotalDiaCancelamentosICMS', Decimal) +
             self._read_register('TotalDiaCancelamentosISSQN', Decimal)),
            ('ISS',
             self._read_register('TotalDiaISSQN', Decimal)),
            ]

        for reg in range(16):
            value = self._read_register('TotalDiaValorAliquota[%d]' % (
                reg,), Decimal)
            if value:
                retdict = self._send_command(
                    'LeAliquota', CodAliquotaProgramavel=reg)
                # The service taxes are already added in the 'ISS' tax
                # Skip non-ICMS taxes here.
                if retdict['AliquotaICMS'] == 'N':
                    continue
                desc = retdict['PercentualAliquota'].replace(',', '')
                taxes.append(('%04d' % int(desc), value))
        return taxes

    def setup(self):
        self._define_tax_name(0, "Suprimento".encode('cp850'))
        self._define_tax_name(1, "Sangria".encode('cp850'))
        for code in range(2, 15):
            self._delete_tax_name(code)

        self._define_payment_method(0, u'Cheque'.encode('cp850'))
        self._define_payment_method(1, u'Boleto'.encode('cp850'))
        self._define_payment_method(2, u'Cartão credito'.encode('cp850'))
        self._define_payment_method(3, u'Cartão debito'.encode('cp850'))
        self._define_payment_method(4, u'Financeira'.encode('cp850'))
        self._define_payment_method(5, u'Vale compra'.encode('cp850'))
        for code in range(6, 15):
            self._delete_payment_method(code)

        self._define_tax_code(0, Decimal("17.00"))
        self._define_tax_code(1, Decimal("12.00"))
        self._define_tax_code(2, Decimal("25.00"))
        self._define_tax_code(3, Decimal("8.00"))
        self._define_tax_code(4, Decimal("5.00"))
        self._define_tax_code(5, Decimal("3.00"), service=True)
        for code in range(6, 16):
            self._delete_tax_code(code)

    def print_status(self):
        status = self._get_status()
        print 'Flags'
        for flag in reversed(_status_flags):
            if status & flag:
                print flag, _flagnames[flag]

        print 'non-fiscal registers'
        for i in range(15):
            try:
                print self._send_command(
                    'LeNaoFiscal', CodNaoFiscal=i)
            except DriverError, e:
                if e.code != 8057:
                    raise

    #
    # ICouponPrinter implementation
    #

    def coupon_identify_customer(self, customer, address, document):
        self._customer_name = customer
        self._customer_document = document
        self._customer_address = address

    def coupon_open(self):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            raise CouponOpenError(_("Coupon already opened."))

        customer = self._customer_name
        document = self._customer_document
        address = self._customer_address
        self._send_command('AbreCupomFiscal',
                           EnderecoConsumidor=address[:80],
                           IdConsumidor=document[:29],
                           NomeConsumidor=customer[:30])

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UnitType.EMPTY,
                        discount=Decimal("0.0"), surcharge=Decimal("0.0"),
                        unit_desc=""):
        status = self._get_status()
        if not status & FLAG_DOCUMENTO_ABERTO:
            raise CouponNotOpenError

        if unit == UnitType.CUSTOM:
            unit = unit_desc
        else:
            unit = self._consts.get_value(unit)

        taxcode = ord(taxcode) - 128
        self._send_command('VendeItem',
                           CodAliquota=taxcode,
                           CodProduto=code[:48],
                           NomeProduto=description[:200],
                           Unidade=unit,
                           PrecoUnitario=price,
                           Quantidade=quantity)
        return self._get_last_item_id()

    def coupon_cancel_item(self, item_id):
        self._send_command('CancelaItemFiscal', NumItem=item_id)

    def coupon_cancel(self):
        self._send_command('CancelaCupom')

    def coupon_totalize(self, discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), taxcode=TaxType.NONE):
        # The FISCnet protocol (the protocol used in this printer model)
        # doesn't have a command to totalize the coupon, so we just get
        # the discount/surcharge values and applied to the coupon.
        value = discount and (discount * -1) or surcharge
        if value:
            self._send_command('AcresceSubtotal',
                               Cancelar=False,
                               ValorPercentual=value)
        return self._get_coupon_total_value()

    def coupon_add_payment(self, payment_method, value, description=u"",
                           custom_pm=''):
        if not custom_pm:
            pm = int(self._consts.get_value(payment_method))
        else:
            pm = custom_pm
        self._send_command('PagaCupom',
                           CodMeioPagamento=pm, Valor=value,
                           TextoAdicional=description[:80])
        return self._get_coupon_remainder_value()

    def coupon_close(self, message=''):
        self._send_command('EncerraDocumento',
                           TextoPromocional=message[:492])
        self._reset()
        return self._get_coupon_number()

    def summarize(self):
        self._send_command('EmiteLeituraX')

    def close_till(self):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self.coupon_cancel()

        data = Settable(
            opening_date=self._read_register('DataAbertura', datetime.date),
            serial=self._read_register('NumeroSerieECF', str),
            serial_id=self._read_register('ECF', int),
            coupon_start=self._read_register('COOInicioDia', int),
            coupon_end=self._read_register('COO', int),
            cro=self._read_register('CRO', int),
            crz=self._read_register('CRZ', int),
            period_total=self._read_register('TotalDiaVendaBruta', Decimal),
            total=self._read_register('GT', Decimal),
            taxes=self._get_taxes())

        self._send_command('EmiteReducaoZ')

        return data

    def till_add_cash(self, value):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self.coupon_cancel()
        self._send_command('AbreCupomNaoFiscal')
        self._send_command('EmiteItemNaoFiscal',
                           NomeNaoFiscal="Suprimento",
                           Valor=value)
        self._send_command('EncerraDocumento')

    def till_remove_cash(self, value):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self.coupon_cancel()
        self._send_command('AbreCupomNaoFiscal')
        self._send_command('EmiteItemNaoFiscal',
                           NomeNaoFiscal="Sangria",
                           Valor=value)
        self._send_command('EncerraDocumento')

    def till_read_memory(self, start=None, end=None):
        try:
            self._send_command('EmiteLeituraMF',
                               LeituraSimplificada=True,
                               DataInicial=start,
                               DataFinal=end)
        except DriverError, e:
            if e.code == 8089:
                return

    def till_read_memory_by_reductions(self, start=None, end=None):
        self._send_command('EmiteLeituraMF',
                           LeituraSimplificada=True,
                           ReducaoInicial=start,
                           ReducaoFinal=end)

    #
    # IChequePrinter implementation
    #

    def print_cheque(self, bank, value, thirdparty, city, date=None):
        if date is None:
            data = datetime.datetime.now()
        if not isinstance(bank, BankConfiguration):
            raise TypeError("bank parameter must be BankConfiguration instance")

        data = dict(HPosAno=bank.get_x_coordinate("year"),
                    HPosCidade=bank.get_x_coordinate("city"),
                    HPosDia=bank.get_x_coordinate("day"),
                    HPosExtensoLinha1=bank.get_x_coordinate("legal_amount"),
                    HPosExtensoLinha2=bank.get_x_coordinate("legal_amount2"),
                    HPosFavorecido=bank.get_x_coordinate("thirdparty"),
                    HPosMes=bank.get_x_coordinate("month"),
                    HPosValor=bank.get_x_coordinate("value"),
                    VPosCidade=bank.get_y_coordinate("city"),
                    VPosExtensoLinha1=bank.get_y_coordinate("legal_amount"),
                    VPosExtensoLinha2=bank.get_y_coordinate("legal_amount2"),
                    VPosFavorecido=bank.get_y_coordinate("thirdparty"),
                    VPosValor=bank.get_y_coordinate("value"))

        self._send_command('ImprimeCheque', Cidade=city[:27],
                           Data=date.strftime("#%d/%m/%Y#"),
                           Favorecido=thirdparty[:45],
                           Valor=value, **data)

    def get_capabilities(self):
        return dict(item_code=Capability(max_len=48),
                    item_id=Capability(max_size=32767),
                    items_quantity=Capability(digits=14, decimals=4),
                    item_price=Capability(digits=14, decimals=4),
                    item_description=Capability(max_len=200),
                    payment_value=Capability(digits=14, decimals=4),
                    promotional_message=Capability(max_len=492),
                    payment_description=Capability(max_len=80),
                    customer_name=Capability(max_len=30),
                    customer_id=Capability(max_len=29),
                    customer_address=Capability(max_len=80),
                    cheque_thirdparty=Capability(max_len=45),
                    cheque_value=Capability(digits=14, decimals=4),
                    cheque_city=Capability(max_len=27))

    def get_constants(self):
        return self._consts

    def query_status(self):
        return '{0;LeInteiro;NomeInteiro="Indicadores";}'

    def status_reply_complete(self, reply):
        return '}' in reply

    def get_serial(self):
        return self._read_register('NumeroSerieECF', str)

    def get_tax_constants(self):
        constants = []

        for reg in range(16):
            try:
                retdict = self._send_command(
                    'LeAliquota', CodAliquotaProgramavel=reg)
            except DriverError, e:
                if e.code == 8005: # Aliquota nao carregada
                    continue
                raise
            print retdict
            # The service taxes are already added in the 'ISS' tax
            # Skip non-ICMS taxes here.
            if retdict['AliquotaICMS'] == 'Y':
                tax_type = TaxType.CUSTOM
            else:
                tax_type = TaxType.SERVICE

            value = Decimal(retdict['PercentualAliquota'].replace(',', '.'))
            device_value = int(retdict['CodAliquotaProgramavel'])
            constants.append((tax_type,
                              chr(128 + device_value),
                              value))

        # These are signed integers, we're storing them
        # as strings and then subtract by 127
        # Page 10
        constants.extend([
            (TaxType.SUBSTITUTION, '\x7e', None), # -2
            (TaxType.EXEMPTION,    '\x7d', None), # -3
            (TaxType.NONE,         '\x7c', None), # -4
            ])

        return constants
