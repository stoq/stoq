# -*- Mode: Python; coding: iso-8859-1 -*-
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

from serial import PARITY_EVEN
from zope.interface import implements

from stoqdrivers.devices.serialbase import SerialBase
from stoqdrivers.devices.interfaces import (ICouponPrinter,
                                            IChequePrinter)
from stoqdrivers.devices.printers.cheque import (BaseChequePrinter,
                                                 BankConfiguration)
from stoqdrivers.devices.printers.base import BaseDriverConstants
from stoqdrivers.constants import (TAX_CUSTOM, TAX_SUBSTITUTION,
                                   TAX_EXEMPTION, TAX_NONE)
from stoqdrivers.constants import (UNIT_WEIGHT, UNIT_METERS, UNIT_LITERS,
                                   UNIT_EMPTY, UNIT_CUSTOM)
from stoqdrivers.constants import MONEY_PM, CHEQUE_PM
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
        UNIT_WEIGHT:      'km',
        UNIT_LITERS:      'lt',
        UNIT_METERS:      'm ',
        UNIT_EMPTY:       '  ',
        MONEY_PM:         '-2',
        CHEQUE_PM:        '2',
        }

    _tax_constants = [
        # These are signed integers, we're storing them
        # as strings and then subtract by 127
        # Page 10
        (TAX_SUBSTITUTION, '\x7e', None), # -2
        (TAX_EXEMPTION,    '\x7d', None), # -3
        (TAX_NONE,         '\x7c', None), # -4

        (TAX_CUSTOM,       '\x80', Decimal(17)),
        (TAX_CUSTOM,       '\x81', Decimal(12)),
        (TAX_CUSTOM,       '\x82', Decimal(25)),
        (TAX_CUSTOM,       '\x83', Decimal(8)),
        (TAX_CUSTOM,       '\x84', Decimal(5)),
        ]

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

    CMD_READ_X = 'EmiteLeituraX'
    CMD_CANCEL_COUPON = 'CancelaCupom'
    CMD_CLOSE_TILL = 'EmiteReducaoZ'
    # Page 87
    CMD_ADD_ITEM = 'VendeItem'
    CMD_COUPON_OPEN = 'AbreCupomFiscal'
    CMD_COUPON_OPEN_NOT_FISCAL = 'AbreCupomNaoFiscal'
    CMD_CANCEL_ITEM = 'CancelaItemFiscal'
    CMD_ADD_PAYMENT = 'PagaCupom'
    CMD_ADD_COUPON_DIFFERENCE = 'AcresceSubtotal'
    CMD_COUPON_CANCEL = 'CancelaCupom'
    CMD_COUPON_CLOSE = 'EncerraDocumento'
    CMD_GET_LAST_ITEM_ID = 'ContadorDocUltimoItemVendido'
    CMD_GET_COUPON_TOTAL_VALUE = 'TotalDocLiquido'
    CMD_GET_COUPON_TOTAL_PAID_VALUE = 'TotalDocValorPago'
    CMD_PRINT_CHEQUE = 'ImprimeCheque'
    CMD_GET_COO = "COO"
    CMD_READ_REGISTER_INT = 'LeInteiro'
    CMD_READ_REGISTER_MONEY = 'LeMoeda'
    CMD_READ_REGISTER_DATE = 'LeData'
    CMD_READ_REGISTER_TEXT = 'LeTexto'

    # Page 53
    REGISTER_INDICATORS = "Indicadores"

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
        self._customer_name = ''
        self._customer_document = ''
        self._customer_address = ''
        self._command_id = 0

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

            parameters.append('%s=%s' % (param, value))

        reply = self.writeline("%d;%s;%s;" % (self._command_id,
                                              command,
                                              ' '.join(parameters)))
        if reply[0] != '{':
            raise AssertionError

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
            cmd = Pay2023.CMD_READ_REGISTER_INT
            argname = 'NomeInteiro'
            retname = 'ValorInteiro'
        elif regtype == Decimal:
            cmd = Pay2023.CMD_READ_REGISTER_MONEY
            argname = 'NomeDadoMonetario'
            retname = 'ValorMoeda'
        elif regtype == datetime.date:
            cmd = Pay2023.CMD_READ_REGISTER_DATE
            argname = 'NomeData'
            retname = 'ValorData'
        elif regtype == str:
            cmd = Pay2023.CMD_READ_REGISTER_TEXT
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
            return retval[1:-1]
        elif regtype == str:
            return retval[1:-1]
        else:
            raise AssertionError

    def _get_status(self):
        return self._read_register(Pay2023.REGISTER_INDICATORS, int)

    def _get_last_item_id(self):
        return self._read_register(Pay2023.CMD_GET_LAST_ITEM_ID, int)

    def _get_coupon_number(self):
        return self._read_register(Pay2023.CMD_GET_COO, int)

    def _get_coupon_total_value(self):
        return self._read_register(Pay2023.CMD_GET_COUPON_TOTAL_VALUE, Decimal)

    def _get_coupon_remainder_value(self):
        value = self._read_register(Pay2023.CMD_GET_COUPON_TOTAL_PAID_VALUE,
                                    Decimal)
        result = self._get_coupon_total_value() - value
        if result < 0.0:
            result = 0.0
        return result

    # This how the printer needs to be configured.
    def setup(self):
        self._send_command(
            'DefineNaoFiscal', CodNaoFiscal=1, DescricaoNaoFiscal="Sangria",
            NomeNaoFiscal="Sangria", TipoNaoFiscal=False)
        self._send_command(
            'DefineNaoFiscal', CodNaoFiscal=0, DescricaoNaoFiscal="Suprimento",
            NomeNaoFiscal="Suprimento", TipoNaoFiscal=False)

    def print_sintegra_data(self):
        print self._read_register('DataAbertura', datetime.date) # 3
        print self._read_register('NumeroSerieECF', str) # 4
        print self._read_register('ECF', int) # 5
        print self._read_register('COOInicioDia', int) # 7
        print self._read_register('COO', int) # 8
        print self._read_register('CRZ', int) # 9
        print self._read_register('CRO', int) # 10
        print self._read_register('TotalDiaVendaBruta', Decimal) # 11
        print self._read_register('GT', Decimal) # 1

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
                if e.code == 8057:
                    pass
                else:
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
        self._send_command(Pay2023.CMD_COUPON_OPEN,
                           EnderecoConsumidor=address[:80],
                           IdConsumidor=document[:29],
                           NomeConsumidor=customer[:30])

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UNIT_EMPTY,
                        discount=Decimal("0.0"), surcharge=Decimal("0.0"),
                        unit_desc=""):
        status = self._get_status()
        if not status & FLAG_DOCUMENTO_ABERTO:
            raise CouponNotOpenError

        if unit == UNIT_CUSTOM:
            unit = unit_desc
        else:
            unit = self._consts.get_value(unit)

        taxcode = ord(taxcode) - 128
        self._send_command(Pay2023.CMD_ADD_ITEM,
                           CodAliquota=taxcode,
                           CodProduto=code[:48],
                           NomeProduto=description[:200],
                           Unidade=unit,
                           PrecoUnitario=price,
                           Quantidade=quantity)
        return self._get_last_item_id()

    def coupon_cancel_item(self, item_id):
        self._send_command(Pay2023.CMD_CANCEL_ITEM, NumItem=item_id)

    def coupon_cancel(self):
        self._send_command(Pay2023.CMD_COUPON_CANCEL)

    def coupon_totalize(self, discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), taxcode=TAX_NONE):
        # The FISCnet protocol (the protocol used in this printer model)
        # doesn't have a command to totalize the coupon, so we just get
        # the discount/surcharge values and applied to the coupon.
        value = discount and (discount * -1) or surcharge
        if value:
            self._send_command(Pay2023.CMD_ADD_COUPON_DIFFERENCE,
                               Cancelar=False,
                               ValorPercentual=value)
        return self._get_coupon_total_value()

    def coupon_add_payment(self, payment_method, value, description=u"",
                           custom_pm=''):
        if not custom_pm:
            pm = int(self._consts.get_value(payment_method))
        else:
            pm = custom_pm
        self._send_command(Pay2023.CMD_ADD_PAYMENT,
                           CodMeioPagamento=pm, Valor=value,
                           TextoAdicional=description[:80])
        return self._get_coupon_remainder_value()

    def coupon_close(self, message=''):
        self._send_command(Pay2023.CMD_COUPON_CLOSE,
                           TextoPromocional=message[:492])
        return self._get_coupon_number()

    def summarize(self):
        self._send_command(Pay2023.CMD_READ_X)

    def close_till(self):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self._send_command(Pay2023.CMD_COUPON_CANCEL)

        self._send_command(Pay2023.CMD_CLOSE_TILL)

    def till_add_cash(self, value):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self._send_command(Pay2023.CMD_COUPON_CANCEL)
        self._send_command(Pay2023.CMD_COUPON_OPEN_NOT_FISCAL)
        self._send_command('EmiteItemNaoFiscal',
                           NomeNaoFiscal="Suprimento",
                           Valor=value)
        self._send_command(Pay2023.CMD_COUPON_CLOSE)

    def till_remove_cash(self, value):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self._send_command(Pay2023.CMD_COUPON_CANCEL)
        self._send_command(Pay2023.CMD_COUPON_OPEN_NOT_FISCAL)
        self._send_command('EmiteItemNaoFiscal',
                           NomeNaoFiscal="Sangria",
                           Valor=value)
        self._send_command(Pay2023.CMD_COUPON_CLOSE)

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

        self._send_command(Pay2023.CMD_PRINT_CHEQUE, Cidade=city[:27],
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
