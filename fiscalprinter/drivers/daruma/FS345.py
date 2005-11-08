# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Fiscal Printer
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
##
"""
    fiscalprinter/drivers/daruma/FS345.py:

    Daruma printer drivers implementation
"""

import time

from fiscalprinter.constants import (TAX_IOF, TAX_ICMS, TAX_NONE,
                                     TAX_SUBSTITUTION, MONEY_PM, CHEQUE_PM)
from fiscalprinter.drivers.serialbase import SerialBase
from fiscalprinter.exceptions import (DriverError, PendingReduceZ,
     HardwareFailure, AuthenticationFailure, CommError, PendingReadX, 
     CouponNotOpenError, OutofPaperError, PrinterOfflineError,
     CouponOpenError)


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

def isbitset(value, bit):
    # BCD crap
    return (int(value, 16) >> bit) & 1 == 1

def ifset(value, bit, false='', true=''):
    if not isbitset(value, bit):
        return false
    else:
        return true

payment_methods = {
    MONEY_PM : 'A',
    CHEQUE_PM : 'B' # XXX: Just a test, the print isn't configured to
                    # consider the type 'B' as Cheque.
}


class FS345Printer(SerialBase):
    log_domain = 'fs345'

    def send_command(self, command, extra=''):
        raw = chr(command) + extra
        retval = super(FS345Printer, self).writeline(raw)
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
            raise SystemExit('Broken status reply')

        if verbose:
            print '== STATUS =='
        
            # Codes found on page 57-59
            print 'Raw status code:', status
            print 'Cashier drawer is', ifset(status[1], 3, 'closed', 'open')
            
        if self.needs_reduce_z():
            raise PendingReduceZ('Pending Reduce Z')
        if self.status_check(status, 1, 2):
            raise HardwareFailure('Mechanical failure')
        if not self.status_check(status, 1, 1):
            raise AuthenticationFailure('Not properly authenticated')
        if self.status_check(status, 1, 0):
            raise OutofPaperError('No paper')
        if self.status_check(status, 2, 3):
            raise PrinterOfflineError("Offline")
        if not self.status_check(status, 2, 2):
             raise CommError("Peripheral is not connected to AUX")
        if self.status_check(status, 2, 0):
            self.warning('Almost out of paper')

        if verbose:
            S3 = status[3]
            print ifset(S3, 3, 'Maintenance', 'Operational'), 'mode'
            print 'Authentication', ifset(S3, 2, 'disabled', 'enabled')
            print 'Guillotine', ifset(S3, 1, 'disabled', 'enabled')
            print 'Auto close CF?', ifset(S3, 0, 'no', 'yes')

        if self.needs_read_x(status):
            raise PendingReadX("readX is not emitted yet")

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
        # Page 14-16
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
            raise CouponOpenError("Document is already open")
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
            raise CouponNotOpenError("Coupon is not open")

    def _is_open(self, status):
        return self.status_check(status, 4, 2)

    # 
    # API implementation
    #
    
    def coupon_open(self, customer, address, document):
        status = self._check_status()
        if self._is_open(status):
            raise CouponOpenError("Coupon already open")
        self.send_command(CMD_OPEN_COUPON)
        
        self._customer = customer
        self._address = address
        self._document = document

    def coupon_add_item(self, code, quantity, price, unit, description,
                        taxcode, discount, charge):
        if taxcode == TAX_NONE:
            S = 'Nb'
        elif taxcode == TAX_SUBSTITUTION:
            S = 'Tb'
        else: # TAX_EXEMPTION
            S = 'Fb'
            
        if charge:
            d = 1
            E = charge
        else:
            d = 0
            E = discount

        unit = '  '
        data = '%2s%13s%d%04d%010d%08d%s%s\xff' % (S, code[:13], d,
                                                   int(E * 1e2),
                                                   int(price * 1e3),
                                                   int(quantity * 1e3),
                                                   unit,
                                                   description[:174])
        value = self.send_command(CMD_ADD_ITEM_3L13D53U, data)
        return int(value[2:5])

    def coupon_cancel_item(self, item_id):
        self.send_command(CMD_CANCEL_ITEM, "%03d" % item_id)

    def coupon_add_payment(self, payment_method, value, description=''):
        self._check_status()
        self._verify_coupon_open()
        if not payment_method in payment_methods:
            raise TypeError("You need specify a valid payment method.")

        pm = payment_methods[payment_method]
        rv = self.send_command(CMD_DESCRIBE_PAYMENT_FORM,
                               '%c%012d%s\xff' % (pm, int(value * 1e2),
                                                  description[:48]))
        return float(rv) / 1e2

    def coupon_cancel(self):
        self._check_status()
        self._verify_coupon_open()
        self.send_command(CMD_CANCEL_COUPON)

    def coupon_totalize(self, discount, markup, taxcode):
        self._check_status()
        self._verify_coupon_open()

        if markup:
            value = markup
            name = 'markup'
        elif discount:
            value = discount
            name = 'discount'
        else:
            value = 0
            name = ''

        if taxcode == TAX_ICMS:
            mode = 3
        elif taxcode == TAX_IOF:
            mode = 5
        else: #taxcode == TAX_NONE:
            mode = 1

        data = '%d%012d' % (mode, int(value * 1e2))
        rv = self.send_command(CMD_TOTALIZE_COUPON, data)
        return float(rv) / 1e2

    def coupon_close(self, message):
        self._check_status()
        self._verify_coupon_open()

        empty = " " *42

        if self._customer or self._address or self._document:
            self.send_command(CMD_IDENTIFY_CUSTOMER,
                              (("% 42s" % self._customer) + empty +
                               ("% 42s" % self._address) + empty +
                               ("% 42s" % self._document) + empty))

        LINE_LEN = 48
        msg_len = len(message)
        if msg_len > LINE_LEN * 8:
            raise TypeError("message too long")
        elif msg_len > LINE_LEN:
            l = []
            for i in range(0, msg_len, LINE_LEN):
                l.append(message[i:i+LINE_LEN])
            message = '\n'.join(l)

        self.send_command(CMD_CLOSE_COUPON, message + '\xff')

    def summarize(self):
        self.send_command(CMD_GET_X)

    def close_till(self):
        if self._is_open(self._get_status()):
            raise CouponOpenError("There is a coupon opened")
        elif self.needs_read_x():
            raise PendingReadX("Pending read X")

        date = time.strftime('%d%m%y%H%M%S', time.localtime())
        self.send_command(CMD_REDUCE_Z, date)

