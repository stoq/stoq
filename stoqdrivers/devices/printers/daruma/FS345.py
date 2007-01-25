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
## Author(s):   Johan Dahlin     <jdahlin@async.com.br>
##              Henrique Romano  <henrique@async.com.br>
##
"""
stoqdrivers/devices/printers/daruma/FS345.py:

    Daruma printer drivers implementation
"""
import time
from decimal import Decimal

from zope.interface import implements

from stoqdrivers.constants import (TAX_IOF, TAX_ICMS, TAX_NONE, TAX_EXEMPTION,
                                   TAX_SUBSTITUTION, MONEY_PM, CHEQUE_PM,
                                   UNIT_WEIGHT, UNIT_METERS, UNIT_LITERS,
                                   UNIT_EMPTY, UNIT_CUSTOM)
from stoqdrivers.devices.serialbase import SerialBase
from stoqdrivers.exceptions import (DriverError, PendingReduceZ, HardwareFailure,
                                    AuthenticationFailure, CommError,
                                    PendingReadX, CouponNotOpenError,
                                    OutofPaperError, PrinterOfflineError,
                                    CouponOpenError, CancelItemError,
                                    CloseCouponError)
from stoqdrivers.devices.interfaces import ICouponPrinter
from stoqdrivers.devices.printers.capabilities import Capability
from stoqdrivers.devices.printers.base import BaseDriverConstants
from stoqdrivers.translation import stoqdrivers_gettext

_ = lambda msg: stoqdrivers_gettext(msg)

CMD_STATUS = '\x1d\xff'

CMD_SET_OWNER = 190
# [ESC] 191 Gravação da indicação de mudança de moeda
# [ESC] 192 Intervenção Técnica
CMD_GET_MODEL = 195
CMD_GET_FIRMWARE = 199
CMD_OPEN_COUPON = 200
CMD_IDENTIFY_CUSTOMER = 201
CMD_ADD_ITEM_1L6D = 202
CMD_ADD_ITEM_2L6D = 203
CMD_ADD_ITEM_3L6D = 204
CMD_CANCEL_ITEM = 205
# [ESC] 206 Cancelamento de Documento
CMD_CANCEL_COUPON = 206
CMD_GET_X = 207
CMD_REDUCE_Z = 208
# [ESC] 209 Leitura da Memória Fiscal
# [ESC] 210 Emissão de Cupom Adicional
# [ESC] 211 Abertura de Relatório Gerencial (Leitura X)
# [ESC] 212 Fechamento de Relatório Gerencial (Leitura X)
# [ESC] 213 Linha de texto de Relatório Gerencial (Leitura X)
CMD_ADD_ITEM_1L13D = 214
CMD_ADD_ITEM_2L13D = 215
CMD_ADD_ITEM_3L13D = 216
# [ESC] 217 Emissão de Comprovante Não Fiscal Não Vinculado
CMD_DESCRIBE_MESSAGES = 218
# [ESC] 219 Abertura de Comprovante Não Fiscal Vinculado
# [ESC] 220 Carga de alíquota de imposto
CMD_LAST_RECORD = 221
# [ESC] 223 Descrição de produto em 3 linhas com código de 13 dígitos
#           (Formato fixo p/ Quantidade 5,3)
CMD_ADD_ITEM_3L13D53U = 223
# [ESC] 225 Descrição de produto com preço unitário com 3 decimais
# [ESC] 226 Criação de Comprovante Não Fiscal (Vinculado ou Não)
# [ESC] 227 Subtotalização de Cupom Fiscal
# [ESC] 228 Configuração da IF
CMD_GET_CONFIGURATION = 229
# [ESC] 230 Leitura do relógio interno da impressora
# [ESC] 231 Leitura das alíquotas fiscais carregadas
# [ESC] 232 Leitura do clichê do proprietário
# [ESC] 234 Retransmissão de mensagens da IF
# [ESC] 236 Leitura da identificação da IF
# [ESC] 238 Leitura das mensagens personalizadas
CMD_GET_DOCUMENT_STATUS = 239
CMD_GET_FISCAL_REGISTRIES = 240
CMD_TOTALIZE_COUPON = 241
CMD_DESCRIBE_PAYMENT_FORM = 242
CMD_CLOSE_COUPON = 243
CMD_GET_REGISTRIES = 244
# [ESC] 246 Leitura Horária
# [ESC] 247 Descrição Estendida
# [ESC] 248 Estorno de forma de pagamento
# [ESC] 250 Leitura de datas de Controle Fiscal
# [ESC] 251 Leitura das informações cadastrais do usuário
# [ESC] V   Controle de horário de verão
CMD_GET_TOTALIZERS = 244
CMD_OPEN_VOUCHER = 217

