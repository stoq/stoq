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

from datetime import datetime
from decimal import Decimal

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
        (TAX_SUBSTITUTION, '\x7e', None),
        (TAX_EXEMPTION,    '\x7d', None),
        (TAX_NONE,         '\x7c', None),
        (TAX_CUSTOM,       '\x80', Decimal(17)),
        (TAX_CUSTOM,       '\x81', Decimal(12)),
        (TAX_CUSTOM,       '\x82', Decimal(25)),
        (TAX_CUSTOM,       '\x83', Decimal(8)),
        (TAX_CUSTOM,       '\x84', Decimal(5)),
        ]


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
    CMD_GET_INTEGER_REGISTER_DATA = 'LeInteiro'
    CMD_GET_MONEY_REGISTER_DATA = 'LeMoeda'
    CMD_GET_LAST_ITEM_ID = 'ContadorDocUltimoItemVendido'
    CMD_GET_COUPON_TOTAL_VALUE = 'TotalDocLiquido'
    CMD_GET_COUPON_TOTAL_PAID_VALUE = 'TotalDocValorPago'
    CMD_PRINT_CHEQUE = 'ImprimeCheque'
    CMD_GET_COO = "COO"
    CMD_READ_REGISTER_INT = 'LeInteiro'

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

    def _send_command(self, command, **params):
        params = ["%s=%s" % (param, value) for param, value in params.items()]
        data = "%d;%s;%s;" % (self._command_id, command,
                              " ".join(params))
        result = self.writeline("%s" % data)
        return result

    def send_command(self, command, **params):
        result = self._send_command(command, **params)
        self.handle_error(command, result)

    def _parse_error(self, cmd, reply):
        # removing REPLY_PREFIX and REPLY_SUFFIX
        reply = reply[1:-1]

        cmd_id, code, desc = reply.split(';')
        return int(code)

    def handle_error(self, cmd, reply):
        """
        Reply format::

            {CMD_ID;REPLY_CODE;REPLY_DESCRIPTION;CMD_SIZE}

        Where '{' is the reply prefix and '}' the suffix

        Note that the REPLY_DESCRIPTION field is composed by the following
        sections::

          NomeErro="A_STRING"
          Circunstancia="THE_REPLY_DESCRIPTION_ITSELF"
        """
        # removing REPLY_PREFIX and REPLY_SUFFIX
        reply = reply[1:-1]

        cmd_id, code, desc = reply.split(';')
        code = int(code)
        if code == 0:
            return
        # getting the "raw" reply description
        substr = "Circunstancia="
        desc_idx = desc.index(substr) + len(substr)
        desc = desc[desc_idx:]
        try:
            exception = Pay2023.errors_dict[code]
        except KeyError:
            raise DriverError("%d: %s" % (code, desc))
        raise exception(desc)

    def _get_last_item_id(self):
        return self._get_integer_register_data(Pay2023.CMD_GET_LAST_ITEM_ID)

    def _get_coupon_number(self):
        return self._get_integer_register_data(Pay2023.CMD_GET_COO)

    def _get_integer_register_data(self, data_name):
        result = self._send_command(Pay2023.CMD_GET_INTEGER_REGISTER_DATA,
                                    NomeInteiro="\"%s\"" % data_name)
        result = result[:-1]
        substr = "ValorInteiro"
        index = result.index(substr) + len(substr) + 1
        return int(result[index:])

    def get_money_register_data(self, data_name):
        result = self._send_command(Pay2023.CMD_GET_MONEY_REGISTER_DATA,
                                    NomeDadoMonetario="\"%s\"" % data_name)
        result = result[:-1]
        substr = "ValorMoeda"
        index = result.index(substr) + len(substr) + 1
        return self.parse_value(result[index:])

    def get_coupon_total_value(self):
        name = Pay2023.CMD_GET_COUPON_TOTAL_VALUE
        return self.get_money_register_data(name)

    def get_coupon_remainder_value(self):
        name = Pay2023.CMD_GET_COUPON_TOTAL_PAID_VALUE
        value =  self.get_money_register_data(name)
        result = self.get_coupon_total_value() - value
        if result < 0.0:
            result = 0.0
        return result

    def format_value(self, value, digits=4):
        """ This method receives a float value and format it to the string
        format accepted by the FISCnet protocol.
        """
        format = '%%.0%df' % digits
        return (format % value).replace('.', ',')

    def parse_value(self, value):
        """ This method receives a string value (representing the float
        format used in the FISCnet protocol) and convert it to the
        Python's float format.
        """
        if '.' in value:
            value = value.replace(".", '')
        if ',' in value:
            value = value.replace(',', '.')
        return Decimal(value)

    def _get_status(self):
        status = self._send_command(
            Pay2023.CMD_READ_REGISTER_INT,
            NomeInteiro="\"%s\"" % Pay2023.REGISTER_INDICATORS)

        status = int(status[1:-1].split(';')[2].split('=', 1)[1])
        return status

    # This how the printer needs to be configured.
    def setup(self):
        self._send_command(
            'DefineNaoFiscal', CodNaoFiscal=1, DescricaoNaoFiscal="\"Sangria\"",
            NomeNaoFiscal="\"Sangria\"", TipoNaoFiscal="false")
        self._send_command(
            'DefineNaoFiscal', CodNaoFiscal=0, DescricaoNaoFiscal="\"Suprimento\"",
            NomeNaoFiscal="\"Suprimento\"", TipoNaoFiscal="false")

    def print_status(self):
        status = self._get_status()
        print 'Flags'
        for flag in reversed(_status_flags):
            if status & flag:
                print flag, _flagnames[flag]

        print 'non-fiscal registers'
        for i in range(15):
            print self._send_command(
                'LeNaoFiscal', CodNaoFiscal=i)

    #
    # ICouponPrinter implementation
    #

    def coupon_identify_customer(self, customer, address, document):
        self._customer_name = customer
        self._customer_document = document
        self._customer_address = address

    def coupon_open(self):
        try:
            customer = self._customer_name
            document = self._customer_document
            address = self._customer_address
            self.send_command(Pay2023.CMD_COUPON_OPEN,
                              EnderecoConsumidor="\"%s\"" % address[:80],
                              IdConsumidor="\"%s\"" % document[:29],
                              NomeConsumidor="\"%s\"" % customer[:30])
        except InvalidState:
            raise CouponOpenError(_("Coupon already opened."))

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
        self.send_command(Pay2023.CMD_ADD_ITEM,
                          CodAliquota=taxcode,
                          CodProduto="\"%s\"" % code[:48],
                          NomeProduto="\"%s\"" % description[:200],
                          Unidade="\"%02s\"" % unit,
                          PrecoUnitario=self.format_value(price),
                          Quantidade=self.format_value(quantity, digits=3))
        return self._get_last_item_id()

    def coupon_cancel_item(self, item_id):
        self.send_command(Pay2023.CMD_CANCEL_ITEM, NumItem=item_id)

    def coupon_cancel(self):
        self.send_command(Pay2023.CMD_COUPON_CANCEL)

    def coupon_totalize(self, discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), taxcode=TAX_NONE):
        # The FISCnet protocol (the protocol used in this printer model)
        # doesn't have a command to totalize the coupon, so we just get
        # the discount/surcharge values and applied to the coupon.
        value = discount and (discount * -1) or surcharge
        if value:
            self.send_command(Pay2023.CMD_ADD_COUPON_DIFFERENCE, Cancelar='f',
                              ValorPercentual="%.02f" % value)
        return self.get_coupon_total_value()

    def coupon_add_payment(self, payment_method, value, description=u"",
                           custom_pm=''):
        if not custom_pm:
            pm = self._consts.get_value(payment_method)
        else:
            pm = custom_pm
        self.send_command(Pay2023.CMD_ADD_PAYMENT,
                          CodMeioPagamento=pm, Valor=self.format_value(value),
                          TextoAdicional="\"%s\"" % description[:80])
        return self.get_coupon_remainder_value()

    def coupon_close(self, message=''):
        self.send_command(Pay2023.CMD_COUPON_CLOSE,
                          TextoPromocional="\"%s\"" % message[:492])
        return self._get_coupon_number()

    def summarize(self):
        self.send_command(Pay2023.CMD_READ_X)

    def close_till(self):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self.send_command(Pay2023.CMD_COUPON_CANCEL)

        self.send_command(Pay2023.CMD_CLOSE_TILL)

    def till_add_cash(self, value):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self.send_command(Pay2023.CMD_COUPON_CANCEL)
        self.send_command(Pay2023.CMD_COUPON_OPEN_NOT_FISCAL)
        self.send_command('EmiteItemNaoFiscal',
                          NomeNaoFiscal="\"Suprimento\"",
                          Valor=self.format_value(value))
        self.send_command(Pay2023.CMD_COUPON_CLOSE)

    def till_remove_cash(self, value):
        status = self._get_status()
        if status & FLAG_DOCUMENTO_ABERTO:
            self.send_command(Pay2023.CMD_COUPON_CANCEL)
        self.send_command(Pay2023.CMD_COUPON_OPEN_NOT_FISCAL)
        self.send_command('EmiteItemNaoFiscal',
                          NomeNaoFiscal="\"Sangria\"",
                          Valor=self.format_value(value))
        self.send_command(Pay2023.CMD_COUPON_CLOSE)

    #
    # IChequePrinter implementation
    #

    def print_cheque(self, bank, value, thirdparty, city, date=datetime.now()):
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

        self.send_command(Pay2023.CMD_PRINT_CHEQUE, Cidade="\"%s\"" % city[:27],
                          Data=date.strftime("#%d/%m/%Y#"),
                          Favorecido="\"%s\"" % thirdparty[:45],
                          Valor=self.format_value(value), **data)

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
