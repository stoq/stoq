# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
##
"""
stoqdrivers/devices/printers/perto/Pay2023.py:
    
    PertoPay 2023 driver implementation.
"""

from datetime import datetime

from serial import EIGHTBITS, PARITY_EVEN, STOPBITS_ONE
from zope.interface import implements

from stoqdrivers.devices.serialbase import SerialBase
from stoqdrivers.devices.printers.interface import (ICouponPrinter,
                                                    IChequePrinter)
from stoqdrivers.constants import (TAX_IOF, TAX_ICMS, TAX_SUBSTITUTION,
                                   TAX_EXEMPTION, TAX_NONE)
from stoqdrivers.constants import (UNIT_WEIGHT, UNIT_METERS,
                                   UNIT_LITERS, UNIT_EMPTY)
from stoqdrivers.constants import MONEY_PM, CHEQUE_PM
from stoqdrivers.exceptions import (DriverError, PendingReduceZ,
                                    CommandParametersError, CommandError,
                                    ReadXError, OutofPaperError,
                                    CouponTotalizeError, PaymentAdditionError,
                                    CancelItemError, ReduceZError,
                                    CouponOpenError, InvalidState)
from stoqdrivers.devices.printers.capabilities import Capability


class Pay2023Printer(SerialBase):

    implements(IChequePrinter, ICouponPrinter)

    printer_name = "Pertopay Fiscal 2023"

    CMD_PREFIX = '{'
    CMD_SUFFIX = '}'
    EOL_DELIMIT = CMD_SUFFIX

    CMD_READ_X = 'EmiteLeituraX'
    CMD_CANCEL_COUPON = 'CancelaCupom'
    CMD_CLOSE_TILL = 'EmiteReducaoZ'
    CMD_ADD_ITEM = 'VendeItem'
    CMD_COUPON_OPEN = 'AbreCupomFiscal'
    CMD_CANCEL_ITEM = 'CancelaItemFiscal'
    CMD_ADD_PAYMENT = 'PagaCupom'
    CMD_ADD_COUPON_DIFFERENCE = 'AcresceSubtotal'
    CMD_COUPON_CANCEL = 'CancelaCupom'
    CMD_COUPON_CLOSE = 'EncerraDocumento'
    CMD_GET_REGISTER_DATA = 'LeInteiro'
    CMD_GET_LAST_ITEM_ID = 'ContadorDocUltimoItemVendido'
    CMD_PRINT_CHEQUE = 'ImprimeCheque'

    errors_dict = {7003: OutofPaperError,
                   7004: OutofPaperError,
                   8007: CouponTotalizeError,
                   8011: PaymentAdditionError,
                   8013: CouponTotalizeError,
                   8014: PaymentAdditionError,
                   8045: CancelItemError,
                   8068: PaymentAdditionError,
                   15009: PendingReduceZ,
                   11002: CommandParametersError,
                   11006: CommandError,
                   11007: InvalidState,
                   15007: ReduceZError,
                   15008: ReadXError,
                   15011: OutofPaperError}

    # FIXME: this part will be fixed at bug #2246
    taxcode_dict = {TAX_IOF : '0',
                    TAX_ICMS : '0',
                    TAX_SUBSTITUTION : '0',
                    TAX_EXEMPTION : '0',
                    TAX_NONE : '0'}

    unit_dict = {UNIT_WEIGHT : 'kg',
                 UNIT_METERS : 'm ',
                 UNIT_LITERS : 'lt',
                 UNIT_EMPTY : '  '}

    payment_methods = {MONEY_PM : '1',
                       CHEQUE_PM : '2'}

    #
    # Cheque elements position
    #

    # TODO: Bug #2284 will improve this "position declarations" to work with
    # all the Brazilian banks

    CHEQUE_NUMERIC_VALUE_ROW = 64
    CHEQUE_NUMERIC_VALUE_COL = 1218
    CHEQUE_VALUE_STRING_ROW1 = 152
    CHEQUE_VALUE_STRING_COL1 = 269
    CHEQUE_VALUE_STRING_ROW2 = 208
    CHEQUE_VALUE_STRING_COL2 = 79
    CHEQUE_CITY_ROW = 336
    CHEQUE_CITY_COL = 589
    CHEQUE_THIRDPARTY_ROW = 264
    CHEQUE_THIRDPARTY_COL = 99
    CHEQUE_YEAR_COL = 1577
    CHEQUE_DAY_COL = 1058
    CHEQUE_MONTH_COL = 1208

    def __init__(self, device, baudrate=115200, bytesize=EIGHTBITS,
                 parity=PARITY_EVEN, stopbits=STOPBITS_ONE):
        SerialBase.__init__(self, device, baudrate=baudrate, bytesize=bytesize,
                            parity=parity, stopbits=stopbits)

    #
    # Helper methods
    #

    def _send_command(self, command, **params):
        params = ["%s=%s" % (param, value) for param, value in params.items()]
        data = "%d;%s;%s;" % (self.get_next_command_id(), command,
                              " ".join(params))
        result = self.writeline("%s" % data)
        return result

    def send_command(self, command, **params):
        result = self._send_command(command, **params)
        self.handle_error(command, result)

    def handle_error(self, cmd, reply):
        """ Reply format:

            {CMD_ID;REPLY_CODE;REPLY_DESCRIPTION;CMD_SIZE}

        Where '{' is the reply prefix and '}' the suffix

        Note that the REPLY_DESCRIPTION field is composed by the following
        sections:

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
            exception = Pay2023Printer.errors_dict[code]
        except KeyError:
            raise DriverError("%d: %s" % (code, desc))
        raise exception(desc)

    def get_next_command_id(self):
        # I don't want to work with (and manage!) many commands at the same
        # time, so returning always 0 I can avoid this (all the same ids,
        # all the fuck*** time)
        return 0

    def get_last_item_id(self):
        name = "\"%s\"" % Pay2023Printer.CMD_GET_LAST_ITEM_ID
        result = self._send_command(Pay2023Printer.CMD_GET_REGISTER_DATA,
                                    NomeInteiro=name)
        result = result[:-1]
        substr = "ValorInteiro"
        index = result.index(substr) + len(substr) + 1
        value = int(result[index:])
        return value

    #
    # ICouponPrinter implementation
    #


    def coupon_open(self, customer, address, document):
        try:
            self.send_command(Pay2023Printer.CMD_COUPON_OPEN,
                              EnderecoConsumidor="\"%s\"" % address[:80],
                              IdConsumidor="\"%s\"" % document[:29],
                              NomeConsumidor="\"%s\"" % customer[:30])
        except InvalidState:
            raise CouponOpenError("Coupon already opened.")

    def coupon_add_item(self, code, quantity, price, unit, description, taxcode,
                        discount, surcharge):        
        # FIXME: these magic numbers will be remove when the bug #2176 is fixed
        self.send_command(Pay2023Printer.CMD_ADD_ITEM,
                          CodAliquota=Pay2023Printer.taxcode_dict[taxcode],
                          CodProduto="\"%s\"" % code[:48],
                          NomeProduto="\"%s\"" % description[:200],
                          Unidade="\"%02s\"" % Pay2023Printer.unit_dict[unit],
                          PrecoUnitario="%.04f" % price,
                          Quantidade="%.03f" % quantity)

        return self.get_last_item_id()

    def coupon_cancel_item(self, item_id):
        self.send_command(Pay2023Printer.CMD_CANCEL_ITEM, NumItem=item_id)

    def coupon_cancel(self):
        self.send_command(Pay2023Printer.CMD_COUPON_CANCEL)

    def coupon_totalize(self, discount, surcharge, taxcode):
        # The FISCnet protocol (the protocol used in this printer model)
        # doesn't have a command to totalize the coupon, so we just get
        # the discount/surcharge values and applied to the coupon.
        value = discount and (discount * -1) or surcharge

        self.send_command(Pay2023Printer.CMD_ADD_COUPON_DIFFERENCE,
                          Cancelar='f', ValorPercentual="%.02f" % value)

    def coupon_add_payment(self, payment_method, value, description=''):
        pm = Pay2023Printer.payment_methods[payment_method]
        self.send_command(Pay2023Printer.CMD_ADD_PAYMENT,
                          CodMeioPagamento=pm, Valor="%.04f" % value,
                          TextoAdicional="\"%s\"" % description[:80])
        
    def coupon_close(self, message=''):
        # FIXME: these magic numbers will be remove when the bug #2176 is fixed
        self.send_command(Pay2023Printer.CMD_COUPON_CLOSE,
                          TextoPromocional="\"%s\"" % message[:492])

    def summarize(self):
        self.send_command(Pay2023Printer.CMD_READ_X)

    def close_till(self):
        self.send_command(Pay2023Printer.CMD_CLOSE_TILL)

    #
    # IChequePrinter implementation
    #

    def print_cheque(self, value, thirdparty, city, date=datetime.now()):
        cheque_value_string_col1 = Pay2023Printer.CHEQUE_VALUE_STRING_COL1
        cheque_value_string_col2 = Pay2023Printer.CHEQUE_VALUE_STRING_COL2
        cheque_value_string_row1 = Pay2023Printer.CHEQUE_VALUE_STRING_ROW1
        cheque_value_string_row2 = Pay2023Printer.CHEQUE_VALUE_STRING_ROW2

        # FIXME: these magic numbers will be remove when the bug #2176 is fixed
        self.send_command(Pay2023Printer.CMD_PRINT_CHEQUE,
                          Cidade="\"%s\"" % city[:27],
                          Data=date.strftime("#%d/%m/%Y#"),
                          Favorecido="\"%s\"" % thirdparty[:45],
                          HPosAno=Pay2023Printer.CHEQUE_YEAR_COL,
                          HPosCidade=Pay2023Printer.CHEQUE_CITY_COL,
                          HPosDia=Pay2023Printer.CHEQUE_DAY_COL,
                          HPosExtensoLinha1=cheque_value_string_col1,
                          HPosExtensoLinha2=cheque_value_string_col2,
                          HPosFavorecido=Pay2023Printer.CHEQUE_THIRDPARTY_COL,
                          HPosMes=Pay2023Printer.CHEQUE_MONTH_COL,
                          HPosValor=Pay2023Printer.CHEQUE_NUMERIC_VALUE_COL,
                          Valor="%.04f" % value,
                          VPosCidade=Pay2023Printer.CHEQUE_CITY_ROW,
                          VPosExtensoLinha1=cheque_value_string_row1,
                          VPosExtensoLinha2=cheque_value_string_row2,
                          VPosFavorecido=Pay2023Printer.CHEQUE_THIRDPARTY_ROW,
                          VPosValor=Pay2023Printer.CHEQUE_NUMERIC_VALUE_ROW)

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