CASH_IN_TYPE = 'B'
CASH_OUT_TYPE = 'A'

def isbitset(value, bit):
    # BCD crap
    return (int(value, 16) >> bit) & 1 == 1

def ifset(value, bit, false='', true=''):
    if not isbitset(value, bit):
        return false
    else:
        return true

class FS345Constants(BaseDriverConstants):
    # TODO Fixup these values
    _constants = {
        TAX_IOF:          'Nb',
        TAX_ICMS:         'Nb',
        TAX_SUBSTITUTION: 'Tb',
        TAX_EXEMPTION:    'Fb',
        TAX_NONE:         'Nb',
        UNIT_WEIGHT:      'Kg',
        UNIT_METERS:      'm ',
        UNIT_LITERS:      'Lt',
        UNIT_EMPTY:       '  ',
        MONEY_PM:         'A',
        CHEQUE_PM:        'B'
        }

class FS345(SerialBase):
    log_domain = 'fs345'

    implements(ICouponPrinter)

    model_name = "Daruma FS 345"
    coupon_printer_charset = "cp850"

    def __init__(self, port, consts=None):
        self._consts = consts or FS345Constants
        SerialBase.__init__(self, port)
        self._customer_name = u""
        self._customer_document = u""
        self._customer_address = u""

    def send_command(self, command, extra=''):
        raw = chr(command) + extra
        retval = self.writeline(raw)
        if retval.startswith(':E'):
            self.handle_error(retval, raw)
        return retval[1:]

    # Status
    def _get_status(self):
        self.write(CMD_STATUS)
        return self.readline()

    def status_check(self, S, byte, bit):
        return isbitset(S[byte], bit)

    def _check_status(self, verbose=False):
        status = self._get_status()
        if status[0] != ':':
            raise HardwareFailure('Broken status reply')

        if verbose:
            print '== STATUS =='

            # Codes found on page 57-59
            print 'Raw status code:', status
            print 'Cashier drawer is', ifset(status[1], 3, 'closed', 'open')

        if self.needs_reduce_z():
            raise PendingReduceZ(_('Pending Reduce Z'))
        if self.status_check(status, 1, 2):
            raise HardwareFailure(_('Mechanical failure'))
        if not self.status_check(status, 1, 1):
            raise AuthenticationFailure(_('Not properly authenticated'))
        if self.status_check(status, 1, 0):
            raise OutofPaperError(_('No paper'))
        if self.status_check(status, 2, 3):
            raise PrinterOfflineError(_("Offline"))
        if not self.status_check(status, 2, 2):
             raise CommError(_("Peripheral is not connected to AUX"))
        if self.status_check(status, 2, 0):
            self.warning('Almost out of paper')

        if verbose:
            S3 = status[3]
            print ifset(S3, 3, 'Maintenance', 'Operational'), 'mode'
            print 'Authentication', ifset(S3, 2, 'disabled', 'enabled')
            print 'Guillotine', ifset(S3, 1, 'disabled', 'enabled')
            print 'Auto close CF?', ifset(S3, 0, 'no', 'yes')

        if self.needs_read_x(status):
            raise PendingReadX(_("readX is not emitted yet"))

        return status

    def needs_reduce_z(self, status=None):
        if not status:
            status = self._get_status()
        return self.status_check(status, 2, 1)

    def needs_read_x(self, status=None):
        if not status:
            status = self._get_status()

        return not self.status_check(status, 6, 2)

    # Error handling

    def handle_error(self, error_value, raw):
        error = int(error_value[2:])
        # Page 61-62
        if error == 39:
            raise DriverError('Bad parameters: %r'  % raw)
        elif error == 45:
            raise DriverError("Bad numeric string")
        elif error == 42:
            raise DriverError("Bad OKI command")
        elif error == 24:
            raise DriverError("Bad unit specified: %r" % raw)
        elif error == 23:
            raise DriverError("Bad description: %r" % raw)
        elif error == 16:
            raise DriverError("Bad discount/markup parameter")
        elif error == 10:
            raise CouponOpenError(_("Document is already open"))
        elif error == 11:
            raise CouponNotOpenError(_("Coupon is not open"))
        elif error == 12:
            raise CouponNotOpenError(_("There's no open document to cancel"))
        elif error == 15:
            raise CancelItemError(_("There is no such item in "
                                    "the coupon"))
        else:
            raise DriverError("Unhandled error: %d" % error)

    # Information / debugging

    def show_status(self):
        self._check_status(verbose=True)

    def show_information(self):
        print 'Model:', self.send_command(CMD_GET_MODEL, debug=False)
        print 'Firmware:', self.send_command(CMD_GET_FIRMWARE, debug=False)
        data = self.send_command(CMD_LAST_RECORD, debug=False)

        tt = time.strptime(data[:12], '%d%m%y%H%M%S')
        print 'Last record:', time.strftime('%c', tt)
        print 'Configuration:', self.send_command(CMD_GET_CONFIGURATION,
                                               debug=False)

    def show_document_status(self):
        print '== DOCUMENT STATUS =='
        value = self.send_command(CMD_GET_DOCUMENT_STATUS, debug=False)
        assert value[:2] == '\x1b' + chr(CMD_GET_DOCUMENT_STATUS)
        assert len(value) == 59
        print 'ECF:', value[2:6]
        document_type = value[6]
        if document_type == '2':
            print 'No open coupon'
        elif document_type == '1':
            print 'Document is a coupon (%s)' % value[7:12]
        else:
            print 'Document type:', value[6]

        tt = time.strptime(value[13:27], '%H%M%S%d%m%Y')
        print 'Current date/time:', time.strftime('%c', tt)

        print 'Sum', int(value[27:41]) / 100.0
        print 'GT atual', value[41:59]

    def show_fiscal_registers(self):
        value = self.send_command(CMD_GET_FISCAL_REGISTRIES)
        assert value[:2] == '\x1b' + chr(CMD_GET_FISCAL_REGISTRIES)

    def show_registers(self):
        value = self.send_command(CMD_GET_REGISTRIES)
        assert value[:2] == '\x1b' + chr(CMD_GET_REGISTRIES)
        print value[48:62]

    # High level commands
    def _verify_coupon_open(self):
        if not self.status_check(self._get_status(), 4, 2):
            raise CouponNotOpenError(_("Coupon is not open"))

    def _is_open(self, status):
        return self.status_check(status, 4, 2)

    # Helper commands

    def _get_totalizers(self):
        return self.send_command(CMD_GET_TOTALIZERS)

    def _get_coupon_number(self):
        return int(self._get_totalizers()[8:14])

    def _add_payment(self, payment_method, value, description='',
                     custom_pm=''):
        if not custom_pm:
            pm = self._consts.get_value(payment_method)
        else:
            pm = custom_pm
        rv = self.send_command(CMD_DESCRIBE_PAYMENT_FORM,
                               '%c%012d%s\xff' % (pm, int(float(value) * 1e2),
                                                  description[:48]))
        return float(rv) / 1e2

    def _add_voucher(self, type, value):
        data = "%s1%s%012d\xff" % (type, "0" * 12, # padding
                                   int(float(value) * 1e2))
        self.send_command(CMD_OPEN_VOUCHER, data)

    #
    # API implementation
    #

    def coupon_identify_customer(self, customer, address, document):
        self._customer_name = customer
        self._customer_document = document
        self._customer_address = address

    def coupon_open(self):
        status = self._check_status()
        if self._is_open(status):
            raise CouponOpenError(_("Coupon already open"))
        self.send_command(CMD_OPEN_COUPON)

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UNIT_EMPTY,
                        discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), unit_desc=""):
        taxcode = self._consts.get_value(taxcode)
        if surcharge:
            d = 1
            E = surcharge
        else:
            d = 0
            E = discount

        if unit == UNIT_CUSTOM:
            unit = unit_desc
        else:
            unit = self._consts.get_value(unit)
        data = '%2s%13s%d%04d%010d%08d%s%s\xff' % (taxcode, code[:13], d,
                                                   int(float(E) * 1e2),
                                                   int(float(price) * 1e3),
                                                   int(float(quantity) * 1e3),
                                                   unit, description[:174])
        value = self.send_command(CMD_ADD_ITEM_3L13D53U, data)
        return int(value[1:4])

    def coupon_cancel_item(self, item_id):
        self.send_command(CMD_CANCEL_ITEM, "%03d" % item_id)

    def coupon_add_payment(self, payment_method, value, description='',
                           custom_pm=''):
        self._check_status()
        self._verify_coupon_open()
        return self._add_payment(payment_method, value, description,
                                 custom_pm)

    def coupon_cancel(self):
        # If we need reduce Z don't verify that the coupon is open, instead
        # just cancel the coupon. This avoids a race when you forgot
        # to close a coupon and reduce Z at the same time.
        if not self.needs_reduce_z():
            self._check_status()

        self.send_command(CMD_CANCEL_COUPON)

    def coupon_totalize(self, discount=Decimal("0.0"), surcharge=Decimal("0.0"),
                        taxcode=TAX_NONE):
        self._check_status()
        self._verify_coupon_open()
        if surcharge:
            value = surcharge
            if taxcode == TAX_ICMS:
                mode = 2
            elif taxcode == TAX_IOF:
                mode = 4
            else:
                raise ValueError("Invalid tax code specified. Allowed "
                                 "constants are: TAX_ICMS and TAX_IOF")
        elif discount:
            value = discount
            mode = 0
        else:
            mode = 0
            value = Decimal("0")
        data = '%d%012d' % (mode, int(value * Decimal("1e2")))
        rv = self.send_command(CMD_TOTALIZE_COUPON, data)
        coupon_subtotal = Decimal(rv) / Decimal("1e2")
        return (coupon_subtotal + (coupon_subtotal * surcharge / Decimal("1e2"))
                - (coupon_subtotal * discount / Decimal("1e2")))

    def coupon_close(self, message=''):
        self._check_status()
        self._verify_coupon_open()

        empty = " " *42

        if (self._customer_name or self._customer_address or
            self._customer_document):
            self.send_command(CMD_IDENTIFY_CUSTOMER,
                              (("% 42s" % self._customer_name) + empty +
                               ("% 42s" % self._customer_address) + empty +
                               ("% 42s" % self._customer_document) + empty))
        LINE_LEN = 48
        msg_len = len(message)
        if msg_len > LINE_LEN:
            l = []
            for i in range(0, msg_len, LINE_LEN):
                l.append(message[i:i+LINE_LEN])
            message = '\n'.join(l)
        try:
            self.send_command(CMD_CLOSE_COUPON, message + '\xff')
        except DriverError:
            raise CloseCouponError(_("It is not possible to close the "
                                     "coupon"))
        return self._get_coupon_number()

    def summarize(self):
        self.send_command(CMD_GET_X)

    def close_till(self):
        status = self._get_status()
        if self._is_open(status):
            raise CouponOpenError(_("There is a coupon opened"))
        elif self.needs_read_x(status):
            raise PendingReadX(_("Pending read X"))

        date = time.strftime('%d%m%y%H%M%S', time.localtime())
        self.send_command(CMD_REDUCE_Z, date)

    def till_add_cash(self, value):
        self._add_voucher(CASH_IN_TYPE, value)
        self._add_payment(MONEY_PM, value, '')

    def till_remove_cash(self, value):
        self._add_voucher(CASH_OUT_TYPE, value)

    def get_capabilities(self):
        return dict(item_code=Capability(max_len=13),
                    item_id=Capability(digits=3),
                    items_quantity=Capability(min_size=1, digits=5, decimals=3),
                    item_price=Capability(min_size=0, digits=7, decimals=3),
                    item_description=Capability(max_len=173),
                    payment_value=Capability(digits=10, decimals=2),
                    promotional_message=Capability(max_len=384),
                    payment_description=Capability(max_len=48),
                    customer_name=Capability(max_len=42),
                    customer_id=Capability(max_len=42),
                    customer_address=Capability(max_len=42),
                    remove_cash_value=Capability(min_size=1, digits=10,
                                                 decimals=2),
                    add_cash_value=Capability(min_size=1, digits=10,
                                              decimals=2))

    def get_constants(self):
        return self._consts
